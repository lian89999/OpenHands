"""
OpenHands 事件系统核心模块

定义了事件系统的基础类和枚举，包括：
- Event: 所有事件的基类
- EventSource: 事件来源枚举
- FileEditSource: 文件编辑来源枚举
- FileReadSource: 文件读取来源枚举
- RecallType: 回忆类型枚举
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Metrics


class EventSource(str, Enum):
    """事件来源枚举，标识事件的产生者"""

    AGENT = 'agent'  # 代理产生的事件
    USER = 'user'  # 用户产生的事件
    ENVIRONMENT = 'environment'  # 环境产生的事件


class FileEditSource(str, Enum):
    """文件编辑来源枚举，标识文件编辑操作的来源"""

    LLM_BASED_EDIT = 'llm_based_edit'  # 基于LLM的编辑
    OH_ACI = 'oh_aci'  # OpenHands ACI (自动代码改进)


class FileReadSource(str, Enum):
    """文件读取来源枚举，标识文件读取操作的来源"""

    OH_ACI = 'oh_aci'  # OpenHands ACI (自动代码改进)
    DEFAULT = 'default'  # 默认读取方式


class RecallType(str, Enum):
    """回忆类型枚举，定义可以从微代理检索的信息类型"""

    WORKSPACE_CONTEXT = 'workspace_context'
    """工作空间上下文信息（仓库指令、运行时环境等）"""

    KNOWLEDGE = 'knowledge'
    """知识型微代理提供的信息"""


@dataclass
class Event:
    """
    事件基类，所有OpenHands事件的基础类

    这个类定义了所有事件共有的属性和方法，包括：
    - 事件ID和时间戳
    - 事件来源和原因
    - 超时设置
    - LLM指标和工具调用元数据
    """

    INVALID_ID = -1  # 无效事件ID的常量

    @property
    def message(self) -> str | None:
        """
        获取事件消息内容

        Returns:
            str | None: 事件的消息内容，如果没有消息则返回空字符串
        """
        if hasattr(self, '_message'):
            msg = getattr(self, '_message')
            return str(msg) if msg is not None else None
        return ''

    @property
    def id(self) -> int:
        """
        获取事件ID

        Returns:
            int: 事件的唯一标识符，如果没有设置则返回INVALID_ID
        """
        if hasattr(self, '_id'):
            id_val = getattr(self, '_id')
            return int(id_val) if id_val is not None else Event.INVALID_ID
        return Event.INVALID_ID

    @property
    def timestamp(self) -> str | None:
        """
        获取事件时间戳

        Returns:
            str | None: ISO格式的时间戳字符串
        """
        if hasattr(self, '_timestamp') and isinstance(self._timestamp, str):
            ts = getattr(self, '_timestamp')
            return str(ts) if ts is not None else None
        return None

    @timestamp.setter
    def timestamp(self, value: datetime) -> None:
        """
        设置事件时间戳

        Args:
            value (datetime): 要设置的时间戳
        """
        if isinstance(value, datetime):
            self._timestamp = value.isoformat()

    @property
    def source(self) -> EventSource | None:
        """
        获取事件来源

        Returns:
            EventSource | None: 事件的来源（AGENT、USER或ENVIRONMENT）
        """
        if hasattr(self, '_source'):
            src = getattr(self, '_source')
            return EventSource(src) if src is not None else None
        return None

    @property
    def cause(self) -> int | None:
        """
        获取事件原因（触发此事件的事件ID）

        Returns:
            int | None: 触发此事件的事件ID
        """
        if hasattr(self, '_cause'):
            cause_val = getattr(self, '_cause')
            return int(cause_val) if cause_val is not None else None
        return None

    @property
    def timeout(self) -> float | None:
        """
        获取事件超时时间

        Returns:
            float | None: 超时时间（秒），如果没有设置则返回None
        """
        if hasattr(self, '_timeout'):
            timeout_val = getattr(self, '_timeout')
            return float(timeout_val) if timeout_val is not None else None
        return None

    def set_hard_timeout(self, value: float | None, blocking: bool = True) -> None:
        """
        设置事件的硬超时时间

        注意：这是一个硬超时，意味着事件将被阻塞直到超时时间到达

        Args:
            value (float | None): 超时时间（秒），None表示无超时
            blocking (bool): 是否阻塞执行，默认为True
        """
        self._timeout = value
        if value is not None and value > 600:
            from openhands.core.logger import openhands_logger as logger

            logger.warning(
                'Timeout greater than 600 seconds may not be supported by '
                'the runtime. Consider setting a lower timeout.'
            )

        # 检查事件是否有blocking属性
        if hasattr(self, 'blocking'):
            # 如果设置了timeout，blocking需要设置为True
            self.blocking = blocking

    @property
    def llm_metrics(self) -> Metrics | None:
        """
        获取LLM调用的性能指标

        Returns:
            Metrics | None: LLM调用的成本和性能指标
        """
        if hasattr(self, '_llm_metrics'):
            metrics = getattr(self, '_llm_metrics')
            return metrics if isinstance(metrics, Metrics) else None
        return None

    @llm_metrics.setter
    def llm_metrics(self, value: Metrics) -> None:
        """
        设置LLM调用的性能指标

        Args:
            value (Metrics): LLM调用的性能指标
        """
        self._llm_metrics = value

    @property
    def tool_call_metadata(self) -> ToolCallMetadata | None:
        """
        获取工具调用的元数据

        Returns:
            ToolCallMetadata | None: 工具调用的元数据信息
        """
        if hasattr(self, '_tool_call_metadata'):
            metadata = getattr(self, '_tool_call_metadata')
            return metadata if isinstance(metadata, ToolCallMetadata) else None
        return None

    @tool_call_metadata.setter
    def tool_call_metadata(self, value: ToolCallMetadata) -> None:
        """
        设置工具调用的元数据

        Args:
            value (ToolCallMetadata): 工具调用的元数据
        """
        self._tool_call_metadata = value

    @property
    def response_id(self) -> str | None:
        """
        获取LLM响应的ID

        Returns:
            str | None: LLM响应的唯一标识符
        """
        if hasattr(self, '_response_id'):
            return self._response_id  # type: ignore[attr-defined]
        return None

    @response_id.setter
    def response_id(self, value: str) -> None:
        """
        设置LLM响应的ID

        Args:
            value (str): LLM响应的唯一标识符
        """
        self._response_id = value
