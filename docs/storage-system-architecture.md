# OpenHands 存储系统架构文档

## 概述

OpenHands的存储系统是一个高度模块化和可扩展的数据持久化解决方案，采用分层架构设计，支持多种存储后端。本文档详细介绍存储系统的技术架构、核心组件、设计模式和技术栈。

## 核心架构

### 1. 分层架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application Layer)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Conversation│  │  Settings   │  │   Secrets   │         │
│  │   Manager   │  │   Manager   │  │   Manager   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   抽象层 (Abstraction Layer)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Conversation │  │  Settings   │  │   Secrets   │         │
│  │    Store    │  │    Store    │  │    Store    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   存储层 (Storage Layer)                     │
│                    ┌─────────────┐                          │
│                    │  FileStore  │                          │
│                    │ (Abstract)  │                          │
│                    └─────────────┘                          │
│                          │                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    Local    │  │     S3      │  │   Memory    │         │
│  │ FileStore   │  │ FileStore   │  │ FileStore   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │Google Cloud │  │  WebHook    │                          │
│  │ FileStore   │  │ FileStore   │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 2. 技术栈组成

#### 核心技术
- **Python 3.12+**: 主要开发语言
- **Pydantic**: 数据验证和序列化
- **asyncio**: 异步I/O支持
- **httpx**: HTTP客户端（WebHook支持）

#### 存储后端
- **本地文件系统**: 直接文件操作
- **Amazon S3**: 对象存储服务
- **Google Cloud Storage**: 云存储服务
- **内存存储**: 测试和临时存储

#### 数据格式
- **JSON**: 主要序列化格式
- **SecretStr**: 敏感信息加密
- **Base64**: 二进制数据编码

## 核心组件

### 1. 文件存储抽象层

#### FileStore 基类

```python
class FileStore:
    """文件存储抽象基类"""

    @abstractmethod
    def write(self, path: str, contents: str | bytes) -> None:
        """写入文件内容"""
        pass

    @abstractmethod
    def read(self, path: str) -> str:
        """读取文件内容"""
        pass

    @abstractmethod
    def list(self, path: str) -> list[str]:
        """列出目录内容"""
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        """删除文件或目录"""
        pass
```

#### 设计优势
- **统一接口**: 所有存储后端使用相同的API
- **策略模式**: 运行时可切换存储后端
- **易于扩展**: 新增存储后端只需实现接口
- **测试友好**: 可使用内存存储进行测试

### 2. 存储后端实现

#### 2.1 本地文件存储 (LocalFileStore)

```python
class LocalFileStore(FileStore):
    """本地文件系统存储实现"""

    def __init__(self, root: str):
        self.root = os.path.expanduser(root)
        os.makedirs(self.root, exist_ok=True)

    def write(self, path: str, contents: str | bytes) -> None:
        full_path = self.get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        mode = 'w' if isinstance(contents, str) else 'wb'
        with open(full_path, mode) as f:
            f.write(contents)
```

**特点**:
- 高性能本地访问
- 支持文本和二进制文件
- 自动创建目录结构
- 适用于单机部署

#### 2.2 S3对象存储 (S3FileStore)

```python
class S3FileStore(FileStore):
    """Amazon S3存储实现"""

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')

    def write(self, path: str, contents: str | bytes) -> None:
        if isinstance(contents, str):
            contents = contents.encode('utf-8')
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=contents
        )
```

**特点**:
- 云端对象存储
- 高可用性和持久性
- 支持大规模数据
- 适用于分布式部署

#### 2.3 内存存储 (InMemoryFileStore)

```python
class InMemoryFileStore(FileStore):
    """内存文件存储实现"""

    def __init__(self, files: dict[str, str] | None = None):
        self.files = files or {}

    def write(self, path: str, contents: str | bytes) -> None:
        if isinstance(contents, bytes):
            contents = contents.decode('utf-8')
        self.files[path] = contents
```

**特点**:
- 极高性能
- 零外部依赖
- 易于测试
- 数据易失性

