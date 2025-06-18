"""
OpenHands 对话存储抽象基类

定义了对话元数据存储的标准接口，支持自定义存储实现。
应用程序可以通过继承此类来实现自定义的对话存储逻辑。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_metadata_result_set import (
    ConversationMetadataResultSet,
)
from openhands.utils.async_utils import wait_all


class ConversationStore(ABC):
    """
    对话存储抽象基类

    这是OpenHands中的一个扩展点，允许应用程序自定义对话元数据的存储方式。
    应用程序可以通过以下方式替换自己的实现：
    1. 创建一个继承自ConversationStore的类
    2. 实现所有必需的方法
    3. 将server_config.conversation_store_class设置为该类的完全限定名

    该类通过openhands.server.shared.py中的get_impl()进行实例化。

    根据环境的不同，实现可能支持也可能不支持多用户。

    主要功能：
    - 对话元数据的CRUD操作
    - 支持分页查询和过滤
    - 用户级别的数据隔离
    - 异步操作支持
    """

    @abstractmethod
    async def save_metadata(self, metadata: ConversationMetadata) -> None:
        """Store conversation metadata."""

    @abstractmethod
    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        """Load conversation metadata."""

    async def validate_metadata(self, conversation_id: str, user_id: str) -> bool:
        """Validate that conversation belongs to the current user."""
        metadata = await self.get_metadata(conversation_id)
        if not metadata.user_id or metadata.user_id != user_id:
            return False
        else:
            return True

    @abstractmethod
    async def delete_metadata(self, conversation_id: str) -> None:
        """Delete conversation metadata."""

    @abstractmethod
    async def exists(self, conversation_id: str) -> bool:
        """Check if conversation exists."""

    @abstractmethod
    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
    ) -> ConversationMetadataResultSet:
        """Search conversations."""

    async def get_all_metadata(
        self, conversation_ids: Iterable[str]
    ) -> list[ConversationMetadata]:
        """Get metadata for multiple conversations in parallel."""
        return await wait_all([self.get_metadata(cid) for cid in conversation_ids])

    @classmethod
    @abstractmethod
    async def get_instance(
        cls, config: OpenHandsConfig, user_id: str | None
    ) -> ConversationStore:
        """Get a store for the user represented by the token given."""
