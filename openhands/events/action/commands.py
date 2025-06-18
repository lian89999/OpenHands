"""
OpenHands 命令执行动作模块

定义了命令执行相关的动作类，包括：
- CmdRunAction: 运行bash命令的动作
- IPythonRunCellAction: 运行IPython代码单元的动作

这些动作允许代理执行系统命令和Python代码。
"""

from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import (
    Action,
    ActionConfirmationStatus,
    ActionSecurityRisk,
)


@dataclass
class CmdRunAction(Action):
    """
    命令运行动作

    用于在终端中执行bash命令。支持多种执行模式，包括阻塞/非阻塞、
    静态/动态执行等。

    Attributes:
        command (str): 要执行的命令。当为空时，用于打印当前tmux窗口
        is_input (bool): 如果为True，命令是对正在运行进程的输入
        thought (str): 执行此命令的思考过程
        blocking (bool): 如果为True，命令将以阻塞方式运行，但必须通过_set_hard_timeout设置超时
        is_static (bool): 如果为True，在单独的进程中运行命令
        cwd (str | None): 当前工作目录，仅在is_static为True时使用
        hidden (bool): 是否隐藏此命令的执行
        action (str): 动作类型，固定为ActionType.RUN
        runnable (ClassVar[bool]): 标识此动作可以执行
        confirmation_state (ActionConfirmationStatus): 确认状态
        security_risk (ActionSecurityRisk | None): 安全风险等级
    """

    command: str  # 要执行的命令
    is_input: bool = False  # 是否为进程输入
    thought: str = ''  # 思考过程
    blocking: bool = False  # 是否阻塞执行
    is_static: bool = False  # 是否静态执行
    cwd: str | None = None  # 工作目录
    hidden: bool = False  # 是否隐藏
    action: str = ActionType.RUN  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    confirmation_state: ActionConfirmationStatus = (
        ActionConfirmationStatus.CONFIRMED
    )  # 确认状态
    security_risk: ActionSecurityRisk | None = None  # 安全风险

    @property
    def message(self) -> str:
        """返回动作的描述消息"""
        return f'Running command: {self.command}'

    def __str__(self) -> str:
        """返回动作的字符串表示"""
        ret = f'**CmdRunAction (source={self.source}, is_input={self.is_input})**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'COMMAND:\n{self.command}'
        return ret


@dataclass
class IPythonRunCellAction(Action):
    """
    IPython运行单元动作

    用于在IPython环境中执行Python代码。支持包含额外信息
    如当前工作目录和Python解释器信息。

    Attributes:
        code (str): 要执行的Python代码
        thought (str): 执行此代码的思考过程
        include_extra (bool): 是否在输出中包含当前工作目录和Python解释器信息
        action (str): 动作类型，固定为ActionType.RUN_IPYTHON
        runnable (ClassVar[bool]): 标识此动作可以执行
        confirmation_state (ActionConfirmationStatus): 确认状态
        security_risk (ActionSecurityRisk | None): 安全风险等级
    """

    code: str  # Python代码
    thought: str = ''  # 思考过程
    include_extra: bool = True  # 是否包含额外信息
    action: str = ActionType.RUN_IPYTHON  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    confirmation_state: ActionConfirmationStatus = (
        ActionConfirmationStatus.CONFIRMED
    )  # 确认状态
    security_risk: ActionSecurityRisk | None = None  # 安全风险
    kernel_init_code: str = ''  # 内核初始化代码（内核重启时运行）

    def __str__(self) -> str:
        """返回动作的字符串表示"""
        ret = '**IPythonRunCellAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'CODE:\n{self.code}'
        return ret

    @property
    def message(self) -> str:
        """返回动作的描述消息"""
        return f'Running Python code interactively: {self.code}'
