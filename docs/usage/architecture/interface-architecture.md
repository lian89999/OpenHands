# OpenHands 控制接口通路和配置接口通路完整结构

## 总体架构概览

OpenHands 采用前后端分离的架构，前端使用 React + TypeScript，后端使用 FastAPI + Python。系统通过 WebSocket 和 REST API 两种方式进行通信。

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   前端层 (Frontend)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  React Components  │  State Management  │  API Client  │  WebSocket Client      │
│  - 用户界面组件     │  - Redux Store     │  - REST API  │  - Socket.IO Client    │
│  - 设置界面        │  - Chat Slice      │  - Axios     │  - 实时事件处理         │
│  - 对话界面        │  - Agent Slice     │  - TanStack  │  - 消息传递            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  网络通信层                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│           WebSocket 连接                    │           HTTP/REST API            │
│  - 实时双向通信                             │  - 请求/响应模式                    │
│  - 事件流传输                               │  - 配置管理                        │
│  - Agent 状态更新                           │  - 文件操作                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  后端服务层 (Backend)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│  FastAPI Server  │  Route Handlers  │  Session Manager  │  Conversation Manager │
│  - app.py        │  - conversation  │  - agent_session  │  - 对话生命周期管理    │
│  - 中间件        │  - settings      │  - session.py     │  - 状态跟踪           │
│  - 依赖注入      │  - files         │  - 会话管理       │  - 事件流处理         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   控制层 (Controller)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Agent Controller │  State Tracker  │  Event Stream    │  Action Parser         │
│  - 代理生命周期    │  - 状态管理     │  - 事件处理      │  - 动作解析            │
│  - 任务执行       │  - 状态跟踪     │  - 观察结果      │  - 响应生成            │
│  - 错误处理       │  - 状态持久化   │  - 事件订阅      │  - 格式验证            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   代理层 (Agent)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Agent Hub       │  CodeAct Agent   │  Memory System   │  Microagents          │
│  - 代理注册      │  - 代码执行      │  - 对话记忆      │  - 专业化提示          │
│  - 代理选择      │  - 任务规划      │  - 上下文管理    │  - 领域知识            │
│  - 能力管理      │  - 工具调用      │  - 历史压缩      │  - 仓库特定指令        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  运行时层 (Runtime)                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Runtime Manager │  Docker Runtime  │  E2B Runtime     │  Local Runtime        │
│  - 环境管理      │  - 容器化执行    │  - 云端沙盒      │  - 本地执行            │
│  - 资源分配      │  - 隔离环境      │  - 安全隔离      │  - 开发测试            │
│  - 生命周期      │  - 镜像构建      │  - 扩展性        │  - 快速迭代            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  存储层 (Storage)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Conversation    │  Settings Store  │  Secrets Store   │  File Store           │
│  - 对话历史      │  - 用户设置      │  - 敏感信息      │  - 文件管理            │
│  - 事件存储      │  - 配置持久化    │  - API 密钥      │  - 版本控制            │
│  - 轨迹记录      │  - 偏好设置      │  - 令牌管理      │  - 备份恢复            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 1. 控制接口通路 (Control Interface Pathway)

### 1.1 前端控制接口

#### WebSocket 客户端 (`frontend/src/context/ws-client-provider.tsx`)
```typescript
// WebSocket 连接管理
interface UseWsClient {
  webSocketStatus: WebSocketStatus;
  isLoadingMessages: boolean;
  events: Record<string, unknown>[];
  parsedEvents: (OpenHandsAction | OpenHandsObservation)[];
  send: (event: Record<string, unknown>) => void;
}

// 事件类型处理
- UserMessageAction: 用户消息
- AssistantMessageAction: 助手回复
- CommandAction: 命令执行
- FileEditAction: 文件编辑
- FileWriteAction: 文件写入
```

#### REST API 客户端 (`frontend/src/api/open-hands.ts`)
```typescript
class OpenHands {
  // 配置管理
  static async getModels(): Promise<string[]>
  static async getAgents(): Promise<string[]>
  static async getConfig(): Promise<GetConfigResponse>

  // 对话管理
  static async getConversations(): Promise<ResultSet<Conversation>>
  static async createConversation(): Promise<Conversation>
  static async deleteConversation(conversationId: string): Promise<void>

  // 文件操作
  static async getFiles(path?: string): Promise<FileSystemItem[]>
  static async uploadFiles(files: File[]): Promise<void>
}
```

#### 状态管理 (`frontend/src/state/`)
```typescript
// Agent 状态切片
interface AgentState {
  curAgentState: AgentStateType;
  isAgentPaused: boolean;
  isAgentTaskCompleted: boolean;
}

// 聊天状态切片
interface ChatState {
  messages: Message[];
  isLoadingMessages: boolean;
  isStreaming: boolean;
}
```

### 1.2 后端控制接口