#### 2.4 WebHook装饰器 (WebHookFileStore)

```python
class WebHookFileStore(FileStore):
    """WebHook装饰器存储"""

    def __init__(self, store: FileStore, webhook_url: str, client: httpx.Client):
        self.store = store
        self.webhook_url = webhook_url
        self.client = client

    def write(self, path: str, contents: str | bytes) -> None:
        # 执行实际写入
        self.store.write(path, contents)
        # 发送WebHook通知
        self.send_webhook_notification('write', path)
```

**特点**:
- 装饰器模式
- 操作通知机制
- 支持任意存储后端
- 可配置HTTP客户端

### 3. 数据模型层

#### 3.1 设置模型 (Settings)

```python
class Settings(BaseModel):
    """OpenHands会话持久化设置"""

    # 基础设置
    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None

    # 安全设置
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None

    # LLM配置
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
```

**特点**:
- Pydantic数据验证
- 敏感信息保护
- 自定义序列化器
- 配置文件集成

#### 3.2 对话元数据 (ConversationMetadata)

```python
class ConversationMetadata(BaseModel):
    """对话元数据模型"""

    conversation_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    status: ConversationStatus
    github_user_id: str | None = None
    selected_repository: str | None = None
```

**特点**:
- 时间戳管理
- 状态跟踪
- 用户关联
- 仓库绑定

#### 3.3 用户密钥 (UserSecrets)

```python
class UserSecrets(BaseModel):
    """用户密钥存储模型"""

    provider_tokens: dict[str, SecretStr] = Field(default_factory=dict)
    custom_secrets: dict[str, SecretStr] = Field(default_factory=dict)

    @field_serializer('provider_tokens', 'custom_secrets')
    def serialize_secrets(self, secrets: dict[str, SecretStr]):
        return {k: v.get_secret_value() for k, v in secrets.items()}
```

**特点**:
- 多提供商支持
- 自定义密钥
- 安全序列化
- 类型安全

### 4. 存储管理器

#### 4.1 对话存储管理器

```python
class ConversationStore:
    """对话存储管理器"""

    def __init__(self, file_store: FileStore):
        self.file_store = file_store

    async def save_conversation(self, conversation_id: str, metadata: ConversationMetadata):
        """保存对话元数据"""
        path = f"conversations/{conversation_id}/metadata.json"
        content = metadata.model_dump_json()
        self.file_store.write(path, content)

    async def load_conversation(self, conversation_id: str) -> ConversationMetadata:
        """加载对话元数据"""
        path = f"conversations/{conversation_id}/metadata.json"
        content = self.file_store.read(path)
        return ConversationMetadata.model_validate_json(content)
```

#### 4.2 设置存储管理器

```python
class SettingsStore:
    """设置存储管理器"""

    def __init__(self, file_store: FileStore):
        self.file_store = file_store

    async def save_settings(self, user_id: str, settings: Settings):
        """保存用户设置"""
        path = f"users/{user_id}/settings.json"
        content = settings.model_dump_json()
        self.file_store.write(path, content)

    async def load_settings(self, user_id: str) -> Settings:
        """加载用户设置"""
        path = f"users/{user_id}/settings.json"
        content = self.file_store.read(path)
        return Settings.model_validate_json(content)
```

## 设计模式

### 1. 策略模式 (Strategy Pattern)

```python
class StorageStrategy:
    """存储策略接口"""

    def create_file_store(self, config: dict) -> FileStore:
        raise NotImplementedError

class LocalStorageStrategy(StorageStrategy):
    def create_file_store(self, config: dict) -> FileStore:
        return LocalFileStore(config['path'])

class S3StorageStrategy(StorageStrategy):
    def create_file_store(self, config: dict) -> FileStore:
        return S3FileStore(config['bucket'])

class StorageFactory:
    strategies = {
        'local': LocalStorageStrategy(),
        's3': S3StorageStrategy(),
        'gcs': GoogleCloudStorageStrategy(),
        'memory': MemoryStorageStrategy(),
    }

    @classmethod
    def create_store(cls, storage_type: str, config: dict) -> FileStore:
        strategy = cls.strategies[storage_type]
        return strategy.create_file_store(config)
```

