"""
OpenHands 内存文件存储实现

提供基于内存的文件存储实现，主要用于测试和临时数据存储。
所有数据存储在内存中，进程重启后数据会丢失。
"""

import os

from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


class InMemoryFileStore(FileStore):
    """
    内存文件存储实现

    将所有文件数据存储在内存的字典中，提供快速的读写访问。
    主要用于单元测试、集成测试和临时数据存储场景。

    特点：
    - 极高性能：所有操作都在内存中进行
    - 零依赖：不需要文件系统或外部服务
    - 易于测试：状态完全可控
    - 数据易失：进程重启后数据丢失

    Attributes:
        files (dict[str, str]): 存储文件路径到内容的映射
    """

    files: dict[str, str]  # 文件路径到内容的映射

    def __init__(self, files: dict[str, str] | None = None) -> None:
        """
        初始化内存文件存储

        Args:
            files (dict[str, str] | None): 初始文件数据，可选
                键为文件路径，值为文件内容
        """
        self.files = {}
        if files is not None:
            self.files = files

    def write(self, path: str, contents: str | bytes) -> None:
        """
        写入文件内容到内存

        Args:
            path (str): 文件路径
            contents (str | bytes): 文件内容，字节内容会自动转换为UTF-8字符串

        Note:
            二进制内容会被解码为UTF-8字符串存储
        """
        # 将字节内容转换为字符串
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')
        self.files[path] = contents

    def read(self, path: str) -> str:
        """
        从内存读取文件内容

        Args:
            path (str): 文件路径

        Returns:
            str: 文件内容

        Raises:
            FileNotFoundError: 当文件不存在时
        """
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def list(self, path: str) -> list[str]:
        """
        列出目录内容

        模拟文件系统的目录结构，返回指定路径下的文件和子目录。

        Args:
            path (str): 目录路径

        Returns:
            list[str]: 文件和目录列表，目录以/结尾

        Note:
            通过分析文件路径来模拟目录结构
        """
        files = []

        # 遍历所有文件，找出属于指定路径的项目
        for file in self.files:
            if not file.startswith(path):
                continue

            # 获取相对于指定路径的后缀
            suffix = file.removeprefix(path)
            parts = suffix.split('/')

            # 移除空的第一部分（如果路径以/开头）
            if parts[0] == '':
                parts.pop(0)

            # 如果只有一个部分，说明是直接子文件
            if len(parts) == 1:
                files.append(file)
            else:
                # 多个部分说明是子目录，添加目录路径
                dir_path = os.path.join(path, parts[0])
                if not dir_path.endswith('/'):
                    dir_path += '/'
                if dir_path not in files:
                    files.append(dir_path)

        return files

    def delete(self, path: str) -> None:
        """
        删除文件或目录

        删除指定路径的文件，或删除以指定路径为前缀的所有文件（模拟目录删除）。

        Args:
            path (str): 要删除的文件或目录路径

        Note:
            - 支持删除单个文件或整个目录树
            - 操作失败时记录错误日志但不抛出异常
        """
        try:
            # 找出所有以指定路径开头的键（文件或目录下的所有文件）
            keys_to_delete = [key for key in self.files.keys() if key.startswith(path)]

            # 删除所有匹配的文件
            for key in keys_to_delete:
                del self.files[key]

            logger.debug(f'Cleared in-memory file store: {path}')
        except Exception as e:
            logger.error(f'Error clearing in-memory file store: {str(e)}')