#### FastAPI 应用入口 (`openhands/server/app.py`)
```python
# 路由注册
app.include_router(conversation_api_router)  # 对话管理
app.include_router(settings_router)         # 设置管理
app.include_router(files_api_router)        # 文件操作
app.include_router(security_api_router)     # 安全分析
app.include_router(mcp_server.http_app)     # MCP 服务
```

#### 对话路由 (`openhands/server/routes/conversation.py`)
```python
@app.get('/config')
async def get_remote_runtime_config() -> JSONResponse
    # 获取运行时配置

@app.get('/vscode-url')
async def get_vscode_url() -> JSONResponse
    # 获取 VSCode URL

@app.get('/web-hosts')
async def get_hosts() -> JSONResponse
    # 获取 Web 主机信息
```

#### WebSocket 处理 (`openhands/server/listen_socket.py`)
```python
# Socket.IO 事件处理
@sio.event
async def connect(sid, environ, auth):
    # 客户端连接处理

@sio.event
async def action(sid, data):
    # 动作事件处理

@sio.event
async def disconnect(sid):
    # 客户端断开处理
```

### 1.3 代理控制器 (`openhands/controller/agent_controller.py`)

```python
class AgentController:
    def __init__(self, agent: Agent, event_stream: EventStream, ...):
        self.agent = agent
        self.event_stream = event_stream
        self.state_tracker = StateTracker()
        self.stuck_detector = StuckDetector()

    async def start_loop(self, task: str) -> None:
        # 主控制循环

    async def step(self, action: Action) -> Observation:
        # 单步执行

    def get_state(self) -> State:
        # 获取当前状态
```

### 1.4 事件流系统 (`openhands/events/`)

```python
# 事件类型
class Action(Event):
    # 代理动作基类

class Observation(Event):
    # 观察结果基类

# 具体动作类型
- CmdRunAction: 命令执行
- FileReadAction: 文件读取
- FileWriteAction: 文件写入
- BrowseURLAction: 网页浏览
- MessageAction: 消息发送

# 具体观察类型
- CmdOutputObservation: 命令输出
- FileReadObservation: 文件内容
- BrowserObservation: 浏览器结果
- ErrorObservation: 错误信息
```

## 2. 配置接口通路 (Configuration Interface Pathway)

### 2.1 前端配置接口

#### 设置页面组件 (`frontend/src/routes/`)
```typescript
// 应用设置
app-settings.tsx: 通用应用设置
llm-settings.tsx: LLM 模型配置
git-settings.tsx: Git 集成设置
secrets-settings.tsx: 密钥管理
user-settings.tsx: 用户偏好设置
mcp-settings.tsx: MCP 配置
```

#### 设置类型定义 (`frontend/src/types/settings.ts`)
```typescript
interface Settings {
  LLM_MODEL: string;
  LLM_API_KEY: string;
  AGENT: string;
  LANGUAGE: string;
  LLM_BASE_URL?: string;
  CONFIRMATION_MODE: boolean;
  SECURITY_ANALYZER?: string;
  // ... 更多设置项
}

interface ApiSettings extends Settings {
  llm_api_key_set: boolean;
  search_api_key_set: boolean;
  provider_tokens_set: Record<ProviderType, string | null>;
}
```

#### 设置服务 (`frontend/src/services/settings.ts`)
```typescript
export const DEFAULT_SETTINGS: Settings = {
  LLM_MODEL: "gpt-4o",
  LLM_API_KEY: "",
  AGENT: "CodeActAgent",
  LANGUAGE: "en",
  CONFIRMATION_MODE: false,
  SECURITY_ANALYZER: "",
  // ... 默认值
};
```

### 2.2 后端配置接口

#### 设置路由 (`openhands/server/routes/settings.py`)
```python
@app.get('/settings', response_model=GETSettingsModel)
async def load_settings() -> GETSettingsModel | JSONResponse:
    # 加载用户设置

@app.post('/reset-settings')
async def reset_settings() -> JSONResponse:
    # 重置设置（已弃用）
```

#### 核心配置类 (`openhands/core/config/`)

##### OpenHands 主配置 (`openhands_config.py`)
```python
class OpenHandsConfig(BaseModel):
    # LLM 配置
    llms: dict[str, LLMConfig] = Field(default_factory=dict)

    # 代理配置
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    default_agent: str = Field(default=OH_DEFAULT_AGENT)

    # 沙盒配置
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)

    # 安全配置
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # 运行时配置
    runtime: str = Field(default='docker')

    # 文件存储配置
    file_store: str = Field(default='local')
    file_store_path: str = Field(default='~/.openhands')

    # 其他配置项...
```

