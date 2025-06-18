"""
OpenHands 观察模块

这个模块定义了所有可能的观察类型，包括：
- Observation: 观察基类
- 代理观察：思考、状态变化、委托等
- 文件操作观察：读取、写入、编辑文件的结果
- 命令执行观察：bash命令、Python代码执行的输出
- 浏览器观察：浏览器操作的输出
- 错误和成功观察：操作结果的反馈
- MCP观察：模型上下文协议观察

观察是对动作执行结果的反馈，提供给代理用于决策。
"""

from openhands.events.event import RecallType
from openhands.events.observation.agent import (
    AgentCondensationObservation,  # 代理压缩观察
    AgentStateChangedObservation,  # 代理状态变化观察
    AgentThinkObservation,  # 代理思考观察
    RecallObservation,  # 回忆观察
)
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,  # 命令输出元数据
    CmdOutputObservation,  # 命令输出观察
    IPythonRunCellObservation,  # IPython运行单元观察
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.empty import (
    NullObservation,  # 空观察
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import (
    FileEditObservation,  # 文件编辑观察
    FileReadObservation,  # 文件读取观察
    FileWriteObservation,  # 文件写入观察
)
from openhands.events.observation.mcp import MCPObservation
from openhands.events.observation.observation import Observation
from openhands.events.observation.reject import UserRejectObservation
from openhands.events.observation.success import SuccessObservation

__all__ = [
    'Observation',  # 观察基类
    'NullObservation',  # 空观察
    'AgentThinkObservation',  # 代理思考观察
    'CmdOutputObservation',  # 命令输出观察
    'CmdOutputMetadata',  # 命令输出元数据
    'IPythonRunCellObservation',  # IPython运行单元观察
    'BrowserOutputObservation',  # 浏览器输出观察
    'FileReadObservation',  # 文件读取观察
    'FileWriteObservation',  # 文件写入观察
    'FileEditObservation',  # 文件编辑观察
    'ErrorObservation',  # 错误观察
    'AgentStateChangedObservation',  # 代理状态变化观察
    'AgentDelegateObservation',  # 代理委托观察
    'SuccessObservation',  # 成功观察
    'UserRejectObservation',  # 用户拒绝观察
    'AgentCondensationObservation',  # 代理压缩观察
    'RecallObservation',  # 回忆观察
    'RecallType',  # 回忆类型
    'MCPObservation',  # MCP观察
]
