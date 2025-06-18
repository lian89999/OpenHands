"""
OpenHands 微代理核心实现

这个模块包含了微代理系统的核心实现，包括：
- 基础微代理类和子类
- 微代理加载和验证逻辑
- 不同类型微代理的特化功能
- 动态微代理发现和注册

微代理是OpenHands中用于增强AI代理能力的模块化组件，
通过提供特定领域的知识和指导来提升代理的表现。
"""

import io
import re
from pathlib import Path
from typing import Union

import frontmatter
from pydantic import BaseModel

from openhands.core.exceptions import (
    MicroagentValidationError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.microagent.types import InputMetadata, MicroagentMetadata, MicroagentType


class BaseMicroagent(BaseModel):
    """
    微代理基类

    所有微代理的基础类，提供通用的属性和方法。
    微代理通过Markdown文件定义，支持frontmatter元数据。

    Attributes:
        name (str): 微代理名称，通常从文件路径派生
        content (str): 微代理内容，包含指导和知识
        metadata (MicroagentMetadata): 微代理元数据
        source (str): 源文件路径
        type (MicroagentType): 微代理类型
    """

    name: str  # 微代理名称
    content: str  # 微代理内容
    metadata: MicroagentMetadata  # 元数据
    source: str  # 源文件路径
    type: MicroagentType  # 微代理类型

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        microagent_dir: Path | None = None,
        file_content: str | None = None,
    ) -> 'BaseMicroagent':
        """
        从Markdown文件加载微代理

        支持从带有frontmatter的Markdown文件加载微代理。
        微代理名称从相对于microagent_dir的路径派生。

        Args:
            path (Union[str, Path]): 微代理文件路径
            microagent_dir (Path | None): 微代理目录路径，用于计算相对名称
            file_content (str | None): 文件内容，如果提供则不从文件读取

        Returns:
            BaseMicroagent: 加载的微代理实例

        Raises:
            MicroagentValidationError: 当微代理验证失败时
            ValueError: 当无法确定微代理类型时
        """
        path = Path(path) if isinstance(path, str) else path

        # 如果提供了微代理目录，从相对路径计算派生名称
        # 否则，稍后依赖元数据中的名称
        derived_name = None
        if microagent_dir is not None:
            derived_name = str(path.relative_to(microagent_dir).with_suffix(''))

        # 只有在未提供文件内容时才从路径直接加载
        if file_content is None:
            with open(path) as f:
                file_content = f.read()

        # 遗留的仓库指令存储在.openhands_instructions中
        if path.name == '.openhands_instructions':
            return RepoMicroagent(
                name='repo_legacy',
                content=file_content,
                metadata=MicroagentMetadata(name='repo_legacy'),
                source=str(path),
                type=MicroagentType.REPO_KNOWLEDGE,
            )

        file_io = io.StringIO(file_content)
        loaded = frontmatter.load(file_io)
        content = loaded.content

        # Handle case where there's no frontmatter or empty frontmatter
        metadata_dict = loaded.metadata or {}

        try:
            metadata = MicroagentMetadata(**metadata_dict)

            # Validate MCP tools configuration if present
            if metadata.mcp_tools:
                if metadata.mcp_tools.sse_servers:
                    logger.warning(
                        f'Microagent {metadata.name} has SSE servers. Only stdio servers are currently supported.'
                    )

                if not metadata.mcp_tools.stdio_servers:
                    raise MicroagentValidationError(
                        f'Microagent {metadata.name} has MCP tools configuration but no stdio servers. '
                        'Only stdio servers are currently supported.'
                    )
        except Exception as e:
            # Provide more detailed error message for validation errors
            error_msg = f'Error validating microagent metadata in {path.name}: {str(e)}'
            if 'type' in metadata_dict and metadata_dict['type'] not in [
                t.value for t in MicroagentType
            ]:
                valid_types = ', '.join([f'"{t.value}"' for t in MicroagentType])
                error_msg += f'. Invalid "type" value: "{metadata_dict["type"]}". Valid types are: {valid_types}'
            raise MicroagentValidationError(error_msg) from e

        # Create appropriate subclass based on type
        subclass_map = {
            MicroagentType.KNOWLEDGE: KnowledgeMicroagent,
            MicroagentType.REPO_KNOWLEDGE: RepoMicroagent,
            MicroagentType.TASK: TaskMicroagent,
        }

        # Infer the agent type:
        # 1. If inputs exist -> TASK
        # 2. If triggers exist -> KNOWLEDGE
        # 3. Else (no triggers) -> REPO (always active)
        inferred_type: MicroagentType
        if metadata.inputs:
            inferred_type = MicroagentType.TASK
            # Add a trigger for the agent name if not already present
            trigger = f'/{metadata.name}'
            if not metadata.triggers or trigger not in metadata.triggers:
                if not metadata.triggers:
                    metadata.triggers = [trigger]
                else:
                    metadata.triggers.append(trigger)
        elif metadata.triggers:
            inferred_type = MicroagentType.KNOWLEDGE
        else:
            # No triggers, default to REPO
            # This handles cases where 'type' might be missing or defaulted by Pydantic
            inferred_type = MicroagentType.REPO_KNOWLEDGE

        if inferred_type not in subclass_map:
            # This should theoretically not happen with the logic above
            raise ValueError(f'Could not determine microagent type for: {path}')

        # Use derived_name if available (from relative path), otherwise fallback to metadata.name
        agent_name = derived_name if derived_name is not None else metadata.name

        agent_class = subclass_map[inferred_type]
        return agent_class(
            name=agent_name,
            content=content,
            metadata=metadata,
            source=str(path),
            type=inferred_type,
        )


