"""
OpenHands 微代理模块

微代理(Microagent)是OpenHands中的一个重要概念，用于增强AI代理的特定领域知识和能力。
微代理系统提供了一种模块化的方式来扩展代理的功能，包括：

- 知识微代理：提供特定领域的知识和指导
- 仓库微代理：提供项目特定的上下文和最佳实践
- 可扩展的微代理框架：支持自定义微代理类型

技术特点：
- 基于Jinja2模板的提示词生成
- 元数据驱动的微代理管理
- 动态加载和注册机制
- 类型安全的微代理接口
"""

from .microagent import (
    BaseMicroagent,
    KnowledgeMicroagent,
    RepoMicroagent,
    load_microagents_from_dir,
)
from .types import MicroagentMetadata, MicroagentType

__all__ = [
    'BaseMicroagent',
    'KnowledgeMicroagent',
    'RepoMicroagent',
    'MicroagentMetadata',
    'MicroagentType',
    'load_microagents_from_dir',
]
