# OpenHands 事件系统接口文档

## 概述

本文档详细描述了OpenHands事件系统的控制接口和配置接口，包括API设计、接口规范、使用方法和配置选项。这些接口是外部系统与OpenHands事件系统交互的主要通道。

## 控制接口(Control Interface)

### 1. 事件流控制接口

#### 1.1 EventStream API

```python
class EventStreamAPI:
    """事件流控制API"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.event_stream = EventStream(session_id)

    async def add_event(self, event_data: dict, source: str = "USER") -> dict:
        """
        添加事件到事件流

        Args:
            event_data: 事件数据字典
            source: 事件来源 (USER/AGENT/ENVIRONMENT)

        Returns:
            dict: 包含事件ID和状态的响应
        """
        try:
            # 1. 验证事件数据
            validated_data = self._validate_event_data(event_data)

            # 2. 创建事件对象
            event = event_from_dict(validated_data)
            event.source = EventSource(source)

            # 3. 添加到事件流
            await self.event_stream.add_event(event, EventStreamSubscriber.MAIN)

            return {
                "status": "success",
                "event_id": event.id,
                "timestamp": event.timestamp
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_events(self, start: int = 0, end: int = -1,
                        filter_params: dict = None) -> dict:
        """
        获取事件列表

        Args:
            start: 起始事件ID
            end: 结束事件ID (-1表示最新)
            filter_params: 过滤参数

        Returns:
            dict: 事件列表和元数据
        """
        try:
            # 1. 获取事件
            events = await self.event_stream.get_events(start, end)

            # 2. 应用过滤器
            if filter_params:
                events = self._apply_filter(events, filter_params)

            # 3. 序列化事件
            serialized_events = [event_to_dict(e) for e in events]

            return {
                "status": "success",
                "events": serialized_events,
                "total_count": len(serialized_events),
                "start": start,
                "end": end if end != -1 else events[-1].id if events else 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def subscribe_events(self, callback, event_types: list = None) -> str:
        """
        订阅事件流

        Args:
            callback: 事件回调函数
            event_types: 订阅的事件类型列表

        Returns:
            str: 订阅ID
        """
        subscription_id = str(uuid.uuid4())

        async def filtered_callback(event: Event):
            if not event_types or self._get_event_type(event) in event_types:
                await callback(event)

        self.event_stream.subscribe(
            EventStreamSubscriber.MAIN,
            filtered_callback
        )

        return subscription_id

    async def unsubscribe_events(self, subscription_id: str) -> bool:
        """取消事件订阅"""
        # 实现取消订阅逻辑
        return True
```

#### 1.2 REST API 接口

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class EventRequest(BaseModel):
    """事件请求模型"""
    action: str
    content: str = ""
    source: str = "USER"
    metadata: dict = {}

class EventResponse(BaseModel):
    """事件响应模型"""
    status: str
    event_id: int = None
    error: str = None

