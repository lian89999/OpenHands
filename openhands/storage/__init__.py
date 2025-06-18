"""
OpenHands 存储模块

这个模块提供了统一的存储抽象层，支持多种存储后端：
- LocalFileStore: 本地文件系统存储
- S3FileStore: Amazon S3对象存储
- GoogleCloudFileStore: Google Cloud Storage
- InMemoryFileStore: 内存存储（用于测试）
- WebHookFileStore: WebHook装饰器存储

存储模块是OpenHands数据持久化的核心组件，支持文件、对话、设置、密钥等数据的存储。
"""

import os

import httpx

from openhands.storage.files import FileStore
from openhands.storage.google_cloud import GoogleCloudFileStore
from openhands.storage.local import LocalFileStore
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.s3 import S3FileStore
from openhands.storage.web_hook import WebHookFileStore


def get_file_store(
    file_store_type: str,
    file_store_path: str | None = None,
    file_store_web_hook_url: str | None = None,
    file_store_web_hook_headers: dict | None = None,
) -> FileStore:
    """
    文件存储工厂函数

    根据指定的存储类型创建相应的文件存储实例。支持多种存储后端，
    并可选择性地添加WebHook装饰器用于存储操作的通知。

    Args:
        file_store_type (str): 存储类型
            - 'local': 本地文件系统存储
            - 's3': Amazon S3存储
            - 'google_cloud': Google Cloud Storage
            - 其他: 默认使用内存存储
        file_store_path (str | None): 存储路径
            - 对于local存储：本地目录路径（必需）
            - 对于s3存储：S3桶名称
            - 对于google_cloud存储：GCS桶名称
        file_store_web_hook_url (str | None): WebHook URL，用于存储操作通知
        file_store_web_hook_headers (dict | None): WebHook请求头

    Returns:
        FileStore: 配置好的文件存储实例

    Raises:
        ValueError: 当local存储类型未提供file_store_path时

    Examples:
        # 创建本地文件存储
        store = get_file_store('local', '/path/to/storage')

        # 创建S3存储
        store = get_file_store('s3', 'my-bucket')

        # 创建带WebHook的存储
        store = get_file_store(
            'local',
            '/path/to/storage',
            'https://api.example.com/webhook',
            {'Authorization': 'Bearer token'}
        )
    """
    store: FileStore

    # 根据存储类型创建相应的存储实例
    if file_store_type == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        store = LocalFileStore(file_store_path)
    elif file_store_type == 's3':
        store = S3FileStore(file_store_path)
    elif file_store_type == 'google_cloud':
        store = GoogleCloudFileStore(file_store_path)
    else:
        # 默认使用内存存储
        store = InMemoryFileStore()

    # 如果指定了WebHook URL，则用WebHook装饰器包装存储
    if file_store_web_hook_url:
        if file_store_web_hook_headers is None:
            # 使用默认请求头，如果环境变量中定义了SESSION_API_KEY则使用它
            file_store_web_hook_headers = {}
            if os.getenv('SESSION_API_KEY'):
                file_store_web_hook_headers['X-Session-API-Key'] = os.getenv(
                    'SESSION_API_KEY'
                )

        # 创建WebHook装饰器存储
        store = WebHookFileStore(
            store,
            file_store_web_hook_url,
            httpx.Client(headers=file_store_web_hook_headers or {}),
        )

    return store
