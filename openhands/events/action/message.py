"""
OpenHands 消息动作模块

定义了消息相关的动作类，包括：
- MessageAction: 普通消息动作
- SystemMessageAction: 系统消息动作

这些动作用于在代理和用户之间传递消息和系统信息。
"""

from dataclasses import dataclass
from typing import Any

import openhands
from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class MessageAction(Action):
    """
    消息动作

    用于发送文本消息，支持包含图片URL。可以选择是否等待响应。

    Attributes:
        content (str): 消息内容
        image_urls (list[str] | None): 图片URL列表
        wait_for_response (bool): 是否等待响应
        action (str): 动作类型，固定为ActionType.MESSAGE
        security_risk (ActionSecurityRisk | None): 安全风险等级
    """

    content: str  # 消息内容
    image_urls: list[str] | None = None  # 图片URL列表
    wait_for_response: bool = False  # 是否等待响应
    action: str = ActionType.MESSAGE  # 动作类型
    security_risk: ActionSecurityRisk | None = None  # 安全风险

    @property
    def message(self) -> str:
        """返回消息内容"""
        return self.content

    @property
    def images_urls(self) -> list[str] | None:
        """向后兼容的已弃用别名"""
        return self.image_urls

    @images_urls.setter
    def images_urls(self, value: list[str] | None) -> None:
        """设置图片URL（向后兼容）"""
        self.image_urls = value

    def __str__(self) -> str:
        """返回消息动作的字符串表示"""
        ret = f'**MessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        if self.image_urls:
            for url in self.image_urls:
                ret += f'\nIMAGE_URL: {url}'
        return ret


@dataclass
class SystemMessageAction(Action):
    """
    系统消息动作

    表示代理的系统消息，包括系统提示和可用工具。
    这应该是事件流中的第一条消息。

    Attributes:
        content (str): 系统消息内容
        tools (list[Any] | None): 可用工具列表
        openhands_version (str | None): OpenHands版本
        agent_class (str | None): 代理类名
        action (ActionType): 动作类型，固定为ActionType.SYSTEM
    """

    content: str  # 系统消息内容
    tools: list[Any] | None = None  # 可用工具列表
    openhands_version: str | None = openhands.__version__  # OpenHands版本
    agent_class: str | None = None  # 代理类名
    action: ActionType = ActionType.SYSTEM  # 动作类型

    @property
    def message(self) -> str:
        """返回系统消息内容"""
        return self.content

    def __str__(self) -> str:
        """返回系统消息动作的字符串表示"""
        ret = f'**SystemMessageAction** (source={self.source})\n'
        ret += f'CONTENT: {self.content}'
        if self.tools:
            ret += f'\nTOOLS: {len(self.tools)} tools available'
        if self.agent_class:
            ret += f'\nAGENT_CLASS: {self.agent_class}'
        return ret