@app.post("/api/v1/events", response_model=EventResponse)
async def create_event(session_id: str, event_request: EventRequest):
    """
    创建新事件

    POST /api/v1/events?session_id=xxx
    {
        "action": "message",
        "content": "Hello, world!",
        "source": "USER",
        "metadata": {}
    }
    """
    try:
        api = EventStreamAPI(session_id)
        result = await api.add_event(event_request.dict(), event_request.source)

        if result["status"] == "success":
            return EventResponse(
                status="success",
                event_id=result["event_id"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/events")
async def get_events(session_id: str, start: int = 0, end: int = -1,
                    event_types: str = None, sources: str = None):
    """
    获取事件列表

    GET /api/v1/events?session_id=xxx&start=0&end=10&event_types=message,run
    """
    try:
        api = EventStreamAPI(session_id)

        # 构建过滤参数
        filter_params = {}
        if event_types:
            filter_params["event_types"] = event_types.split(",")
        if sources:
            filter_params["sources"] = sources.split(",")

        result = await api.get_events(start, end, filter_params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/v1/events/stream")
async def event_stream_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket事件流

    连接: ws://localhost:8000/api/v1/events/stream?session_id=xxx
    """
    await websocket.accept()

    try:
        api = EventStreamAPI(session_id)

        async def send_event(event: Event):
            await websocket.send_json(event_to_dict(event))

        subscription_id = await api.subscribe_events(send_event)

        # 保持连接
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息

    except WebSocketDisconnect:
        await api.unsubscribe_events(subscription_id)
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
```

### 2. 代理控制接口

#### 2.1 Agent Controller API

```python
class AgentControllerAPI:
    """代理控制器API"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agent_controller = AgentController(session_id)

    async def start_agent(self, agent_config: dict) -> dict:
        """
        启动代理

        Args:
            agent_config: 代理配置

        Returns:
            dict: 启动结果
        """
        try:
            # 1. 验证配置
            config = self._validate_agent_config(agent_config)

            # 2. 创建代理实例
            agent = self._create_agent(config)

            # 3. 启动代理
            await self.agent_controller.start_agent(agent)

            return {
                "status": "success",
                "agent_id": agent.id,
                "state": "running"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def stop_agent(self, agent_id: str) -> dict:
        """停止代理"""
        try:
            await self.agent_controller.stop_agent(agent_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_agent_status(self, agent_id: str) -> dict:
        """获取代理状态"""
        try:
            status = await self.agent_controller.get_agent_status(agent_id)
            return {
                "status": "success",
                "agent_status": status
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def send_message_to_agent(self, agent_id: str, message: str) -> dict:
        """向代理发送消息"""
        try:
            # 创建消息事件
            message_action = MessageAction(
                content=message,
                source=EventSource.USER
            )

            # 发送给代理
            await self.agent_controller.send_action(agent_id, message_action)

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

#### 2.2 Agent Management REST API

```python
class AgentConfig(BaseModel):
    """代理配置模型"""
    agent_type: str = "CodeActAgent"
    llm_config: dict = {}
    max_iterations: int = 100
    tools: list[str] = []
    runtime_config: dict = {}

@app.post("/api/v1/agents")
async def create_agent(session_id: str, config: AgentConfig):
    """
    创建代理

    POST /api/v1/agents?session_id=xxx
    {
        "agent_type": "CodeActAgent",
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.1
        },
        "max_iterations": 100,
        "tools": ["bash", "python", "browser"],
        "runtime_config": {
            "runtime_type": "docker",
            "image": "python:3.12"
        }
    }
    """
    try:
        api = AgentControllerAPI(session_id)
        result = await api.start_agent(config.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/{agent_id}/status")
async def get_agent_status(session_id: str, agent_id: str):
    """获取代理状态"""
    try:
        api = AgentControllerAPI(session_id)
        result = await api.get_agent_status(agent_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{agent_id}/message")
async def send_message(session_id: str, agent_id: str, message: dict):
    """向代理发送消息"""
    try:
        api = AgentControllerAPI(session_id)
        result = await api.send_message_to_agent(agent_id, message["content"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/agents/{agent_id}")
async def stop_agent(session_id: str, agent_id: str):
    """停止代理"""
    try:
        api = AgentControllerAPI(session_id)
        result = await api.stop_agent(agent_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 运行时控制接口

#### 3.1 Runtime Controller API

```python
class RuntimeControllerAPI:
    """运行时控制器API"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.runtime_controller = RuntimeController(session_id)

    async def create_runtime(self, runtime_config: dict) -> dict:
        """
        创建运行时环境

        Args:
            runtime_config: 运行时配置

        Returns:
            dict: 创建结果
        """
        try:
            # 1. 验证配置
            config = self._validate_runtime_config(runtime_config)

            # 2. 创建运行时
            runtime = await self.runtime_controller.create_runtime(config)

            return {
                "status": "success",
                "runtime_id": runtime.id,
                "runtime_type": runtime.type,
                "state": "ready"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def execute_action(self, runtime_id: str, action: dict) -> dict:
        """在运行时中执行动作"""
        try:
            # 1. 创建动作对象
            action_obj = action_from_dict(action)

            # 2. 执行动作
            observation = await self.runtime_controller.execute_action(
                runtime_id, action_obj
            )

            return {
                "status": "success",
                "observation": observation_to_dict(observation)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_runtime_status(self, runtime_id: str) -> dict:
        """获取运行时状态"""
        try:
            status = await self.runtime_controller.get_runtime_status(runtime_id)
            return {"status": "success", "runtime_status": status}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def destroy_runtime(self, runtime_id: str) -> dict:
        """销毁运行时环境"""
        try:
            await self.runtime_controller.destroy_runtime(runtime_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

## 配置接口(Configuration Interface)

### 1. 系统配置

#### 1.1 EventSystemConfig

```python
@dataclass
class EventSystemConfig:
    """事件系统配置"""

    # 事件存储配置
    storage_backend: str = "file"           # 存储后端: file, redis, database
    storage_path: str = "./events"          # 存储路径
    max_events_per_file: int = 1000         # 每个文件最大事件数

    # 事件流配置
    max_subscribers: int = 10               # 最大订阅者数量
    event_buffer_size: int = 1000           # 事件缓冲区大小
    batch_size: int = 100                   # 批处理大小

    # 性能配置
    enable_caching: bool = True             # 启用缓存
    cache_size: int = 1000                  # 缓存大小
    cache_ttl: int = 3600                   # 缓存TTL(秒)

    # 安全配置
    enable_validation: bool = True          # 启用事件验证
    max_event_size: int = 1024 * 1024       # 最大事件大小(字节)
    allowed_sources: list[str] = None       # 允许的事件来源

    # 监控配置
    enable_metrics: bool = True             # 启用指标收集
    metrics_interval: int = 60              # 指标收集间隔(秒)
    enable_tracing: bool = False            # 启用事件追踪

    def __post_init__(self):
        """配置验证"""
        if self.allowed_sources is None:
            self.allowed_sources = ["USER", "AGENT", "ENVIRONMENT"]

        if self.storage_backend not in ["file", "redis", "database"]:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")

class EventSystemConfigManager:
    """事件系统配置管理器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> EventSystemConfig:
        """加载配置"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            return EventSystemConfig(**config_data)
        else:
            return EventSystemConfig()

    def save_config(self):
        """保存配置"""
        if self.config_file:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

    def get_config(self) -> EventSystemConfig:
        """获取配置"""
        return self.config
```

#### 1.2 配置API接口

```python
@app.get("/api/v1/config/event-system")
async def get_event_system_config():
    """获取事件系统配置"""
    try:
        config_manager = EventSystemConfigManager()
        config = config_manager.get_config()
        return {"status": "success", "config": asdict(config)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/config/event-system")
async def update_event_system_config(config_update: dict):
    """
    更新事件系统配置

    PUT /api/v1/config/event-system
    {
        "cache_size": 2000,
        "enable_metrics": true,
        "batch_size": 200
    }
    """
    try:
        config_manager = EventSystemConfigManager()
        config_manager.update_config(**config_update)
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 代理配置

#### 2.1 AgentConfig

```python
@dataclass
class LLMConfig:
    """LLM配置"""
    model: str = "gpt-4"                    # 模型名称
    api_key: str = ""                       # API密钥
    base_url: str = ""                      # API基础URL
    temperature: float = 0.1                # 温度参数
    max_tokens: int = 4096                  # 最大token数
    timeout: int = 60                       # 超时时间(秒)

@dataclass
class AgentConfig:
    """代理配置"""
    agent_type: str = "CodeActAgent"        # 代理类型
    llm_config: LLMConfig = None            # LLM配置
    max_iterations: int = 100               # 最大迭代次数
    max_budget_per_task: float = 1.0        # 每个任务最大预算

    # 工具配置
    enabled_tools: list[str] = None         # 启用的工具
    tool_configs: dict = None               # 工具配置

    # 行为配置
    enable_auto_retry: bool = True          # 启用自动重试
    max_retry_attempts: int = 3             # 最大重试次数
    enable_confirmation: bool = False       # 启用操作确认

    # 安全配置
    sandbox_mode: bool = True               # 沙箱模式
    allowed_commands: list[str] = None      # 允许的命令
    blocked_commands: list[str] = None      # 禁止的命令

    def __post_init__(self):
        if self.llm_config is None:
            self.llm_config = LLMConfig()
        if self.enabled_tools is None:
            self.enabled_tools = ["bash", "python", "browser", "editor"]
        if self.tool_configs is None:
            self.tool_configs = {}
        if self.blocked_commands is None:
            self.blocked_commands = ["rm -rf /", "sudo rm", "format"]

class AgentConfigManager:
    """代理配置管理器"""

    def __init__(self):
        self.configs = {}  # agent_id -> AgentConfig

    def create_config(self, agent_id: str, config_data: dict) -> AgentConfig:
        """创建代理配置"""
        config = AgentConfig(**config_data)
        self.configs[agent_id] = config
        return config

    def get_config(self, agent_id: str) -> AgentConfig:
        """获取代理配置"""
        return self.configs.get(agent_id)

    def update_config(self, agent_id: str, **kwargs):
        """更新代理配置"""
        if agent_id in self.configs:
            config = self.configs[agent_id]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    def delete_config(self, agent_id: str):
        """删除代理配置"""
        if agent_id in self.configs:
            del self.configs[agent_id]
```

### 3. 运行时配置

#### 3.1 RuntimeConfig

```python
@dataclass
class DockerRuntimeConfig:
    """Docker运行时配置"""
    image: str = "python:3.12"              # Docker镜像
    memory_limit: str = "2g"                # 内存限制
    cpu_limit: str = "1.0"                  # CPU限制
    network_mode: str = "bridge"            # 网络模式
    volumes: dict = None                    # 挂载卷
    environment: dict = None                # 环境变量

    def __post_init__(self):
        if self.volumes is None:
            self.volumes = {}
        if self.environment is None:
            self.environment = {}

@dataclass
class LocalRuntimeConfig:
    """本地运行时配置"""
    working_directory: str = "/tmp"         # 工作目录
    python_path: str = "python"             # Python路径
    shell: str = "/bin/bash"                # Shell路径
    timeout: int = 300                      # 超时时间(秒)
    max_memory: int = 2048                  # 最大内存(MB)

@dataclass
class RuntimeConfig:
    """运行时配置"""
    runtime_type: str = "docker"            # 运行时类型
    docker_config: DockerRuntimeConfig = None
    local_config: LocalRuntimeConfig = None
    e2b_config: dict = None                 # E2B配置
    modal_config: dict = None               # Modal配置

    # 通用配置
    enable_networking: bool = True          # 启用网络
    enable_gpu: bool = False                # 启用GPU
    persistent_storage: bool = False        # 持久化存储

    def __post_init__(self):
        if self.runtime_type == "docker" and self.docker_config is None:
            self.docker_config = DockerRuntimeConfig()
        elif self.runtime_type == "local" and self.local_config is None:
            self.local_config = LocalRuntimeConfig()

class RuntimeConfigManager:
    """运行时配置管理器"""

    def __init__(self):
        self.configs = {}  # runtime_id -> RuntimeConfig

    def create_config(self, runtime_id: str, config_data: dict) -> RuntimeConfig:
        """创建运行时配置"""
        config = RuntimeConfig(**config_data)
        self.configs[runtime_id] = config
        return config

    def get_config(self, runtime_id: str) -> RuntimeConfig:
        """获取运行时配置"""
        return self.configs.get(runtime_id)

    def update_config(self, runtime_id: str, **kwargs):
        """更新运行时配置"""
        if runtime_id in self.configs:
            config = self.configs[runtime_id]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
```

## 接口使用示例

### 1. Python SDK 使用示例

```python
from openhands.client import OpenHandsClient

# 创建客户端
client = OpenHandsClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 创建会话
session = await client.create_session()

# 配置代理
agent_config = {
    "agent_type": "CodeActAgent",
    "llm_config": {
        "model": "gpt-4",
        "temperature": 0.1
    },
    "max_iterations": 50,
    "enabled_tools": ["bash", "python", "editor"]
}

# 启动代理
agent = await session.create_agent(agent_config)

# 发送消息
response = await agent.send_message("请帮我创建一个Python脚本")

# 订阅事件
async def event_handler(event):
    print(f"收到事件: {event['action']} - {event['content']}")

subscription = await session.subscribe_events(event_handler)

# 获取事件历史
events = await session.get_events(start=0, end=10)

# 清理资源
await subscription.unsubscribe()
await agent.stop()
await session.close()
```

### 2. JavaScript SDK 使用示例

```javascript
import { OpenHandsClient } from '@openhands/client';

// 创建客户端
const client = new OpenHandsClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'your-api-key'
});

// 创建会话
const session = await client.createSession();

// 配置代理
const agentConfig = {
    agentType: 'CodeActAgent',
    llmConfig: {
        model: 'gpt-4',
        temperature: 0.1
    },
    maxIterations: 50,
    enabledTools: ['bash', 'python', 'editor']
};

// 启动代理
const agent = await session.createAgent(agentConfig);

// 发送消息
const response = await agent.sendMessage('请帮我创建一个Python脚本');

// 订阅事件
const subscription = await session.subscribeEvents((event) => {
    console.log(`收到事件: ${event.action} - ${event.content}`);
});

// 获取事件历史
const events = await session.getEvents({ start: 0, end: 10 });

// 清理资源
await subscription.unsubscribe();
await agent.stop();
await session.close();
```

### 3. REST API 使用示例

```bash
# 创建会话
curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# 创建代理
curl -X POST "http://localhost:8000/api/v1/agents?session_id=session123" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "CodeActAgent",
    "llm_config": {
      "model": "gpt-4",
      "temperature": 0.1
    },
    "max_iterations": 50
  }'

# 发送消息
curl -X POST "http://localhost:8000/api/v1/events?session_id=session123" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "message",
    "content": "请帮我创建一个Python脚本",
    "source": "USER"
  }'

# 获取事件
curl "http://localhost:8000/api/v1/events?session_id=session123&start=0&end=10"

# 获取代理状态
curl "http://localhost:8000/api/v1/agents/agent123/status?session_id=session123"
```

## 接口安全

### 1. 认证和授权

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证API令牌"""
    token = credentials.credentials

    # 验证令牌逻辑
    if not is_valid_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return get_user_from_token(token)

@app.post("/api/v1/events")
async def create_event(
    event_request: EventRequest,
    user = Depends(verify_token)
):
    """需要认证的事件创建接口"""
    # 检查用户权限
    if not user.has_permission("create_event"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # 处理事件创建
    pass
```

### 2. 速率限制

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/events")
@limiter.limit("100/minute")
async def create_event(request: Request, event_request: EventRequest):
    """带速率限制的事件创建接口"""
    pass
```

### 3. 输入验证

```python
from pydantic import BaseModel, validator

class EventRequest(BaseModel):
    action: str
    content: str = ""
    source: str = "USER"

    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['message', 'read', 'write', 'edit', 'run']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {allowed_actions}')
        return v

    @validator('content')
    def validate_content(cls, v):
        if len(v) > 10000:  # 限制内容长度
            raise ValueError('Content too long')
        return v

    @validator('source')
    def validate_source(cls, v):
        allowed_sources = ['USER', 'AGENT', 'ENVIRONMENT']
        if v not in allowed_sources:
            raise ValueError(f'Source must be one of: {allowed_sources}')
        return v
```

## 监控和日志

### 1. 接口监控

```python
import time
from prometheus_client import Counter, Histogram, generate_latest

# 指标定义
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """请求监控中间件"""
    start_time = time.time()

    response = await call_next(request)

    # 记录指标
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(duration)

    return response

@app.get("/metrics")
async def get_metrics():
    """Prometheus指标端点"""
    return Response(generate_latest(), media_type="text/plain")
```

### 2. 结构化日志

```python
import structlog

logger = structlog.get_logger()

@app.post("/api/v1/events")
async def create_event(event_request: EventRequest):
    """带结构化日志的事件创建接口"""
    logger.info(
        "Event creation requested",
        action=event_request.action,
        source=event_request.source,
        content_length=len(event_request.content)
    )

    try:
        # 处理事件创建
        result = await process_event(event_request)

        logger.info(
            "Event created successfully",
            event_id=result["event_id"],
            processing_time=result["processing_time"]
        )

        return result
    except Exception as e:
        logger.error(
            "Event creation failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

## 总结

OpenHands的事件系统接口设计具有以下特点：

### 控制接口特点
1. **RESTful设计**: 遵循REST原则，提供清晰的API结构
2. **实时通信**: 支持WebSocket实现实时事件流
3. **异步处理**: 全面支持异步操作，提高性能
4. **类型安全**: 使用Pydantic进行数据验证

### 配置接口特点
1. **分层配置**: 系统、代理、运行时分层配置管理
2. **动态更新**: 支持运行时配置更新
3. **验证机制**: 完善的配置验证和错误处理
4. **持久化**: 配置自动持久化和恢复

### 安全和监控
1. **多层安全**: 认证、授权、速率限制、输入验证
2. **全面监控**: 指标收集、结构化日志、性能追踪
3. **错误处理**: 优雅的错误处理和恢复机制
4. **可观测性**: 完整的系统可观测性支持

这些接口为OpenHands提供了强大而灵活的控制和配置能力，支持复杂的AI代理应用场景。
