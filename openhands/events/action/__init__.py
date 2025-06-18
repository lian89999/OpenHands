"""
OpenHands 动作模块

这个模块定义了所有可能的动作类型，包括：
- Action: 动作基类
- 代理动作：思考、完成、拒绝、委托等
- 文件操作动作：读取、写入、编辑文件
- 命令执行动作：运行bash命令、Python代码
- 浏览器动作：访问URL、交互式浏览
- 消息动作：发送消息、系统消息
- MCP动作：模型上下文协议动作
"""

from openhands.events.action.action import Action, ActionConfirmationStatus
from openhands.events.action.agent import (
    AgentDelegateAction,  # 代理委托动作
    AgentFinishAction,  # 代理完成动作
    AgentRejectAction,  # 代理拒绝动作
    AgentThinkAction,  # 代理思考动作
    ChangeAgentStateAction,  # 改变代理状态动作
    RecallAction,  # 回忆动作
)
from openhands.events.action.browse import BrowseInteractiveAction, BrowseURLAction
from openhands.events.action.commands import CmdRunAction, IPythonRunCellAction
from openhands.events.action.empty import NullAction
from openhands.events.action.files import (
    FileEditAction,  # 文件编辑动作
    FileReadAction,  # 文件读取动作
    FileWriteAction,  # 文件写入动作
)
from openhands.events.action.mcp import MCPAction
from openhands.events.action.message import MessageAction, SystemMessageAction

__all__ = [
    'Action',  # 动作基类
    'NullAction',  # 空动作
    'CmdRunAction',  # 命令运行动作
    'BrowseURLAction',  # 浏览URL动作
    'BrowseInteractiveAction',  # 交互式浏览动作
    'FileReadAction',  # 文件读取动作
    'FileWriteAction',  # 文件写入动作
    'FileEditAction',  # 文件编辑动作
    'AgentFinishAction',  # 代理完成动作
    'AgentRejectAction',  # 代理拒绝动作
    'AgentDelegateAction',  # 代理委托动作
    'ChangeAgentStateAction',  # 改变代理状态动作
    'IPythonRunCellAction',  # IPython运行单元动作
    'MessageAction',  # 消息动作
    'SystemMessageAction',  # 系统消息动作
    'ActionConfirmationStatus',  # 动作确认状态
    'AgentThinkAction',  # 代理思考动作
    'RecallAction',  # 回忆动作
    'MCPAction',  # MCP动作
]
