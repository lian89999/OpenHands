"""
OpenHands 会话管理模块

这个模块定义了Session类，负责管理用户会话的完整生命周期，包括：
- WebSocket连接管理
- 代理会话的创建和控制
- 事件流的处理和转发
- 用户状态的维护

Session是服务器端会话管理的核心组件，连接了前端用户和后端代理系统。
"""

import asyncio
import time
from copy import deepcopy
from logging import LoggerAdapter

import socketio

from openhands.controller.agent import Agent
from openhands.core.config import OpenHandsConfig
from openhands.core.config.condenser_config import (
    BrowserOutputCondenserConfig,
    CondenserPipelineConfig,
    LLMSummarizingCondenserConfig,
)
from openhands.core.config.mcp_config import MCPConfig, OpenHandsMCPConfigImpl
from openhands.core.exceptions import MicroagentValidationError
from openhands.core.logger import OpenHandsLoggerAdapter
from openhands.core.schema import AgentState
from openhands.events.action import MessageAction, NullAction
from openhands.events.event import Event, EventSource
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    NullObservation,
)
from openhands.events.observation.agent import RecallObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.serialization import event_from_dict, event_to_dict
from openhands.events.stream import EventStreamSubscriber
from openhands.llm.llm import LLM
from openhands.server.session.agent_session import AgentSession
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore

# WebSocket房间键模板，用于Socket.IO房间管理
ROOM_KEY = 'room:{sid}'