### 2. 装饰器模式 (Decorator Pattern)

```python
class FileStoreDecorator(FileStore):
    """文件存储装饰器基类"""

    def __init__(self, store: FileStore):
        self.store = store

class CachingFileStore(FileStoreDecorator):
    """缓存装饰器"""

    def __init__(self, store: FileStore, cache_size: int = 1000):
        super().__init__(store)
        self.cache = LRUCache(cache_size)

    def read(self, path: str) -> str:
        if path in self.cache:
            return self.cache[path]
        content = self.store.read(path)
        self.cache[path] = content
        return content

class CompressionFileStore(FileStoreDecorator):
    """压缩装饰器"""

    def write(self, path: str, contents: str | bytes) -> None:
        if isinstance(contents, str):
            contents = contents.encode('utf-8')
        compressed = gzip.compress(contents)
        self.store.write(path + '.gz', compressed)
```

### 3. 工厂模式 (Factory Pattern)

```python
def get_file_store(
    file_store_type: str,
    file_store_path: str | None = None,
    file_store_web_hook_url: str | None = None,
    file_store_web_hook_headers: dict | None = None,
) -> FileStore:
    """文件存储工厂函数"""

    # 创建基础存储
    if file_store_type == 'local':
        store = LocalFileStore(file_store_path)
    elif file_store_type == 's3':
        store = S3FileStore(file_store_path)
    elif file_store_type == 'google_cloud':
        store = GoogleCloudFileStore(file_store_path)
    else:
        store = InMemoryFileStore()

    # 添加WebHook装饰器
    if file_store_web_hook_url:
        store = WebHookFileStore(store, file_store_web_hook_url, httpx.Client())

    return store
```

### 4. 仓储模式 (Repository Pattern)

```python
class ConversationRepository:
    """对话仓储"""

    def __init__(self, store: ConversationStore):
        self.store = store

    async def find_by_id(self, conversation_id: str) -> ConversationMetadata | None:
        try:
            return await self.store.load_conversation(conversation_id)
        except FileNotFoundError:
            return None

    async def find_by_user(self, user_id: str) -> list[ConversationMetadata]:
        conversations = []
        try:
            files = self.store.file_store.list(f"users/{user_id}/conversations/")
            for file in files:
                if file.endswith('/metadata.json'):
                    conversation_id = file.split('/')[-2]
                    metadata = await self.store.load_conversation(conversation_id)
                    conversations.append(metadata)
        except FileNotFoundError:
            pass
        return conversations

    async def save(self, metadata: ConversationMetadata) -> None:
        await self.store.save_conversation(metadata.conversation_id, metadata)

    async def delete(self, conversation_id: str) -> None:
        path = f"conversations/{conversation_id}/"
        self.store.file_store.delete(path)
```

## 数据流和生命周期

### 1. 数据写入流程

```
用户操作 → 应用层 → 数据模型验证 → 序列化 → 存储管理器 → 文件存储 → 持久化
    ↓
WebHook通知 ← 装饰器 ← 存储后端 ← 路径解析 ← 内容处理 ← JSON序列化
```

### 2. 数据读取流程

```
应用请求 → 存储管理器 → 文件存储 → 存储后端 → 内容读取 → JSON反序列化 → 数据模型验证 → 返回对象
```

### 3. 缓存策略

```python
class CachedStorageManager:
    """带缓存的存储管理器"""

    def __init__(self, store: FileStore, cache_ttl: int = 300):
        self.store = store
        self.cache = {}
        self.cache_ttl = cache_ttl

    async def get_with_cache(self, key: str, loader: Callable) -> Any:
        now = time.time()

        # 检查缓存
        if key in self.cache:
            cached_item = self.cache[key]
            if now - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']

        # 加载数据
        data = await loader()

        # 更新缓存
        self.cache[key] = {
            'data': data,
            'timestamp': now
        }

        return data
```

