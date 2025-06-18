"""
OpenHands 命令执行观察模块

定义了命令执行结果的观察类，包括：
- CmdOutputMetadata: 命令输出元数据，包含退出码、进程ID等信息
- CmdOutputObservation: 命令输出观察，包含命令执行的完整结果
- IPythonRunCellObservation: IPython代码执行观察

这些观察类用于捕获和处理命令执行的结果。
"""

import json
import re
import traceback
from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation

# PS1提示符的开始和结束标记，用于捕获命令元数据
CMD_OUTPUT_PS1_BEGIN = '\n###PS1JSON###\n'
CMD_OUTPUT_PS1_END = '\n###PS1END###'
CMD_OUTPUT_METADATA_PS1_REGEX = re.compile(
    f'^{CMD_OUTPUT_PS1_BEGIN.strip()}(.*?){CMD_OUTPUT_PS1_END.strip()}',
    re.DOTALL | re.MULTILINE,
)


class CmdOutputMetadata(BaseModel):
    """
    命令输出元数据

    从PS1提示符中捕获的额外元数据，包含命令执行的环境信息。

    Attributes:
        exit_code (int): 命令退出码，-1表示未知
        pid (int): 进程ID，-1表示未知
        username (str | None): 用户名
        hostname (str | None): 主机名
        working_dir (str | None): 工作目录
        py_interpreter_path (str | None): Python解释器路径
        prefix (str): 添加到命令输出前的前缀
        suffix (str): 添加到命令输出后的后缀
    """

    exit_code: int = -1  # 命令退出码
    pid: int = -1  # 进程ID
    username: str | None = None  # 用户名
    hostname: str | None = None  # 主机名
    working_dir: str | None = None  # 工作目录
    py_interpreter_path: str | None = None  # Python解释器路径
    prefix: str = ''  # 输出前缀
    suffix: str = ''  # 输出后缀

    @classmethod
    def to_ps1_prompt(cls) -> str:
        """Convert the required metadata into a PS1 prompt."""
        prompt = CMD_OUTPUT_PS1_BEGIN
        json_str = json.dumps(
            {
                'pid': '$!',
                'exit_code': '$?',
                'username': r'\u',
                'hostname': r'\h',
                'working_dir': r'$(pwd)',
                'py_interpreter_path': r'$(which python 2>/dev/null || echo "")',
            },
            indent=2,
        )
        # Make sure we escape double quotes in the JSON string
        # So that PS1 will keep them as part of the output
        prompt += json_str.replace('"', r'\"')
        prompt += CMD_OUTPUT_PS1_END + '\n'  # Ensure there's a newline at the end
        return prompt

    @classmethod
    def matches_ps1_metadata(cls, string: str) -> list[re.Match[str]]:
        matches = []
        for match in CMD_OUTPUT_METADATA_PS1_REGEX.finditer(string):
            try:
                json.loads(match.group(1).strip())  # Try to parse as JSON
                matches.append(match)
            except json.JSONDecodeError:
                logger.warning(
                    f'Failed to parse PS1 metadata: {match.group(1)}. Skipping.'
                    + traceback.format_exc()
                )
                continue  # Skip if not valid JSON
        return matches

    @classmethod
    def from_ps1_match(cls, match: re.Match[str]) -> Self:
        """Extract the required metadata from a PS1 prompt."""
        metadata = json.loads(match.group(1))
        # Create a copy of metadata to avoid modifying the original
        processed = metadata.copy()
        # Convert numeric fields
        if 'pid' in metadata:
            try:
                processed['pid'] = int(float(str(metadata['pid'])))
            except (ValueError, TypeError):
                processed['pid'] = -1
        if 'exit_code' in metadata:
            try:
                processed['exit_code'] = int(float(str(metadata['exit_code'])))
            except (ValueError, TypeError):
                logger.warning(
                    f'Failed to parse exit code: {metadata["exit_code"]}. Setting to -1.'
                )
                processed['exit_code'] = -1
        return cls(**processed)


@dataclass
class CmdOutputObservation(Observation):
    """This data class represents the output of a command."""

    command: str
    observation: str = ObservationType.RUN
    # Additional metadata captured from PS1
    metadata: CmdOutputMetadata = field(default_factory=CmdOutputMetadata)
    # Whether the command output should be hidden from the user
    hidden: bool = False

    def __init__(
        self,
        content: str,
        command: str,
        observation: str = ObservationType.RUN,
        metadata: dict[str, Any] | CmdOutputMetadata | None = None,
        hidden: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(content)
        self.command = command
        self.observation = observation
        self.hidden = hidden
        if isinstance(metadata, dict):
            self.metadata = CmdOutputMetadata(**metadata)
        else:
            self.metadata = metadata or CmdOutputMetadata()

        # Handle legacy attribute
        if 'exit_code' in kwargs:
            self.metadata.exit_code = kwargs['exit_code']
        if 'command_id' in kwargs:
            self.metadata.pid = kwargs['command_id']

    @property
    def command_id(self) -> int:
        return self.metadata.pid

    @property
    def exit_code(self) -> int:
        return self.metadata.exit_code

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'

    @property
    def success(self) -> bool:
        return not self.error

    def __str__(self) -> str:
        return (
            f'**CmdOutputObservation (source={self.source}, exit code={self.exit_code}, '
            f'metadata={json.dumps(self.metadata.model_dump(), indent=2)})**\n'
            '--BEGIN AGENT OBSERVATION--\n'
            f'{self.to_agent_observation()}\n'
            '--END AGENT OBSERVATION--'
        )

    def to_agent_observation(self) -> str:
        ret = f'{self.metadata.prefix}{self.content}{self.metadata.suffix}'
        if self.metadata.working_dir:
            ret += f'\n[Current working directory: {self.metadata.working_dir}]'
        if self.metadata.py_interpreter_path:
            ret += f'\n[Python interpreter: {self.metadata.py_interpreter_path}]'
        if self.metadata.exit_code != -1:
            ret += f'\n[Command finished with exit code {self.metadata.exit_code}]'
        return ret


@dataclass
class IPythonRunCellObservation(Observation):
    """This data class represents the output of a IPythonRunCellAction."""

    code: str
    observation: str = ObservationType.RUN_IPYTHON
    image_urls: list[str] | None = None

    @property
    def error(self) -> bool:
        return False  # IPython cells do not return exit codes

    @property
    def message(self) -> str:
        return 'Code executed in IPython cell.'

    @property
    def success(self) -> bool:
        return True  # IPython cells are always considered successful

    def __str__(self) -> str:
        result = f'**IPythonRunCellObservation**\n{self.content}'
        if self.image_urls:
            result += f'\nImages: {len(self.image_urls)}'
        return result
