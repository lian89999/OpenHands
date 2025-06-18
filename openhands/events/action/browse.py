"""
OpenHands 浏览器动作模块

定义了浏览器相关的动作类，包括：
- BrowseURLAction: 浏览URL动作
- BrowseInteractiveAction: 交互式浏览动作

这些动作允许代理与网页进行交互，包括访问URL和执行浏览器操作。
"""

from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk


@dataclass
class BrowseURLAction(Action):
    """
    浏览URL动作

    用于导航到指定的URL。支持返回可访问性树(accessibility tree)
    以便进行更详细的页面分析。

    Attributes:
        url (str): 要浏览的URL地址
        thought (str): 浏览此URL的思考过程
        action (str): 动作类型，固定为ActionType.BROWSE
        runnable (ClassVar[bool]): 标识此动作可以执行
        security_risk (ActionSecurityRisk | None): 安全风险等级
        return_axtree (bool): 是否返回可访问性树
    """

    url: str  # URL地址
    thought: str = ''  # 思考过程
    action: str = ActionType.BROWSE  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    security_risk: ActionSecurityRisk | None = None  # 安全风险
    return_axtree: bool = False  # 是否返回可访问性树

    @property
    def message(self) -> str:
        """返回浏览动作的描述消息"""
        return f'I am browsing the URL: {self.url}'

    def __str__(self) -> str:
        """返回浏览动作的字符串表示"""
        ret = '**BrowseURLAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'URL: {self.url}'
        return ret


@dataclass
class BrowseInteractiveAction(Action):
    """
    交互式浏览动作

    用于在浏览器中执行交互操作，如点击、输入文本、滚动等。
    支持复杂的浏览器自动化任务。

    Attributes:
        browser_actions (str): 要执行的浏览器动作序列
        thought (str): 执行这些动作的思考过程
        browsergym_send_msg_to_user (str): 发送给用户的BrowserGym消息
        action (str): 动作类型，固定为ActionType.BROWSE_INTERACTIVE
        runnable (ClassVar[bool]): 标识此动作可以执行
        security_risk (ActionSecurityRisk | None): 安全风险等级
        return_axtree (bool): 是否返回可访问性树
    """

    browser_actions: str  # 浏览器动作序列
    thought: str = ''  # 思考过程
    browsergym_send_msg_to_user: str = ''  # 用户消息
    action: str = ActionType.BROWSE_INTERACTIVE  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    security_risk: ActionSecurityRisk | None = None  # 安全风险
    return_axtree: bool = False  # 是否返回可访问性树

    @property
    def message(self) -> str:
        """返回交互动作的描述消息"""
        return f'I am interacting with the browser:\n```\n{self.browser_actions}\n```'

    def __str__(self) -> str:
        """返回交互动作的字符串表示"""
        ret = '**BrowseInteractiveAction**\n'
        if self.thought:
            ret += f'THOUGHT: {self.thought}\n'
        ret += f'BROWSER_ACTIONS: {self.browser_actions}'
        return ret
