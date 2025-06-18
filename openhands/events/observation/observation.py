"""
OpenHands 观察基类模块

定义了观察系统的基础类。
观察是对动作执行结果的反馈，包含执行的输出、错误信息或状态变化。
"""

from dataclasses import dataclass

from openhands.events.event import Event


@dataclass
class Observation(Event):
    """
    观察基类，继承自Event

    所有观察类型都继承自这个类。观察表示对代理动作的响应或反馈，
    包含执行结果、输出信息、错误消息等。

    Attributes:
        content (str): 观察的内容，通常是执行结果或输出信息
    """

    content: str  # 观察内容
