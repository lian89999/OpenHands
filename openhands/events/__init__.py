"""
OpenHands 事件系统模块

这个模块定义了 OpenHands 中的核心事件系统，包括：
- Event: 事件基类，所有事件的基础
- EventSource: 事件源枚举，标识事件来源
- EventStream: 事件流，用于事件的发布和订阅
- EventStreamSubscriber: 事件流订阅者接口
- RecallType: 回忆类型，用于内存管理

事件系统是 OpenHands 架构的核心，负责在不同组件之间传递信息和状态变化。
"""

from openhands.events.event import Event, EventSource, RecallType
from openhands.events.stream import EventStream, EventStreamSubscriber

__all__ = [
    'Event',  # 事件基类
    'EventSource',  # 事件源枚举
    'EventStream',  # 事件流
    'EventStreamSubscriber',  # 事件流订阅者
    'RecallType',  # 回忆类型
]
