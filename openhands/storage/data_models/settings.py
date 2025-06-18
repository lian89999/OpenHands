"""
OpenHands 设置数据模型

定义了OpenHands会话的持久化设置，包括语言、代理、LLM配置、安全设置等。
使用Pydantic进行数据验证和序列化，支持敏感信息的安全处理。
"""

from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.utils import load_openhands_config
from openhands.storage.data_models.user_secrets import UserSecrets


class Settings(BaseModel):
    """
    OpenHands会话持久化设置

    存储用户的个性化配置和偏好设置，包括：
    - 界面语言和代理选择
    - LLM模型配置和API密钥
    - 安全和确认模式设置
    - 运行时和沙箱配置
    - 用户通知和分析偏好

    所有设置都支持序列化到存储后端，并在会话间保持持久化。
    敏感信息（如API密钥）使用SecretStr类型进行安全处理。
    """

    # 基础设置
    language: str | None = None  # 界面语言（如'en', 'zh'）
    agent: str | None = None  # 默认代理类型
    max_iterations: int | None = None  # 最大迭代次数

    # 安全设置
    security_analyzer: str | None = None  # 安全分析器类型
    confirmation_mode: bool | None = None  # 确认模式开关

    # LLM配置
    llm_model: str | None = None  # LLM模型名称
    llm_api_key: SecretStr | None = None  # LLM API密钥（加密存储）
    llm_base_url: str | None = None  # LLM API基础URL

    # 运行时配置
    remote_runtime_resource_factor: int | None = None  # 远程运行时资源因子
    sandbox_base_container_image: str | None = None  # 沙箱基础容器镜像
    sandbox_runtime_container_image: str | None = None  # 沙箱运行时容器镜像

    # 密钥存储（计划移除）
    secrets_store: UserSecrets = Field(default_factory=UserSecrets, frozen=True)

    # 功能开关
    enable_default_condenser: bool = True  # 启用默认压缩器
    enable_sound_notifications: bool = False  # 启用声音通知
    enable_proactive_conversation_starters: bool = True  # 启用主动对话启动器

    # 用户偏好
    user_consents_to_analytics: bool | None = None  # 用户同意分析
    email: str | None = None  # 用户邮箱
    email_verified: bool | None = None  # 邮箱验证状态

    # 扩展配置
    mcp_config: MCPConfig | None = None  # MCP配置
    search_api_key: SecretStr | None = None  # 搜索API密钥

    model_config = {
        'validate_assignment': True,  # 启用赋值验证
    }

    @field_serializer('llm_api_key', 'search_api_key')
    def api_key_serializer(self, api_key: SecretStr | None, info: SerializationInfo):
        """
        API密钥自定义序列化器

        默认情况下API密钥会被序列化为********，保护敏感信息。
        如果需要序列化实际的API密钥值，需要在序列化上下文中设置expose_secrets=True。

        Args:
            api_key (SecretStr | None): 要序列化的API密钥
            info (SerializationInfo): 序列化信息和上下文

        Returns:
            str | None: 序列化后的密钥值或掩码
        """
        if api_key is None:
            return None

        context = info.context
        # 如果上下文中设置了expose_secrets=True，则返回实际密钥值
        if context and context.get('expose_secrets', False):
            return api_key.get_secret_value()

        # 否则返回默认的掩码形式
        return pydantic_encoder(api_key)

    @model_validator(mode='before')
    @classmethod
    def convert_provider_tokens(cls, data: dict | object) -> dict | object:
        """
        提供商令牌格式转换验证器

        将JSON格式的提供商令牌转换为UserSecrets格式，
        确保向后兼容性和数据格式的一致性。

        Args:
            data (dict | object): 输入数据

        Returns:
            dict | object: 转换后的数据
        """
        if not isinstance(data, dict):
            return data

        secrets_store = data.get('secrets_store')
        if not isinstance(secrets_store, dict):
            return data

        # 提取自定义密钥和提供商令牌
        custom_secrets = secrets_store.get('custom_secrets')
        tokens = secrets_store.get('provider_tokens')

        # 创建新的密钥存储对象
        secret_store = UserSecrets(provider_tokens={}, custom_secrets={})

        # 转换提供商令牌
        if isinstance(tokens, dict):
            converted_store = UserSecrets(provider_tokens=tokens)
            secret_store = secret_store.model_copy(
                update={'provider_tokens': converted_store.provider_tokens}
            )
        else:
            secret_store.model_copy(update={'provider_tokens': tokens})

        # 转换自定义密钥
        if isinstance(custom_secrets, dict):
            converted_store = UserSecrets(custom_secrets=custom_secrets)
            secret_store = secret_store.model_copy(
                update={'custom_secrets': converted_store.custom_secrets}
            )
        else:
            secret_store = secret_store.model_copy(
                update={'custom_secrets': custom_secrets}
            )

        data['secret_store'] = secret_store
        return data

    @field_serializer('secrets_store')
    def secrets_store_serializer(self, secrets: UserSecrets, info: SerializationInfo):
        """
        密钥存储自定义序列化器

        出于安全考虑，强制使密钥存储失效，返回空的提供商令牌。
        这确保了敏感的密钥信息不会被意外序列化到持久化存储中。

        Args:
            secrets (UserSecrets): 密钥存储对象
            info (SerializationInfo): 序列化信息

        Returns:
            dict: 空的提供商令牌字典
        """
        # 强制使密钥存储失效，返回空字典
        return {'provider_tokens': {}}

    @staticmethod
    def from_config() -> Settings | None:
        """
        从应用配置创建设置对象

        读取OpenHands的应用配置文件，并将其转换为Settings对象。
        如果没有设置API密钥，则返回None表示没有合理的默认配置。

        Returns:
            Settings | None: 从配置创建的设置对象，如果无法创建则返回None

        Note:
            这个方法主要用于从配置文件初始化默认设置
        """
        # 加载应用配置
        app_config = load_openhands_config()
        llm_config: LLMConfig = app_config.get_llm_config()

        # 如果没有设置API密钥，认为没有合理的默认配置
        if llm_config.api_key is None:
            return None

        security = app_config.security

        # 获取MCP配置（如果可用）
        mcp_config = None
        if hasattr(app_config, 'mcp'):
            mcp_config = app_config.mcp

        # 创建设置对象
        settings = Settings(
            language='en',  # 默认语言
            agent=app_config.default_agent,  # 默认代理
            max_iterations=app_config.max_iterations,  # 最大迭代次数
            security_analyzer=security.security_analyzer,  # 安全分析器
            confirmation_mode=security.confirmation_mode,  # 确认模式
            llm_model=llm_config.model,  # LLM模型
            llm_api_key=llm_config.api_key,  # LLM API密钥
            llm_base_url=llm_config.base_url,  # LLM基础URL
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,  # 远程运行时资源因子
            mcp_config=mcp_config,  # MCP配置
            search_api_key=app_config.search_api_key,  # 搜索API密钥
        )
        return settings
