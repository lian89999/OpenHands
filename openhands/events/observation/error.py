"""
OpenHands 错误观察模块

定义了错误观察类，用于表示代理遇到的可恢复错误。
"""

from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class ErrorObservation(Observation):
    """
    错误观察

    表示代理遇到的错误。这是LLM可以从中恢复的错误类型，
    例如编辑文件后的语法检查错误。

    Attributes:
        observation (str): 观察类型，固定为ObservationType.ERROR
        error_id (str): 错误标识符
        content (str): 继承自Observation，包含错误详细信息
    """

    observation: str = ObservationType.ERROR  # 观察类型
    error_id: str = ''  # 错误标识符

    @property
    def message(self) -> str:
        """返回错误消息内容"""
        return self.content

    def __str__(self) -> str:
        """返回错误观察的字符串表示"""
        return f'**ErrorObservation**\n{self.content}'