## 安全性设计

### 1. 敏感信息保护

```python
class SecretStr:
    """敏感字符串类型"""

    def __init__(self, secret: str):
        self._secret = secret

    def get_secret_value(self) -> str:
        return self._secret

    def __str__(self) -> str:
        return "********"

    def __repr__(self) -> str:
        return "SecretStr('********')"

# 使用示例
api_key = SecretStr("sk-1234567890abcdef")
print(api_key)  # 输出: ********
print(api_key.get_secret_value())  # 输出: sk-1234567890abcdef
```

### 2. 访问控制

```python
class SecureFileStore(FileStoreDecorator):
    """安全文件存储装饰器"""

    def __init__(self, store: FileStore, user_id: str):
        super().__init__(store)
        self.user_id = user_id

    def _check_access(self, path: str) -> bool:
        """检查用户是否有权限访问路径"""
        allowed_prefixes = [
            f"users/{self.user_id}/",
            f"conversations/{self.user_id}_",
            "public/"
        ]
        return any(path.startswith(prefix) for prefix in allowed_prefixes)

    def read(self, path: str) -> str:
        if not self._check_access(path):
            raise PermissionError(f"Access denied to path: {path}")
        return self.store.read(path)

    def write(self, path: str, contents: str | bytes) -> None:
        if not self._check_access(path):
            raise PermissionError(f"Access denied to path: {path}")
        self.store.write(path, contents)
```

### 3. 数据加密

```python
class EncryptedFileStore(FileStoreDecorator):
    """加密文件存储装饰器"""

    def __init__(self, store: FileStore, encryption_key: bytes):
        super().__init__(store)
        self.cipher = Fernet(encryption_key)

    def write(self, path: str, contents: str | bytes) -> None:
        if isinstance(contents, str):
            contents = contents.encode('utf-8')
        encrypted = self.cipher.encrypt(contents)
        self.store.write(path, encrypted)

    def read(self, path: str) -> str:
        encrypted_content = self.store.read(path)
        decrypted = self.cipher.decrypt(encrypted_content.encode())
        return decrypted.decode('utf-8')
```

## 性能优化

### 1. 连接池管理

```python
class PooledS3FileStore(S3FileStore):
    """带连接池的S3存储"""

    def __init__(self, bucket_name: str, max_connections: int = 10):
        super().__init__(bucket_name)
        self.session = boto3.Session()
        self.s3_client = self.session.client(
            's3',
            config=Config(
                max_pool_connections=max_connections,
                retries={'max_attempts': 3}
            )
        )
```

### 2. 批量操作

```python
class BatchFileStore(FileStoreDecorator):
    """批量操作文件存储"""

    def __init__(self, store: FileStore, batch_size: int = 100):
        super().__init__(store)
        self.batch_size = batch_size
        self.write_batch = []

    def write(self, path: str, contents: str | bytes) -> None:
        self.write_batch.append((path, contents))
        if len(self.write_batch) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        for path, contents in self.write_batch:
            self.store.write(path, contents)
        self.write_batch.clear()
```

### 3. 异步I/O

```python
class AsyncFileStore:
    """异步文件存储接口"""

    async def write(self, path: str, contents: str | bytes) -> None:
        raise NotImplementedError

    async def read(self, path: str) -> str:
        raise NotImplementedError

class AsyncLocalFileStore(AsyncFileStore):
    """异步本地文件存储"""

    async def write(self, path: str, contents: str | bytes) -> None:
        full_path = self.get_full_path(path)
        mode = 'w' if isinstance(contents, str) else 'wb'

        async with aiofiles.open(full_path, mode) as f:
            await f.write(contents)

    async def read(self, path: str) -> str:
        full_path = self.get_full_path(path)

        async with aiofiles.open(full_path, 'r') as f:
            return await f.read()
```

