"""
OpenHands 本地文件存储实现

提供基于本地文件系统的存储实现，适用于单机部署和开发环境。
支持文件和目录的创建、读取、列表和删除操作。
"""

import os
import shutil

from openhands.core.logger import openhands_logger as logger
from openhands.storage.files import FileStore


class LocalFileStore(FileStore):
    """
    本地文件系统存储实现

    使用本地文件系统作为存储后端，提供文件的基本CRUD操作。
    适用于开发环境、测试环境和单机部署场景。

    特点：
    - 高性能：直接访问本地文件系统
    - 简单可靠：无需外部依赖
    - 易于调试：文件直接可见
    - 支持并发：文件系统级别的并发控制

    Attributes:
        root (str): 存储根目录的绝对路径
    """

    root: str  # 存储根目录

    def __init__(self, root: str):
        """
        初始化本地文件存储

        Args:
            root (str): 存储根目录路径，支持~符号表示用户主目录

        Note:
            如果根目录不存在，会自动创建
        """
        # 展开用户主目录符号
        if root.startswith('~'):
            root = os.path.expanduser(root)

        self.root = root
        # 确保根目录存在
        os.makedirs(self.root, exist_ok=True)

    def get_full_path(self, path: str) -> str:
        """
        获取文件的完整路径

        将相对路径转换为基于存储根目录的绝对路径。

        Args:
            path (str): 相对路径

        Returns:
            str: 完整的文件系统路径

        Note:
            自动处理以/开头的路径，将其视为相对路径
        """
        # 移除开头的/，确保是相对路径
        if path.startswith('/'):
            path = path[1:]
        return os.path.join(self.root, path)

    def write(self, path: str, contents: str | bytes) -> None:
        """
        写入文件内容

        支持文本和二进制内容的写入，自动创建必要的目录结构。

        Args:
            path (str): 文件路径
            contents (str | bytes): 要写入的内容

        Raises:
            IOError: 当写入失败时
            PermissionError: 当没有写入权限时
        """
        full_path = self.get_full_path(path)

        # 确保父目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 根据内容类型选择写入模式
        mode = 'w' if isinstance(contents, str) else 'wb'

        with open(full_path, mode) as f:
            f.write(contents)

    def read(self, path: str) -> str:
        """
        读取文件内容

        Args:
            path (str): 文件路径

        Returns:
            str: 文件内容（文本格式）

        Raises:
            FileNotFoundError: 当文件不存在时
            IOError: 当读取失败时
            PermissionError: 当没有读取权限时
        """
        full_path = self.get_full_path(path)
        with open(full_path, 'r') as f:
            return f.read()

    def list(self, path: str) -> list[str]:
        """
        列出目录内容

        返回指定目录下的所有文件和子目录，目录名以/结尾。

        Args:
            path (str): 目录路径

        Returns:
            list[str]: 文件和目录列表，目录名以/结尾

        Raises:
            FileNotFoundError: 当目录不存在时
            PermissionError: 当没有读取权限时
        """
        full_path = self.get_full_path(path)

        # 获取目录下的所有项目
        files = [os.path.join(path, f) for f in os.listdir(full_path)]

        # 为目录添加/后缀
        files = [f + '/' if os.path.isdir(self.get_full_path(f)) else f for f in files]

        return files

    def delete(self, path: str) -> None:
        """
        删除文件或目录

        支持删除单个文件或整个目录树。操作失败时会记录错误日志。

        Args:
            path (str): 要删除的文件或目录路径

        Note:
            - 如果路径不存在，操作会静默成功
            - 删除目录时会递归删除所有内容
            - 操作失败时会记录错误日志但不抛出异常
        """
        try:
            full_path = self.get_full_path(path)

            # 检查路径是否存在
            if not os.path.exists(full_path):
                logger.debug(f'Local path does not exist: {full_path}')
                return

            # 根据类型选择删除方法
            if os.path.isfile(full_path):
                os.remove(full_path)
                logger.debug(f'Removed local file: {full_path}')
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
                logger.debug(f'Removed local directory: {full_path}')

        except Exception as e:
            logger.error(f'Error clearing local file store: {str(e)}')