##### LLM 配置 (`llm_config.py`)
```python
class LLMConfig(BaseModel):
    model: str = Field(default="gpt-4o")
    api_key: SecretStr | None = Field(default=None)
    base_url: str | None = Field(default=None)
    api_version: str | None = Field(default=None)
    embedding_model: str | None = Field(default=None)
    embedding_base_url: str | None = Field(default=None)
    embedding_api_key: SecretStr | None = Field(default=None)
    num_retries: int = Field(default=8)
    retry_multiplier: float = Field(default=2)
    retry_min_wait: int = Field(default=15)
    retry_max_wait: int = Field(default=120)
    timeout: int | None = Field(default=None)
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=1.0)
    max_message_chars: int = Field(default=30_000)
    max_input_tokens: int | None = Field(default=None)
    max_output_tokens: int | None = Field(default=None)
    cost_per_input_token: float | None = Field(default=None)
    cost_per_output_token: float | None = Field(default=None)
    disable_vision: bool = Field(default=False)
    draft: bool = Field(default=False)
    caching_prompt: bool = Field(default=True)
    drop_params: bool = Field(default=False)
```

##### 代理配置 (`agent_config.py`)
```python
class AgentConfig(BaseModel):
    memory_enabled: bool = Field(default=True)
    memory_max_threads: int = Field(default=3)
    llm_config: LLMConfig = Field(default_factory=LLMConfig)
    codeact_enable_jupyter: bool = Field(default=False)
    codeact_enable_llm_editor: bool = Field(default=True)
    codeact_enable_browsing: bool = Field(default=True)
    function_calling: bool = Field(default=True)
    micro_agent_name: str | None = Field(default=None)
```

##### 沙盒配置 (`sandbox_config.py`)
```python
class SandboxConfig(BaseModel):
    base_container_image: str = Field(default='ghcr.io/all-hands-ai/runtime:0.14-nikolaik')
    runtime_container_image: str | None = Field(default=None)
    user_id: int = Field(default=1000)
    timeout: int = Field(default=120)
    api_key: SecretStr | None = Field(default=None)
    api_url: str | None = Field(default=None)
    keep_runtime_alive: bool = Field(default=False)
    remote_runtime_resource_factor: float = Field(default=1.0)
    enable_auto_lint: bool = Field(default=False)
    use_host_network: bool = Field(default=False)
    initialize_plugins: bool = Field(default=True)
    plugins: list[PluginRequirement] = Field(default_factory=list)
    browsergym_eval_env: str | None = Field(default=None)
```

### 2.3 存储层配置

#### 设置存储 (`openhands/storage/settings/`)
```python
class SettingsStore(ABC):
    @abstractmethod
    async def load(self, user_id: str) -> Settings | None:
        # 加载用户设置

    @abstractmethod
    async def store(self, user_id: str, settings: Settings) -> None:
        # 存储用户设置

class FileSettingsStore(SettingsStore):
    # 基于文件的设置存储实现
```

#### 密钥存储 (`openhands/storage/secrets/`)
```python
class SecretsStore(ABC):
    @abstractmethod
    async def store_secret(self, user_id: str, key: str, value: str) -> None:
        # 存储密钥

    @abstractmethod
    async def get_secret(self, user_id: str, key: str) -> str | None:
        # 获取密钥

class FileSecretsStore(SecretsStore):
    # 基于文件的密钥存储实现
```

#### 数据模型 (`openhands/storage/data_models/`)
```python
class Settings(BaseModel):
    user_id: str
    llm_model: str = Field(default="gpt-4o")
    llm_api_key: str | None = Field(default=None)
    llm_base_url: str | None = Field(default=None)
    agent: str = Field(default="CodeActAgent")
    language: str = Field(default="en")
    confirmation_mode: bool = Field(default=False)
    security_analyzer: str = Field(default="")
    # ... 更多字段

class UserSecrets(BaseModel):
    user_id: str
    provider_tokens: dict[ProviderType, ProviderToken] = Field(default_factory=dict)
    # ... 其他密钥字段
```

## 3. 关键通信流程

### 3.1 用户消息处理流程

```
用户输入 → 前端组件 → WebSocket 发送 → 后端 Socket.IO →
会话管理器 → 代理控制器 → 代理执行 → 运行时环境 →
结果返回 → 观察事件 → WebSocket 推送 → 前端更新
```

### 3.2 配置更新流程

```
设置界面 → 表单提交 → REST API → 设置路由 →
设置存储 → 数据持久化 → 响应返回 → 前端确认
```

### 3.3 文件操作流程

```
文件请求 → 文件 API → 文件服务 → 运行时文件系统 →
文件内容 → 响应返回 → 前端展示
```

## 4. 安全和权限控制

### 4.1 认证机制
- JWT Token 认证
- Session API Key
- Provider Token 管理

### 4.2 权限控制
- 用户级别隔离
- 文件访问控制
- API 访问限制

### 4.3 安全分析
- 代码安全扫描
- 命令执行监控
- 敏感信息保护

## 5. 扩展性设计

### 5.1 插件系统
- Microagent 机制
- MCP (Model Context Protocol) 支持
- 自定义工具集成

### 5.2 多运行时支持
- Docker 容器化
- E2B 云端沙盒
- 本地开发环境
- Modal 分布式计算

### 5.3 存储抽象
- 多种存储后端
- 文件系统抽象
- 配置存储分离

这个架构设计确保了 OpenHands 的高度可扩展性、安全性和可维护性，同时提供了清晰的接口分离和模块化设计。