## 监控和日志

### 1. 操作日志

```python
class LoggingFileStore(FileStoreDecorator):
    """日志记录文件存储装饰器"""

    def __init__(self, store: FileStore, logger: logging.Logger):
        super().__init__(store)
        self.logger = logger

    def write(self, path: str, contents: str | bytes) -> None:
        start_time = time.time()
        try:
            self.store.write(path, contents)
            duration = time.time() - start_time
            self.logger.info(
                "File write successful",
                extra={
                    'path': path,
                    'size': len(contents),
                    'duration': duration,
                    'operation': 'write'
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "File write failed",
                extra={
                    'path': path,
                    'error': str(e),
                    'duration': duration,
                    'operation': 'write'
                }
            )
            raise
```

### 2. 性能指标

```python
class MetricsFileStore(FileStoreDecorator):
    """性能指标收集装饰器"""

    def __init__(self, store: FileStore, metrics_collector):
        super().__init__(store)
        self.metrics = metrics_collector

    def write(self, path: str, contents: str | bytes) -> None:
        with self.metrics.timer('file_store.write.duration'):
            self.store.write(path, contents)

        self.metrics.increment('file_store.write.count')
        self.metrics.histogram('file_store.write.size', len(contents))

    def read(self, path: str) -> str:
        with self.metrics.timer('file_store.read.duration'):
            content = self.store.read(path)

        self.metrics.increment('file_store.read.count')
        self.metrics.histogram('file_store.read.size', len(content))

        return content
```

## 配置管理

### 1. 存储配置

```python
@dataclass
class StorageConfig:
    """存储配置"""

    # 基础配置
    storage_type: str = 'local'
    storage_path: str = './storage'

    # 性能配置
    enable_caching: bool = True
    cache_size: int = 1000
    cache_ttl: int = 300
    batch_size: int = 100

    # 安全配置
    enable_encryption: bool = False
    encryption_key: str | None = None
    enable_access_control: bool = True

    # WebHook配置
    webhook_url: str | None = None
    webhook_headers: dict | None = None

    # 云存储配置
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = 'us-east-1'

    gcp_credentials_path: str | None = None
    gcp_project_id: str | None = None

class StorageConfigManager:
    """存储配置管理器"""

    @staticmethod
    def load_from_env() -> StorageConfig:
        """从环境变量加载配置"""
        return StorageConfig(
            storage_type=os.getenv('STORAGE_TYPE', 'local'),
            storage_path=os.getenv('STORAGE_PATH', './storage'),
            enable_caching=os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            cache_size=int(os.getenv('CACHE_SIZE', '1000')),
            webhook_url=os.getenv('WEBHOOK_URL'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        )

    @staticmethod
    def create_file_store(config: StorageConfig) -> FileStore:
        """根据配置创建文件存储"""
        # 创建基础存储
        if config.storage_type == 'local':
            store = LocalFileStore(config.storage_path)
        elif config.storage_type == 's3':
            store = S3FileStore(config.storage_path)
        elif config.storage_type == 'gcs':
            store = GoogleCloudFileStore(config.storage_path)
        else:
            store = InMemoryFileStore()

        # 添加装饰器
        if config.enable_caching:
            store = CachingFileStore(store, config.cache_size)

        if config.enable_encryption and config.encryption_key:
            store = EncryptedFileStore(store, config.encryption_key.encode())

        if config.webhook_url:
            store = WebHookFileStore(store, config.webhook_url, httpx.Client())

        return store
```

## 测试策略

### 1. 单元测试

```python
class TestFileStore:
    """文件存储单元测试"""

    @pytest.fixture
    def memory_store(self):
        return InMemoryFileStore()

    def test_write_and_read(self, memory_store):
        content = "Hello, World!"
        memory_store.write("test.txt", content)
        assert memory_store.read("test.txt") == content

    def test_list_files(self, memory_store):
        memory_store.write("dir/file1.txt", "content1")
        memory_store.write("dir/file2.txt", "content2")
        files = memory_store.list("dir/")
        assert "dir/file1.txt" in files
        assert "dir/file2.txt" in files

    def test_delete_file(self, memory_store):
        memory_store.write("test.txt", "content")
        memory_store.delete("test.txt")
        with pytest.raises(FileNotFoundError):
            memory_store.read("test.txt")
```