class Session:
    """
    用户会话管理类

    Session类是OpenHands服务器端会话管理的核心组件，负责：
    - 管理单个用户的WebSocket连接
    - 协调前端UI和后端代理之间的通信
    - 处理事件流的订阅和转发
    - 维护会话状态和生命周期

    每个Session实例对应一个用户会话，包含一个AgentSession来管理代理交互。

    Attributes:
        sid (str): 会话唯一标识符
        sio (socketio.AsyncServer | None): Socket.IO服务器实例
        last_active_ts (int): 最后活跃时间戳
        is_alive (bool): 会话是否存活
        agent_session (AgentSession): 代理会话实例
        loop (asyncio.AbstractEventLoop): 异步事件循环
        config (OpenHandsConfig): 配置对象副本
        file_store (FileStore): 文件存储实例
        user_id (str | None): 用户ID
        logger (LoggerAdapter): 日志记录器
    """

    sid: str  # 会话ID
    sio: socketio.AsyncServer | None  # Socket.IO服务器
    last_active_ts: int = 0  # 最后活跃时间
    is_alive: bool = True  # 会话存活状态
    agent_session: AgentSession  # 代理会话
    loop: asyncio.AbstractEventLoop  # 事件循环
    config: OpenHandsConfig  # 配置对象
    file_store: FileStore  # 文件存储
    user_id: str | None  # 用户ID
    logger: LoggerAdapter  # 日志记录器

    def __init__(
        self,
        sid: str,
        config: OpenHandsConfig,
        file_store: FileStore,
        sio: socketio.AsyncServer | None,
        user_id: str | None = None,
    ):
        """
        初始化会话

        Args:
            sid (str): 会话唯一标识符
            config (OpenHandsConfig): OpenHands配置对象
            file_store (FileStore): 文件存储实例
            sio (socketio.AsyncServer | None): Socket.IO服务器实例
            user_id (str | None): 用户ID，可选
        """
        self.sid = sid
        self.sio = sio
        self.last_active_ts = int(time.time())
        self.file_store = file_store

        # 创建带会话ID的日志记录器
        self.logger = OpenHandsLoggerAdapter(extra={'session_id': sid})

        # 创建代理会话，设置状态回调
        self.agent_session = AgentSession(
            sid,
            file_store,
            status_callback=self.queue_status_message,
            user_id=user_id,
        )

        # 订阅代理会话的事件流
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event, self.sid
        )

        # 深拷贝配置，确保会话级别的配置修改不影响全局配置
        self.config = deepcopy(config)
        self.loop = asyncio.get_event_loop()
        self.user_id = user_id

    async def close(self) -> None:
        if self.sio:
            await self.sio.emit(
                'oh_event',
                event_to_dict(
                    AgentStateChangedObservation('', AgentState.STOPPED.value)
                ),
                to=ROOM_KEY.format(sid=self.sid),
            )
        self.is_alive = False
        await self.agent_session.close()

    async def initialize_agent(
        self,
        settings: Settings,
        initial_message: MessageAction | None,
        replay_json: str | None,
    ) -> None:
        self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )
        agent_cls = settings.agent or self.config.default_agent
        self.config.security.confirmation_mode = (
            self.config.security.confirmation_mode
            if settings.confirmation_mode is None
            else settings.confirmation_mode
        )
        self.config.security.security_analyzer = (
            settings.security_analyzer or self.config.security.security_analyzer
        )
        self.config.sandbox.base_container_image = (
            settings.sandbox_base_container_image
            or self.config.sandbox.base_container_image
        )
        self.config.sandbox.runtime_container_image = (
            settings.sandbox_runtime_container_image
            if settings.sandbox_base_container_image
            or settings.sandbox_runtime_container_image
            else self.config.sandbox.runtime_container_image
        )
        max_iterations = settings.max_iterations or self.config.max_iterations

        # This is a shallow copy of the default LLM config, so changes here will
        # persist if we retrieve the default LLM config again when constructing
        # the agent
        default_llm_config = self.config.get_llm_config()
        default_llm_config.model = settings.llm_model or ''
        default_llm_config.api_key = settings.llm_api_key
        default_llm_config.base_url = settings.llm_base_url
        self.config.search_api_key = settings.search_api_key

        # NOTE: this need to happen AFTER the config is updated with the search_api_key
        self.config.mcp = settings.mcp_config or MCPConfig(
            sse_servers=[], stdio_servers=[]
        )
        # Add OpenHands' MCP server by default
        openhands_mcp_server, openhands_mcp_stdio_servers = (
            OpenHandsMCPConfigImpl.create_default_mcp_server_config(
                self.config.mcp_host, self.config, self.user_id
            )
        )
        if openhands_mcp_server:
            self.config.mcp.shttp_servers.append(openhands_mcp_server)
        self.config.mcp.stdio_servers.extend(openhands_mcp_stdio_servers)

        # TODO: override other LLM config & agent config groups (#2075)

        llm = self._create_llm(agent_cls)
        agent_config = self.config.get_agent_config(agent_cls)

        if settings.enable_default_condenser:
            # Default condenser chains a condenser that limits browser the total
            # size of browser observations with a condenser that limits the size
            # of the view given to the LLM. The order matters: with the browser
            # output first, the summarizer will only see the most recent browser
            # output, which should keep the summarization cost down.
            default_condenser_config = CondenserPipelineConfig(
                condensers=[
                    BrowserOutputCondenserConfig(attention_window=2),
                    LLMSummarizingCondenserConfig(
                        llm_config=llm.config, keep_first=4, max_size=120
                    ),
                ]
            )

            self.logger.info(
                f'Enabling pipeline condenser with:'
                f' browser_output_masking(attention_window=2), '
                f' llm(model="{llm.config.model}", '
                f' base_url="{llm.config.base_url}", '
                f' keep_first=4, max_size=80)'
            )
            agent_config.condenser = default_condenser_config
        agent = Agent.get_cls(agent_cls)(llm, agent_config)

        git_provider_tokens = None
        selected_repository = None
        selected_branch = None
        custom_secrets = None
        conversation_instructions = None
        if isinstance(settings, ConversationInitData):
            git_provider_tokens = settings.git_provider_tokens
            selected_repository = settings.selected_repository
            selected_branch = settings.selected_branch
            custom_secrets = settings.custom_secrets
            conversation_instructions = settings.conversation_instructions

        try:
            await self.agent_session.start(
                runtime_name=self.config.runtime,
                config=self.config,
                agent=agent,
                max_iterations=max_iterations,
                max_budget_per_task=self.config.max_budget_per_task,
                agent_to_llm_config=self.config.get_agent_to_llm_config_map(),
                agent_configs=self.config.get_agent_configs(),
                git_provider_tokens=git_provider_tokens,
                custom_secrets=custom_secrets,
                selected_repository=selected_repository,
                selected_branch=selected_branch,
                initial_message=initial_message,
                conversation_instructions=conversation_instructions,
                replay_json=replay_json,
            )
        except MicroagentValidationError as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            # For microagent validation errors, provide more helpful information
            await self.send_error(f'Failed to create agent session: {str(e)}')
            return
        except ValueError as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            error_message = str(e)
            # For ValueError related to microagents, provide more helpful information
            if 'microagent' in error_message.lower():
                await self.send_error(
                    f'Failed to create agent session: {error_message}'
                )
            else:
                # For other ValueErrors, just show the error class
                await self.send_error('Failed to create agent session: ValueError')
            return
        except Exception as e:
            self.logger.exception(f'Error creating agent_session: {e}')
            # For other errors, just show the error class to avoid exposing sensitive information
            await self.send_error(
                f'Failed to create agent session: {e.__class__.__name__}'
            )
            return

    def _create_llm(self, agent_cls: str | None) -> LLM:
        """Initialize LLM, extracted for testing."""
        agent_name = agent_cls if agent_cls is not None else 'agent'
        return LLM(
            config=self.config.get_llm_config_from_agent(agent_name),
            retry_listener=self._notify_on_llm_retry,
        )

    def _notify_on_llm_retry(self, retries: int, max: int) -> None:
        msg_id = 'STATUS$LLM_RETRY'
        self.queue_status_message(
            'info', msg_id, f'Retrying LLM request, {retries} / {max}'
        )

    def on_event(self, event: Event) -> None:
        asyncio.get_event_loop().run_until_complete(self._on_event(event))

    async def _on_event(self, event: Event) -> None:
        """Callback function for events that mainly come from the agent.
        Event is the base class for any agent action and observation.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == EventSource.AGENT:
            await self.send(event_to_dict(event))
        elif event.source == EventSource.USER:
            await self.send(event_to_dict(event))
        # NOTE: ipython observations are not sent here currently
        elif event.source == EventSource.ENVIRONMENT and isinstance(
            event,
            (CmdOutputObservation, AgentStateChangedObservation, RecallObservation),
        ):
            # feedback from the environment to agent actions is understood as agent events by the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)
            if (
                isinstance(event, AgentStateChangedObservation)
                and event.agent_state == AgentState.ERROR
            ):
                self.logger.error(
                    f'Agent status error: {event.reason}',
                    extra={'signal': 'agent_status_error'},
                )
        elif isinstance(event, ErrorObservation):
            # send error events as agent events to the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)

    async def dispatch(self, data: dict) -> None:
        event = event_from_dict(data.copy())
        # This checks if the model supports images
        if isinstance(event, MessageAction) and event.image_urls:
            controller = self.agent_session.controller
            if controller:
                if controller.agent.llm.config.disable_vision:
                    await self.send_error(
                        'Support for images is disabled for this model, try without an image.'
                    )
                    return
                if not controller.agent.llm.vision_is_active():
                    await self.send_error(
                        'Model does not support image upload, change to a different model or try without an image.'
                    )
                    return
        self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> None:
        if asyncio.get_running_loop() != self.loop:
            self.loop.create_task(self._send(data))
            return
        await self._send(data)

    async def _send(self, data: dict[str, object]) -> bool:
        try:
            if not self.is_alive:
                return False
            if self.sio:
                await self.sio.emit('oh_event', data, to=ROOM_KEY.format(sid=self.sid))
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except RuntimeError as e:
            self.logger.error(f'Error sending data to websocket: {str(e)}')
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> None:
        """Sends an error message to the client."""
        await self.send({'error': True, 'message': message})

    async def _send_status_message(self, msg_type: str, id: str, message: str) -> None:
        """Sends a status message to the client."""
        if msg_type == 'error':
            agent_session = self.agent_session
            controller = self.agent_session.controller
            if controller is not None and not agent_session.is_closed():
                await controller.set_agent_state_to(AgentState.ERROR)
            self.logger.error(
                f'Agent status error: {message}',
                extra={'signal': 'agent_status_error'},
            )
        await self.send(
            {'status_update': True, 'type': msg_type, 'id': id, 'message': message}
        )

    def queue_status_message(self, msg_type: str, id: str, message: str) -> None:
        """Queues a status message to be sent asynchronously."""
        asyncio.run_coroutine_threadsafe(
            self._send_status_message(msg_type, id, message), self.loop
        )
