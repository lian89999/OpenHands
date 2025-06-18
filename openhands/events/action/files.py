"""
OpenHands 文件操作动作模块

定义了文件相关的动作类，包括：
- FileReadAction: 文件读取动作
- FileWriteAction: 文件写入动作
- FileEditAction: 文件编辑动作

这些动作允许代理对文件系统进行操作。
"""

from dataclasses import dataclass
from typing import ClassVar

from openhands.core.schema import ActionType
from openhands.events.action.action import Action, ActionSecurityRisk
from openhands.events.event import FileEditSource, FileReadSource


@dataclass
class FileReadAction(Action):
    """
    文件读取动作

    从指定路径读取文件内容。可以通过start和end参数指定读取的行范围。
    默认读取整个文件（0:-1）。

    Attributes:
        path (str): 要读取的文件路径
        start (int): 开始行号（从0开始），默认为0
        end (int): 结束行号，默认为-1（文件末尾）
        thought (str): 执行此动作的思考过程
        action (str): 动作类型，固定为ActionType.READ
        runnable (ClassVar[bool]): 标识此动作可以执行
        security_risk (ActionSecurityRisk | None): 安全风险等级
        impl_source (FileReadSource): 实现来源
        view_range (list[int] | None): 视图范围，仅在OH_ACI模式下使用
    """

    path: str  # 文件路径
    start: int = 0  # 开始行号
    end: int = -1  # 结束行号
    thought: str = ''  # 思考过程
    action: str = ActionType.READ  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    security_risk: ActionSecurityRisk | None = None  # 安全风险
    impl_source: FileReadSource = FileReadSource.DEFAULT  # 实现来源
    view_range: list[int] | None = None  # 视图范围（仅OH_ACI模式）

    @property
    def message(self) -> str:
        """返回动作的描述消息"""
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(Action):
    """
    文件写入动作

    向指定路径写入文件内容。可以通过start和end参数指定写入的行范围。
    默认写入整个文件（0:-1）。

    Attributes:
        path (str): 要写入的文件路径
        content (str): 要写入的内容
        start (int): 开始行号（从0开始），默认为0
        end (int): 结束行号，默认为-1（文件末尾）
        thought (str): 执行此动作的思考过程
        action (str): 动作类型，固定为ActionType.WRITE
        runnable (ClassVar[bool]): 标识此动作可以执行
        security_risk (ActionSecurityRisk | None): 安全风险等级
    """

    path: str  # 文件路径
    content: str  # 文件内容
    start: int = 0  # 开始行号
    end: int = -1  # 结束行号
    thought: str = ''  # 思考过程
    action: str = ActionType.WRITE  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    security_risk: ActionSecurityRisk | None = None  # 安全风险

    @property
    def message(self) -> str:
        """返回动作的描述消息"""
        return f'Writing file: {self.path}'

    def __repr__(self) -> str:
        """返回动作的详细字符串表示"""
        return (
            f'**FileWriteAction**\n'
            f'Path: {self.path}\n'
            f'Range: [L{self.start}:L{self.end}]\n'
            f'Thought: {self.thought}\n'
            f'Content:\n```\n{self.content}\n```\n'
        )


@dataclass
class FileEditAction(Action):
    """
    文件编辑动作

    使用各种命令编辑文件，包括查看、创建、字符串替换、插入和撤销编辑。

    此类支持两种主要操作模式：
    1. 基于LLM的编辑 (impl_source = FileEditSource.LLM_BASED_EDIT)
    2. 基于ACI的编辑 (impl_source = FileEditSource.OH_ACI)

    Attributes:
        path (str): 要编辑的文件路径，适用于LLM和OH_ACI两种模式

        OH_ACI专用参数：
            command (str): 要执行的编辑命令 (view, create, str_replace, insert, undo_edit, write)
            file_text (str): 要创建的文件内容（用于'create'命令）
            old_str (str): 要被替换的字符串（用于'str_replace'命令）
            new_str (str): 替换old_str的新字符串（用于'str_replace'和'insert'命令）
            insert_line (int): 插入new_str的行号（用于'insert'命令）

        基于LLM的编辑参数：
            content (str): 要写入或编辑的文件内容
            start (int): 编辑的起始行（从1开始，包含），默认为1
            end (int): 编辑的结束行（从1开始，包含），默认为-1（文件末尾）

        共享参数：
            thought (str): 编辑动作背后的推理过程
            action (str): 执行的动作类型（始终为ActionType.EDIT）
            runnable (bool): 指示动作是否可以执行（始终为True）
            security_risk (ActionSecurityRisk | None): 与动作相关的安全风险
            impl_source (FileEditSource): 实现来源（LLM_BASED_EDIT或OH_ACI）

    使用方法：
        - 基于LLM的编辑：使用path、content、start和end属性
        - 基于ACI的编辑：使用path、command和特定命令的相应属性

    注意：
        - 在基于LLM的编辑中，如果start设置为-1，内容将追加到文件末尾
        - 'write'命令的行为类似于基于LLM的编辑，使用content、start和end属性
    """

    path: str  # 文件路径

    # OH_ACI专用参数
    command: str = ''  # 编辑命令
    file_text: str | None = None  # 文件文本内容
    old_str: str | None = None  # 要替换的旧字符串
    new_str: str | None = None  # 新字符串
    insert_line: int | None = None  # 插入行号

    # 基于LLM的编辑参数
    content: str = ''  # 文件内容
    start: int = 1  # 起始行号
    end: int = -1  # 结束行号

    # 共享参数
    thought: str = ''  # 思考过程
    action: str = ActionType.EDIT  # 动作类型
    runnable: ClassVar[bool] = True  # 可执行标志
    security_risk: ActionSecurityRisk | None = None  # 安全风险
    impl_source: FileEditSource = FileEditSource.OH_ACI  # 实现来源

    def __repr__(self) -> str:
        """
        返回文件编辑动作的详细字符串表示

        根据不同的实现来源（LLM或OH_ACI）和命令类型，
        返回相应的格式化字符串。

        Returns:
            str: 格式化的动作描述字符串
        """
        ret = '**FileEditAction**\n'
        ret += f'Path: [{self.path}]\n'
        ret += f'Thought: {self.thought}\n'

        if self.impl_source == FileEditSource.LLM_BASED_EDIT:
            # 基于LLM的编辑模式
            ret += f'Range: [L{self.start}:L{self.end}]\n'
            ret += f'Content:\n```\n{self.content}\n```\n'
        else:  # OH_ACI模式
            ret += f'Command: {self.command}\n'
            if self.command == 'create':
                # 创建文件命令
                ret += f'Created File with Text:\n```\n{self.file_text}\n```\n'
            elif self.command == 'str_replace':
                # 字符串替换命令
                ret += f'Old String: ```\n{self.old_str}\n```\n'
                ret += f'New String: ```\n{self.new_str}\n```\n'
            elif self.command == 'insert':
                # 插入命令
                ret += f'Insert Line: {self.insert_line}\n'
                ret += f'New String: ```\n{self.new_str}\n```\n'
            elif self.command == 'undo_edit':
                # 撤销编辑命令
                ret += 'Undo Edit\n'
            # 忽略"view"命令，因为它会被映射到FileReadAction
        return ret