class KnowledgeMicroagent(BaseMicroagent):
    """
    知识微代理

    知识微代理提供通过关键词触发的专业知识，主要用于：
    - 编程语言最佳实践
    - 框架使用指南
    - 常见模式和解决方案
    - 工具使用技巧

    知识微代理在对话中检测到特定关键词时自动激活，
    为AI代理提供相关的专业知识和指导。
    """

    def __init__(self, **data):
        """
        初始化知识微代理

        Args:
            **data: 微代理数据

        Raises:
            ValueError: 当微代理类型不正确时
        """
        super().__init__(**data)
        if self.type not in [MicroagentType.KNOWLEDGE, MicroagentType.TASK]:
            raise ValueError('KnowledgeMicroagent must have type KNOWLEDGE or TASK')

    def match_trigger(self, message: str) -> str | None:
        """
        在消息中匹配触发词

        检查消息是否包含任何触发词，返回第一个匹配的触发词。
        匹配过程不区分大小写。

        Args:
            message (str): 要检查的消息内容

        Returns:
            str | None: 匹配的触发词，如果没有匹配则返回None
        """
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                return trigger

        return None

    @property
    def triggers(self) -> list[str]:
        """
        获取触发词列表

        Returns:
            list[str]: 触发词列表
        """
        return self.metadata.triggers


class RepoMicroagent(BaseMicroagent):
    """
    仓库微代理

    专门用于仓库特定知识和指导的微代理。
    仓库微代理从仓库内的`.openhands/microagents/repo.md`文件加载，
    包含私有的、仓库特定的指令，在使用该仓库时自动加载。

    适用场景：
    - 仓库特定的指导原则
    - 团队实践和约定
    - 项目特定的工作流程
    - 自定义文档引用

    仓库微代理始终处于激活状态，为代理提供持续的上下文信息。
    """

    def __init__(self, **data):
        """
        初始化仓库微代理

        Args:
            **data: 微代理数据

        Raises:
            ValueError: 当微代理类型不正确时
        """
        super().__init__(**data)
        if self.type != MicroagentType.REPO_KNOWLEDGE:
            raise ValueError(
                f'RepoMicroagent initialized with incorrect type: {self.type}'
            )