### 2. 集成测试

```python
class TestStorageIntegration:
    """存储集成测试"""

    @pytest.fixture
    def storage_manager(self):
        store = InMemoryFileStore()
        return ConversationStore(store)

    async def test_save_and_load_conversation(self, storage_manager):
        metadata = ConversationMetadata(
            conversation_id="test-123",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=ConversationStatus.ACTIVE
        )

        await storage_manager.save_conversation("test-123", metadata)
        loaded = await storage_manager.load_conversation("test-123")

        assert loaded.conversation_id == metadata.conversation_id
        assert loaded.title == metadata.title
```

### 3. 性能测试

```python
class TestStoragePerformance:
    """存储性能测试"""

    def test_write_performance(self):
        store = InMemoryFileStore()
        content = "x" * 1024  # 1KB content

        start_time = time.time()
        for i in range(1000):
            store.write(f"file_{i}.txt", content)
        duration = time.time() - start_time

        assert duration < 1.0  # Should complete in less than 1 second
        assert len(store.files) == 1000

    def test_concurrent_access(self):
        store = InMemoryFileStore()

        def write_worker(worker_id: int):
            for i in range(100):
                store.write(f"worker_{worker_id}_file_{i}.txt", f"content_{i}")

        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=write_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(store.files) == 1000
```

## 最佳实践

### 1. 存储选择指南

| 场景 | 推荐存储 | 原因 |
|------|----------|------|
| 开发环境 | LocalFileStore | 简单、快速、易调试 |
| 测试环境 | InMemoryFileStore | 隔离、可控、快速 |
| 单机生产 | LocalFileStore | 高性能、低延迟 |
| 分布式部署 | S3FileStore | 高可用、可扩展 |
| 云原生应用 | GoogleCloudFileStore | 云服务集成 |

### 2. 性能优化建议

1. **使用缓存**: 对频繁访问的数据启用缓存
2. **批量操作**: 合并多个小操作为批量操作
3. **异步I/O**: 使用异步操作避免阻塞
4. **连接池**: 复用网络连接减少开销
5. **压缩存储**: 对大文件启用压缩

### 3. 安全最佳实践

1. **敏感信息加密**: 使用SecretStr保护API密钥
2. **访问控制**: 实施基于路径的访问控制
3. **数据加密**: 对敏感数据启用存储加密
4. **审计日志**: 记录所有存储操作
5. **定期备份**: 建立数据备份机制

### 4. 监控和运维

1. **性能指标**: 监控读写延迟和吞吐量
2. **错误率**: 跟踪操作失败率
3. **存储使用**: 监控存储空间使用情况
4. **健康检查**: 定期检查存储后端健康状态
5. **告警机制**: 设置关键指标告警

## 总结

OpenHands的存储系统具有以下特点：

### 技术优势
1. **模块化设计**: 清晰的分层架构和组件分离
2. **多后端支持**: 支持本地、云存储等多种后端
3. **高度可扩展**: 易于添加新的存储后端和功能
4. **类型安全**: 使用Pydantic确保数据类型安全

### 架构特色
1. **策略模式**: 运行时可切换存储策略
2. **装饰器模式**: 灵活的功能扩展机制
3. **仓储模式**: 统一的数据访问接口
4. **工厂模式**: 简化对象创建和配置

### 应用价值
1. **开发效率**: 统一的API简化开发
2. **运维友好**: 支持多种部署场景
3. **安全可靠**: 完善的安全和监控机制
4. **性能优秀**: 多层次的性能优化

这个存储系统为OpenHands提供了强大而灵活的数据持久化能力，支持从开发到生产的全生命周期需求。
