"""
OpenHands 微代理类型定义

定义了微代理系统中使用的数据类型和元数据结构，包括：
- 微代理类型枚举
- 输入元数据模型
- 微代理元数据模型

这些类型确保了微代理系统的类型安全和一致性。
"""

from enum import Enum

from pydantic import BaseModel, Field

from openhands.core.config.mcp_config import (
    MCPConfig,
)


class MicroagentType(str, Enum):
    """
    微代理类型枚举

    定义了OpenHands支持的微代理类型：
    - KNOWLEDGE: 知识微代理，通过关键词触发，提供特定领域知识
    - REPO_KNOWLEDGE: 仓库微代理，始终激活，提供项目特定上下文
    - TASK: 任务微代理，需要用户输入的特殊类型
    """

    KNOWLEDGE = 'knowledge'  # 可选微代理，通过关键词触发
    REPO_KNOWLEDGE = 'repo'  # 始终激活的微代理
    TASK = 'task'  # 需要用户输入的任务微代理


class InputMetadata(BaseModel):
    """
    任务微代理输入元数据

    定义任务微代理所需的输入参数信息，用于：
    - 生成用户界面表单
    - 验证输入参数
    - 提供参数描述和帮助信息

    Attributes:
        name (str): 输入参数名称
        description (str): 输入参数描述
    """

    name: str  # 参数名称
    description: str  # 参数描述


class MicroagentMetadata(BaseModel):
    """
    微代理元数据模型

    包含微代理的完整元数据信息，用于：
    - 微代理的注册和发现
    - 运行时配置和管理
    - 用户界面展示
    - 功能扩展和集成

    Attributes:
        name (str): 微代理名称
        type (MicroagentType): 微代理类型
        version (str): 版本号
        agent (str): 关联的代理类型
        triggers (list[str]): 触发关键词（仅知识微代理）
        inputs (list[InputMetadata]): 输入参数（仅任务微代理）
        mcp_tools (MCPConfig | None): MCP工具配置（可选）
    """

    name: str = 'default'  # 微代理名称
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)  # 微代理类型
    version: str = Field(default='1.0.0')  # 版本号
    agent: str = Field(default='CodeActAgent')  # 关联代理类型
    triggers: list[str] = []  # 触发关键词（知识微代理专用）
    inputs: list[InputMetadata] = []  # 输入参数（任务微代理专用）
    mcp_tools: MCPConfig | None = (  # MCP工具配置（可选）
        None  # 为微代理提供额外MCP工具的配置
    )
