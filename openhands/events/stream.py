"""
OpenHands 事件流模块

这个模块实现了事件流系统，负责事件的发布、订阅和分发。
主要功能包括：
- 事件流管理和订阅机制
- 多线程事件处理
- 事件持久化和序列化
- 会话管理
"""

import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from functools import partial
from typing import Any, Callable

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.events.event_store import EventStore
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.io import json
from openhands.storage import FileStore
from openhands.storage.locations import (
    get_conversation_dir,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.shutdown_listener import should_continue


class EventStreamSubscriber(str, Enum):
    """事件流订阅者枚举，定义了可以订阅事件流的组件类型"""

    AGENT_CONTROLLER = 'agent_controller'  # 代理控制器
    SECURITY_ANALYZER = 'security_analyzer'  # 安全分析器
    RESOLVER = 'openhands_resolver'  # OpenHands 解析器
    SERVER = 'server'  # 服务器
    RUNTIME = 'runtime'  # 运行时环境
    MEMORY = 'memory'  # 内存管理器
    MAIN = 'main'  # 主程序
    TEST = 'test'  # 测试组件


async def session_exists(
    sid: str, file_store: FileStore, user_id: str | None = None
) -> bool:
    """
    检查会话是否存在

    Args:
        sid (str): 会话ID
        file_store (FileStore): 文件存储实例
        user_id (str | None): 用户ID，可选

    Returns:
        bool: 如果会话存在返回True，否则返回False
    """
    try:
        await call_sync_from_async(file_store.list, get_conversation_dir(sid, user_id))
        return True
    except FileNotFoundError:
        return False


class EventStream(EventStore):
    """
    事件流类，继承自EventStore，负责事件的实时分发和订阅管理

    这个类实现了发布-订阅模式，允许多个组件订阅事件流并接收事件通知。
    主要功能包括：
    - 事件订阅和取消订阅
    - 多线程事件分发
    - 事件队列管理
    - 线程池和事件循环管理
    """

    secrets: dict[str, str]  # 存储敏感信息的字典

    # 订阅者映射：每个订阅者ID对应一个回调函数映射
    # 这样设计便于支持多个监听器
    _subscribers: dict[str, dict[str, Callable]]

    _lock: threading.Lock  # 线程锁，保证线程安全
    _queue: queue.Queue[Event]  # 事件队列
    _queue_thread: threading.Thread  # 队列处理线程
    _queue_loop: asyncio.AbstractEventLoop | None  # 队列事件循环
    _thread_pools: dict[str, dict[str, ThreadPoolExecutor]]  # 线程池映射
    _thread_loops: dict[str, dict[str, asyncio.AbstractEventLoop]]  # 事件循环映射
    _write_page_cache: list[dict]  # 写入页面缓存

    def __init__(self, sid: str, file_store: FileStore, user_id: str | None = None):
        """
        初始化事件流

        Args:
            sid (str): 会话ID
            file_store (FileStore): 文件存储实例
            user_id (str | None): 用户ID，可选
        """
        super().__init__(sid, file_store, user_id)
        self._stop_flag = threading.Event()  # 停止标志
        self._queue: queue.Queue[Event] = queue.Queue()  # 初始化事件队列
        self._thread_pools = {}  # 初始化线程池字典
        self._thread_loops = {}  # 初始化事件循环字典
        self._queue_loop = None  # 队列事件循环

        # 创建并启动队列处理线程
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True  # 设置为守护线程
        self._queue_thread.start()

        self._subscribers = {}  # 初始化订阅者字典
        self._lock = threading.Lock()  # 初始化线程锁
        self.secrets = {}  # 初始化敏感信息字典
        self._write_page_cache = []  # 初始化写入缓存

    def _init_thread_loop(self, subscriber_id: str, callback_id: str) -> None:
        """
        初始化线程事件循环

        为每个订阅者的回调函数创建独立的事件循环

        Args:
            subscriber_id (str): 订阅者ID
            callback_id (str): 回调函数ID
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if subscriber_id not in self._thread_loops:
            self._thread_loops[subscriber_id] = {}
        self._thread_loops[subscriber_id][callback_id] = loop

    def close(self) -> None:
        """
        关闭事件流，清理所有资源

        这个方法会：
        1. 设置停止标志
        2. 等待队列处理线程结束
        3. 清理所有订阅者
        4. 清空事件队列
        """
        self._stop_flag.set()  # 设置停止标志
        if self._queue_thread.is_alive():
            self._queue_thread.join()  # 等待队列线程结束

        # 清理所有订阅者
        subscriber_ids = list(self._subscribers.keys())
        for subscriber_id in subscriber_ids:
            callback_ids = list(self._subscribers[subscriber_id].keys())
            for callback_id in callback_ids:
                self._clean_up_subscriber(subscriber_id, callback_id)

        # 清空队列
        while not self._queue.empty():
            self._queue.get()

    def _clean_up_subscriber(self, subscriber_id: str, callback_id: str) -> None:
        """
        清理指定的订阅者

        Args:
            subscriber_id (str): 订阅者ID
            callback_id (str): 回调函数ID
        """
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during cleanup: {subscriber_id}')
            return
        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during cleanup: {callback_id}')
            return

        # 清理事件循环
        if (
            subscriber_id in self._thread_loops
            and callback_id in self._thread_loops[subscriber_id]
        ):
            loop = self._thread_loops[subscriber_id][callback_id]
            current_task = asyncio.current_task(loop)
            pending = [
                task for task in asyncio.all_tasks(loop) if task is not current_task
            ]
            # 取消所有待处理的任务
            for task in pending:
                task.cancel()
            try:
                loop.stop()
                loop.close()
            except Exception as e:
                logger.warning(
                    f'Error closing loop for {subscriber_id}/{callback_id}: {e}'
                )
            del self._thread_loops[subscriber_id][callback_id]

        # 清理线程池
        if (
            subscriber_id in self._thread_pools
            and callback_id in self._thread_pools[subscriber_id]
        ):
            pool = self._thread_pools[subscriber_id][callback_id]
            pool.shutdown()  # 关闭线程池
            del self._thread_pools[subscriber_id][callback_id]

        # 删除订阅者记录
        del self._subscribers[subscriber_id][callback_id]

    def subscribe(
        self,
        subscriber_id: EventStreamSubscriber,
        callback: Callable[[Event], None],
        callback_id: str,
    ) -> None:
        """
        订阅事件流

        Args:
            subscriber_id (EventStreamSubscriber): 订阅者ID
            callback (Callable[[Event], None]): 事件回调函数
            callback_id (str): 回调函数的唯一标识符

        Raises:
            ValueError: 如果回调ID已存在
        """
        # 创建线程池初始化器
        initializer = partial(self._init_thread_loop, subscriber_id, callback_id)
        pool = ThreadPoolExecutor(max_workers=1, initializer=initializer)

        # 初始化订阅者映射
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
            self._thread_pools[subscriber_id] = {}

        # 检查回调ID是否已存在
        if callback_id in self._subscribers[subscriber_id]:
            raise ValueError(
                f'Callback ID on subscriber {subscriber_id} already exists: {callback_id}'
            )

        # 注册订阅者
        self._subscribers[subscriber_id][callback_id] = callback
        self._thread_pools[subscriber_id][callback_id] = pool

    def unsubscribe(
        self, subscriber_id: EventStreamSubscriber, callback_id: str
    ) -> None:
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during unsubscribe: {subscriber_id}')
            return

        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during unsubscribe: {callback_id}')
            return

        self._clean_up_subscriber(subscriber_id, callback_id)

    def add_event(self, event: Event, source: EventSource) -> None:
        if event.id != Event.INVALID_ID:
            raise ValueError(
                f'Event already has an ID:{event.id}. It was probably added back to the EventStream from inside a handler, triggering a loop.'
            )
        event._timestamp = datetime.now().isoformat()
        event._source = source  # type: ignore [attr-defined]
        with self._lock:
            event._id = self.cur_id  # type: ignore [attr-defined]
            self.cur_id += 1

            # Take a copy of the current write page
            current_write_page = self._write_page_cache

            data = event_to_dict(event)
            data = self._replace_secrets(data)
            event = event_from_dict(data)
            current_write_page.append(data)

            # If the page is full, create a new page for future events / other threads to use
            if len(current_write_page) == self.cache_size:
                self._write_page_cache = []

        if event.id is not None:
            # Write the event to the store - this can take some time
            event_json = json.dumps(data)
            filename = self._get_filename_for_id(event.id, self.user_id)
            if len(event_json) > 1_000_000:  # Roughly 1MB in bytes, ignoring encoding
                logger.warning(
                    f'Saving event JSON over 1MB: {len(event_json):,} bytes, filename: {filename}',
                    extra={
                        'user_id': self.user_id,
                        'session_id': self.sid,
                        'size': len(event_json),
                    },
                )
            self.file_store.write(filename, event_json)

            # Store the cache page last - if it is not present during reads then it will simply be bypassed.
            self._store_cache_page(current_write_page)
        self._queue.put(event)

    def _store_cache_page(self, current_write_page: list[dict]):
        """Store a page in the cache. Reading individual events is slow when there are a lot of them, so we use pages."""
        if len(current_write_page) < self.cache_size:
            return
        start = current_write_page[0]['id']
        end = start + self.cache_size
        contents = json.dumps(current_write_page)
        cache_filename = self._get_filename_for_cache(start, end)
        self.file_store.write(cache_filename, contents)

    def set_secrets(self, secrets: dict[str, str]) -> None:
        self.secrets = secrets.copy()

    def update_secrets(self, secrets: dict[str, str]) -> None:
        self.secrets.update(secrets)

    def _replace_secrets(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in data:
            if isinstance(data[key], dict):
                data[key] = self._replace_secrets(data[key])
            elif isinstance(data[key], str):
                for secret in self.secrets.values():
                    data[key] = data[key].replace(secret, '<secret_hidden>')
        return data

    def _run_queue_loop(self) -> None:
        self._queue_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._queue_loop)
        try:
            self._queue_loop.run_until_complete(self._process_queue())
        finally:
            self._queue_loop.close()

    async def _process_queue(self) -> None:
        while should_continue() and not self._stop_flag.is_set():
            event = None
            try:
                event = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # pass each event to each callback in order
            for key in sorted(self._subscribers.keys()):
                callbacks = self._subscribers[key]
                # Create a copy of the keys to avoid "dictionary changed size during iteration" error
                callback_ids = list(callbacks.keys())
                for callback_id in callback_ids:
                    # Check if callback_id still exists (might have been removed during iteration)
                    if callback_id in callbacks:
                        callback = callbacks[callback_id]
                        pool = self._thread_pools[key][callback_id]
                        future = pool.submit(callback, event)
                        future.add_done_callback(
                            self._make_error_handler(callback_id, key)
                        )

    def _make_error_handler(
        self, callback_id: str, subscriber_id: str
    ) -> Callable[[Any], None]:
        def _handle_callback_error(fut: Any) -> None:
            try:
                # This will raise any exception that occurred during callback execution
                fut.result()
            except Exception as e:
                logger.error(
                    f'Error in event callback {callback_id} for subscriber {subscriber_id}: {str(e)}',
                )
                # Re-raise in the main thread so the error is not swallowed
                raise e

        return _handle_callback_error