class TaskMicroagent(KnowledgeMicroagent):
    """
    任务微代理

    任务微代理是知识微代理的特殊类型，需要用户输入。
    这些微代理通过特殊格式"/{agent_name}"触发，
    在继续执行之前会提示用户提供任何必需的输入。

    特点：
    - 支持变量替换（${variable_name}格式）
    - 自动生成用户输入提示
    - 动态参数收集和验证
    - 交互式任务执行
    """

    def __init__(self, **data):
        """
        初始化任务微代理

        Args:
            **data: 微代理数据

        Raises:
            ValueError: 当微代理类型不正确时
        """
        super().__init__(**data)
        if self.type != MicroagentType.TASK:
            raise ValueError(
                f'TaskMicroagent initialized with incorrect type: {self.type}'
            )

        # 添加缺失变量的提示
        self._append_missing_variables_prompt()

    def _append_missing_variables_prompt(self) -> None:
        """
        添加缺失变量的提示

        如果内容包含变量或定义了输入，则在内容末尾添加提示，
        指导代理在用户未提供变量时主动询问。
        """
        # 检查内容是否包含变量或定义了输入
        if not self.requires_user_input() and not self.metadata.inputs:
            return

        prompt = "\n\nIf the user didn't provide any of these variables, ask the user to provide them first before the agent can proceed with the task."
        self.content += prompt

    def extract_variables(self, content: str) -> list[str]:
        """
        从内容中提取变量

        提取格式为${variable_name}的变量。

        Args:
            content (str): 要分析的内容

        Returns:
            list[str]: 提取的变量名列表
        """
        pattern = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        matches = re.findall(pattern, content)
        return matches

    def requires_user_input(self) -> bool:
        """
        检查此微代理是否需要用户输入

        如果内容包含格式为${variable_name}的变量，则返回True。

        Returns:
            bool: 如果需要用户输入则返回True
        """
        # 检查内容是否包含任何变量
        variables = self.extract_variables(self.content)
        logger.debug(f'This microagent requires user input: {variables}')
        return len(variables) > 0

    @property
    def inputs(self) -> list[InputMetadata]:
        """
        获取此微代理的输入参数

        Returns:
            list[InputMetadata]: 输入参数列表
        """
        return self.metadata.inputs


def load_microagents_from_dir(
    microagent_dir: Union[str, Path],
) -> tuple[dict[str, RepoMicroagent], dict[str, KnowledgeMicroagent]]:
    """
    从指定目录加载所有微代理

    递归扫描微代理目录，加载所有.md文件作为微代理。
    注意：遗留的仓库指令不会在这里加载。

    Args:
        microagent_dir (Union[str, Path]): 微代理目录路径（如.openhands/microagents）

    Returns:
        tuple[dict[str, RepoMicroagent], dict[str, KnowledgeMicroagent]]:
            包含(仓库代理字典, 知识代理字典)的元组

    Raises:
        MicroagentValidationError: 当微代理验证失败时
        ValueError: 当加载过程中出现其他错误时

    Note:
        - 自动跳过README.md文件
        - 知识代理字典同时包含KnowledgeMicroagent和TaskMicroagent
        - 支持嵌套目录结构
    """
    if isinstance(microagent_dir, str):
        microagent_dir = Path(microagent_dir)

    repo_agents = {}
    knowledge_agents = {}

    # 从微代理目录加载所有代理
    logger.debug(f'Loading agents from {microagent_dir}')
    if microagent_dir.exists():
        for file in microagent_dir.rglob('*.md'):
            # 跳过README.md文件
            if file.name == 'README.md':
                continue
            try:
                agent = BaseMicroagent.load(file, microagent_dir)
                if isinstance(agent, RepoMicroagent):
                    repo_agents[agent.name] = agent
                elif isinstance(agent, KnowledgeMicroagent):
                    # KnowledgeMicroagent和TaskMicroagent都放入knowledge_agents
                    knowledge_agents[agent.name] = agent
            except MicroagentValidationError as e:
                # 对于验证错误，包含原始异常
                error_msg = f'Error loading microagent from {file}: {str(e)}'
                raise MicroagentValidationError(error_msg) from e
            except Exception as e:
                # 对于其他错误，用详细消息包装为ValueError
                error_msg = f'Error loading microagent from {file}: {str(e)}'
                raise ValueError(error_msg) from e

    logger.debug(
        f'Loaded {len(repo_agents) + len(knowledge_agents)} microagents: '
        f'{[*repo_agents.keys(), *knowledge_agents.keys()]}'
    )
    return repo_agents, knowledge_agents
