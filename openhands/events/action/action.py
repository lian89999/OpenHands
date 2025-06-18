"""
OpenHands 动作基类模块

定义了动作系统的基础类和枚举，包括：
- Action: 所有动作的基类
- ActionConfirmationStatus: 动作确认状态枚举
- ActionSecurityRisk: 动作安全风险等级枚举
"""

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from openhands.events.event import Event


class ActionConfirmationStatus(str, Enum):
    """动作确认状态枚举，用于需要用户确认的动作"""

    CONFIRMED = 'confirmed'  # 已确认
    REJECTED = 'rejected'  # 已拒绝
    AWAITING_CONFIRMATION = 'awaiting_confirmation'  # 等待确认


class ActionSecurityRisk(int, Enum):
    """动作安全风险等级枚举，用于安全分析"""

    UNKNOWN = -1  # 未知风险
    LOW = 0  # 低风险
    MEDIUM = 1  # 中等风险
    HIGH = 2  # 高风险


@dataclass
class Action(Event):
    """
    动作基类，继承自Event

    所有代理可以执行的动作都继承自这个类。
    动作表示代理想要执行的操作，如运行命令、编辑文件等。

    Attributes:
        runnable (ClassVar[bool]): 类变量，标识此动作是否可以在运行时环境中执行
    """

    runnable: ClassVar[bool] = False  # 默认情况下动作不可运行
