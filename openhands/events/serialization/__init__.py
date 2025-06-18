"""
OpenHands 事件序列化模块

提供事件系统的序列化和反序列化功能，包括：
- action_from_dict: 从字典创建动作对象
- event_from_dict: 从字典创建事件对象
- event_to_dict: 将事件对象转换为字典
- event_to_trajectory: 将事件转换为轨迹格式
- observation_from_dict: 从字典创建观察对象

这些函数用于事件的持久化存储和网络传输。
"""

from openhands.events.serialization.action import (
    action_from_dict,  # 从字典创建动作
)
from openhands.events.serialization.event import (
    event_from_dict,  # 从字典创建事件
    event_to_dict,  # 事件转字典
    event_to_trajectory,  # 事件转轨迹
)
from openhands.events.serialization.observation import (
    observation_from_dict,  # 从字典创建观察
)

__all__ = [
    'action_from_dict',  # 动作反序列化
    'event_from_dict',  # 事件反序列化
    'event_to_dict',  # 事件序列化
    'event_to_trajectory',  # 轨迹转换
    'observation_from_dict',  # 观察反序列化
]
