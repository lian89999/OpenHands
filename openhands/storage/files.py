"""
OpenHands 文件存储抽象基类

定义了文件存储的统一接口，所有具体的存储实现都必须继承此类。
这个抽象层使得OpenHands可以支持多种存储后端，而不需要修改上层代码。
"""

from abc import abstractmethod


class FileStore:
    """
    文件存储抽象基类

    定义了文件存储操作的标准接口，包括读取、写入、列表和删除操作。
    所有具体的存储实现（本地、S3、GCS等）都必须实现这些方法。

    这个设计遵循了策略模式，允许在运行时切换不同的存储后端。
    """

    @abstractmethod
    def write(self, path: str, contents: str | bytes) -> None:
        """
        写入文件内容

        Args:
            path (str): 文件路径，相对于存储根目录
            contents (str | bytes): 要写入的内容，支持文本和二进制数据

        Raises:
            IOError: 当写入操作失败时
            PermissionError: 当没有写入权限时
        """
        pass

    @abstractmethod
    def read(self, path: str) -> str:
        """
        读取文件内容

        Args:
            path (str): 文件路径，相对于存储根目录

        Returns:
            str: 文件内容（文本格式）

        Raises:
            FileNotFoundError: 当文件不存在时
            IOError: 当读取操作失败时
            PermissionError: 当没有读取权限时
        """
        pass

    @abstractmethod
    def list(self, path: str) -> list[str]:
        """
        列出目录下的文件和子目录

        Args:
            path (str): 目录路径，相对于存储根目录

        Returns:
            list[str]: 文件和目录名称列表

        Raises:
            FileNotFoundError: 当目录不存在时
            IOError: 当列表操作失败时
            PermissionError: 当没有读取权限时
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """
        删除文件或目录

        Args:
            path (str): 要删除的文件或目录路径，相对于存储根目录

        Raises:
            FileNotFoundError: 当文件或目录不存在时
            IOError: 当删除操作失败时
            PermissionError: 当没有删除权限时
        """
        pass
