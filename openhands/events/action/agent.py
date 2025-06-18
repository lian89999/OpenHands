"""
OpenHands 代理动作模块

定义了代理相关的动作类，包括：
- ChangeAgentStateAction: 改变代理状态动作
- AgentFinishAction: 代理完成任务动作
- AgentThinkAction: 代理思考动作
- AgentRejectAction: 代理拒绝动作
- AgentDelegateAction: 代理委托动作
- RecallAction: 回忆检索动作
- CondensationAction: 对话历史压缩动作

这些动作控制代理的状态变化和行为模式。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openhands.core.schema import ActionType
from openhands.events.action.action import Action
from openhands.events.event import RecallType


@dataclass
class ChangeAgentStateAction(Action):
    """
    改变代理状态动作

    这是一个虚拟动作，用于通知客户端任务状态已发生变化。
    不执行实际操作，仅用于状态同步。

    Attributes:
        agent_state (str): 新的代理状态
        thought (str): 状态变化的思考过程
        action (str): 动作类型，固定为ActionType.CHANGE_AGENT_STATE
    """

    agent_state: str  # 代理状态
    thought: str = ''  # 思考过程
    action: str = ActionType.CHANGE_AGENT_STATE  # 动作类型

    @property
    def message(self) -> str:
        """返回状态变化的描述消息"""
        return f'Agent state changed to {self.agent_state}'


class AgentFinishTaskCompleted(Enum):
    """代理任务完成状态枚举"""

    FALSE = 'false'  # 任务未完成
    PARTIAL = 'partial'  # 任务部分完成
    TRUE = 'true'  # 任务完全完成


@dataclass
class AgentFinishAction(Action):
    """
    代理完成任务动作

    当代理认为任务已完成时使用此动作。包含最终思考、
    完成状态和输出结果。

    Attributes:
        final_thought (str): 发送给用户的最终消息
        task_completed (AgentFinishTaskCompleted | None): 代理认为任务是否已完成
        outputs (dict[str, Any]): 代理的其他输出，例如"content"
        thought (str): 代理对其行为的解释
        action (str): 动作类型，固定为ActionType.FINISH
    """

    final_thought: str = ''  # 最终思考
    task_completed: AgentFinishTaskCompleted | None = None  # 任务完成状态
    outputs: dict[str, Any] = field(default_factory=dict)  # 输出结果
    thought: str = ''  # 思考过程
    action: str = ActionType.FINISH  # 动作类型

    @property
    def message(self) -> str:
        """返回完成动作的描述消息"""
        if self.thought != '':
            return self.thought
        return "All done! What's next on the agenda?"


@dataclass
class AgentThinkAction(Action):
    """
    代理思考动作

    代理记录思考过程的动作。用于展示代理的推理过程，
    帮助用户理解代理的决策逻辑。

    Attributes:
        thought (str): 代理对其行为的解释
        action (str): 动作类型，固定为ActionType.THINK
    """

    thought: str = ''  # 思考内容
    action: str = ActionType.THINK  # 动作类型

    @property
    def message(self) -> str:
        """返回思考动作的描述消息"""
        return f'I am thinking...: {self.thought}'


@dataclass
class AgentRejectAction(Action):
    """
    代理拒绝动作

    当代理拒绝执行某个任务时使用此动作。
    可以包含拒绝的原因和相关输出。

    Attributes:
        outputs (dict): 拒绝相关的输出信息
        thought (str): 拒绝的思考过程
        action (str): 动作类型，固定为ActionType.REJECT
    """

    outputs: dict = field(default_factory=dict)  # 输出信息
    thought: str = ''  # 思考过程
    action: str = ActionType.REJECT  # 动作类型

    @property
    def message(self) -> str:
        """返回拒绝动作的描述消息"""
        msg: str = 'Task is rejected by the agent.'
        if 'reason' in self.outputs:
            msg += ' Reason: ' + self.outputs['reason']
        return msg


@dataclass
class AgentDelegateAction(Action):
    """
    代理委托动作

    当代理需要将任务委托给其他代理时使用此动作。
    包含目标代理和输入参数。

    Attributes:
        agent (str): 目标代理名称
        inputs (dict): 传递给目标代理的输入参数
        thought (str): 委托的思考过程
        action (str): 动作类型，固定为ActionType.DELEGATE
    """

    agent: str  # 目标代理
    inputs: dict  # 输入参数
    thought: str = ''  # 思考过程
    action: str = ActionType.DELEGATE  # 动作类型

    @property
    def message(self) -> str:
        """返回委托动作的描述消息"""
        return f"I'm asking {self.agent} for help with this task."


@dataclass
class RecallAction(Action):
    """
    回忆检索动作

    用于从全局目录或用户工作空间检索内容。
    支持不同类型的回忆检索，如工作空间上下文和知识库。

    Attributes:
        recall_type (RecallType): 回忆类型
        query (str): 检索查询
        thought (str): 检索的思考过程
        action (str): 动作类型，固定为ActionType.RECALL
    """

    recall_type: RecallType  # 回忆类型
    query: str = ''  # 检索查询
    thought: str = ''  # 思考过程
    action: str = ActionType.RECALL  # 动作类型

    @property
    def message(self) -> str:
        """返回检索动作的描述消息"""
        return f'Retrieving content for: {self.query[:50]}'

    def __str__(self) -> str:
        """返回检索动作的字符串表示"""
        ret = '**RecallAction**\n'
        ret += f'QUERY: {self.query[:50]}'
        return ret


@dataclass
class CondensationAction(Action):
    """
    对话历史压缩动作

    此动作表示正在进行对话历史的压缩。用于管理长对话中的内存使用，
    通过遗忘某些事件来保持上下文窗口在合理范围内。

    有两种方式指定要遗忘的事件：
    1. 提供事件ID列表
    2. 提供事件范围的起始和结束ID

    在第二种情况下，假设事件ID是单调递增的，起始和结束ID之间的
    所有事件都将被遗忘。

    Attributes:
        action (str): 动作类型，固定为ActionType.CONDENSATION
        forgotten_event_ids (list[int] | None): 要遗忘的事件ID列表
        forgotten_events_start_id (int | None): 要遗忘的事件范围起始ID
        forgotten_events_end_id (int | None): 要遗忘的事件范围结束ID
        summary (str | None): 被遗忘事件的可选摘要
        summary_offset (int | None): 摘要插入位置的可选偏移量

    Raises:
        ValueError: 如果可选字段的配置无效
    """

    action: str = ActionType.CONDENSATION

    forgotten_event_ids: list[int] | None = None
    """要遗忘的事件ID列表（从给LLM的视图中移除）"""

    forgotten_events_start_id: int | None = None
    """事件范围中第一个要遗忘的事件ID"""

    forgotten_events_end_id: int | None = None
    """事件范围中最后一个要遗忘的事件ID"""

    summary: str | None = None
    """被遗忘事件的可选摘要"""

    summary_offset: int | None = None
    """结果视图开始处的可选偏移量，指示摘要应插入的位置"""

    def _validate_field_polymorphism(self) -> bool:
        """
        检查可选字段是否以有效配置实例化

        Returns:
            bool: 如果配置有效返回True，否则返回False
        """
        # 对于遗忘的事件，只有两种有效配置：
        # 1. 基于提供的ID列表遗忘事件，或
        using_event_ids = self.forgotten_event_ids is not None
        # 2. 基于ID范围遗忘事件
        using_event_range = (
            self.forgotten_events_start_id is not None
            and self.forgotten_events_end_id is not None
        )

        # 无论哪种方式，我们只能有两种有效配置中的一种
        forgotten_event_configuration = using_event_ids ^ using_event_range

        # 我们还需要检查如果提供了摘要，也必须提供偏移量（反之亦然）
        summary_configuration = (
            self.summary is None and self.summary_offset is None
        ) or (self.summary is not None and self.summary_offset is not None)

        return forgotten_event_configuration and summary_configuration

    def __post_init__(self):
        """初始化后验证字段配置"""
        if not self._validate_field_polymorphism():
            raise ValueError('Invalid configuration of the optional fields.')

    @property
    def forgotten(self) -> list[int]:
        """
        应该被遗忘的事件ID列表

        Returns:
            list[int]: 要遗忘的事件ID列表

        Raises:
            ValueError: 如果字段配置无效
        """
        # 首先确保字段以有效配置实例化。我们在事件初始化时检查这一点，
        # 但我们不能使数据类不可变，所以需要在这里再次检查以确保配置仍然有效
        if not self._validate_field_polymorphism():
            raise ValueError('Invalid configuration of the optional fields.')

        if self.forgotten_event_ids is not None:
            return self.forgotten_event_ids

        # 如果到了这里，起始/结束ID不为None
        assert self.forgotten_events_start_id is not None
        assert self.forgotten_events_end_id is not None
        return list(
            range(self.forgotten_events_start_id, self.forgotten_events_end_id + 1)
        )

    @property
    def message(self) -> str:
        """返回压缩动作的描述消息"""
        if self.summary:
            return f'Summary: {self.summary}'
        return f'Condenser is dropping the events: {self.forgotten}.'
