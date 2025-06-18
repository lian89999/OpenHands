# OpenHands API 接口完整清单

## API 接口分类概览

OpenHands 提供了丰富的 REST API 和 WebSocket 接口，主要分为以下几个类别：

1. **控制接口** - 用于代理控制、对话管理、任务执行
2. **配置接口** - 用于系统设置、用户偏好、密钥管理
3. **文件接口** - 用于文件操作、上传下载、目录浏览
4. **集成接口** - 用于 Git 集成、外部服务连接
5. **监控接口** - 用于健康检查、状态监控、轨迹记录

## 1. 控制接口 (Control APIs)

### 1.1 对话管理接口

#### 创建对话
```http
POST /api/conversations
Content-Type: application/json

{
  "github_token": "string",
  "selected_repository": "string",
  "agent": "string",
  "language": "string",
  "llm_model": "string",
  "llm_api_key": "string"
}
```

#### 获取对话列表
```http
GET /api/conversations?page=1&per_page=10&sort_by=created_at&sort_order=desc
```

#### 获取单个对话
```http
GET /api/conversations/{conversation_id}
```

#### 删除对话
```http
DELETE /api/conversations/{conversation_id}
```

#### 启动对话
```http
POST /api/conversations/{conversation_id}/start
Content-Type: application/json

{
  "task": "string",
  "inputs": {},
  "microagent_name": "string"
}
```

#### 停止对话
```http
POST /api/conversations/{conversation_id}/stop
```

#### 获取记忆提示
```http
GET /api/conversations/{conversation_id}/remember_prompt
```

### 1.2 对话运行时接口

#### 获取运行时配置
```http
GET /api/conversations/{conversation_id}/config
```

#### 获取 VSCode URL
```http
GET /api/conversations/{conversation_id}/vscode-url
```

#### 获取 Web 主机
```http
GET /api/conversations/{conversation_id}/web-hosts
```

### 1.3 WebSocket 控制接口

#### 连接端点
```
ws://localhost:3000/ws
```

#### 事件类型

##### 用户动作事件
```json
{
  "action": "message",
  "args": {
    "content": "用户消息内容",
    "images_urls": ["image_url1", "image_url2"]
  }
}
```

##### 代理控制事件
```json
{
  "action": "start",
  "args": {
    "task": "任务描述"
  }
}
```

```json
{
  "action": "stop",
  "args": {}
}
```

```json
{
  "action": "pause",
  "args": {}
}
```

```json
{
  "action": "resume",
  "args": {}
}
```

##### 文件操作事件
```json
{
  "action": "read",
  "args": {
    "path": "/path/to/file"
  }
}
```

```json
{
  "action": "write",
  "args": {
    "path": "/path/to/file",
    "content": "文件内容"
  }
}
```

##### 命令执行事件
```json
{
  "action": "run",
  "args": {
    "command": "ls -la"
  }
}
```

## 2. 配置接口 (Configuration APIs)

### 2.1 系统设置接口

#### 获取用户设置
```http
GET /api/settings
Authorization: Bearer {jwt_token}
```

响应示例：
```json
{
  "llm_model": "gpt-4o",
  "llm_api_key_set": true,
  "llm_base_url": "https://api.openai.com/v1",
  "agent": "CodeActAgent",
  "language": "en",
  "confirmation_mode": false,
  "security_analyzer": "",
  "search_api_key_set": false,
  "provider_tokens_set": {
    "github": "github.com",
    "gitlab": null
  }
}
```

#### 保存用户设置
```http
POST /api/save-settings
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "llm_model": "gpt-4o",
  "llm_api_key": "sk-...",
  "llm_base_url": "https://api.openai.com/v1",
  "agent": "CodeActAgent",
  "language": "en",
  "confirmation_mode": false,
  "security_analyzer": "default"
}
```

#### 重置设置 (已弃用)
```http
POST /api/reset-settings
```

### 2.2 密钥管理接口

#### 添加 Git 提供商
```http
POST /api/add-git-providers
Content-Type: application/json

{
  "provider": "github",
  "token": "ghp_...",
  "host": "github.com"
}
```

#### 移除提供商令牌
```http
POST /api/unset-provider-tokens
Content-Type: application/json

{
  "providers": ["github", "gitlab"]
}
```

### 2.3 系统选项接口

#### 获取可用模型列表
```http
GET /api/options/models
```

#### 获取可用代理列表
```http
GET /api/options/agents
```

#### 获取安全分析器列表
```http
GET /api/options/security-analyzers
```

#### 获取系统配置
```http
GET /api/options/config
```

响应示例：
```json
{
  "APP_MODE": "oss",
  "FRONTEND_PORT": 3000,
  "BACKEND_PORT": 3001,
  "SANDBOX_RUNTIME_CONTAINER_IMAGE": "ghcr.io/all-hands-ai/runtime:0.14-nikolaik",
  "RUN_AS_OPENHANDS": true,
  "MAX_ITERATIONS": 100,
  "E2B_API_KEY": null,
  "MODAL_API_TOKEN_ID": null,
  "MODAL_API_TOKEN_SECRET": null
}
```

## 3. 文件接口 (File APIs)

### 3.1 文件浏览接口

#### 获取文件列表
```http
GET /api/conversations/{conversation_id}/files?path=/workspace
```

#### 获取文件内容
```http
GET /api/conversations/{conversation_id}/files/content?path=/workspace/file.py
```

#### 获取文件信息
```http
GET /api/conversations/{conversation_id}/files/info?path=/workspace/file.py
```

### 3.2 文件操作接口

#### 上传文件
```http
POST /api/conversations/{conversation_id}/files/upload
Content-Type: multipart/form-data

file: [binary data]
path: /workspace/
```

#### 创建文件
```http
POST /api/conversations/{conversation_id}/files/create
Content-Type: application/json

{
  "path": "/workspace/new_file.py",
  "content": "print('Hello World')"
}
```

#### 删除文件
```http
DELETE /api/conversations/{conversation_id}/files?path=/workspace/file.py
```

### 3.3 目录操作接口

#### 创建目录
```http
POST /api/conversations/{conversation_id}/files/mkdir
Content-Type: application/json

{
  "path": "/workspace/new_directory"
}
```

#### 获取目录结构
```http
GET /api/conversations/{conversation_id}/files/tree?path=/workspace
```

## 4. 集成接口 (Integration APIs)

### 4.1 Git 集成接口

#### 获取用户仓库
```http
GET /api/git/repositories?provider=github
Authorization: Bearer {jwt_token}
```

#### 获取用户信息
```http
GET /api/git/info?provider=github
Authorization: Bearer {jwt_token}
```

#### 搜索仓库
```http
GET /api/git/search/repositories?q=search_term&provider=github
Authorization: Bearer {jwt_token}
```

#### 获取建议任务
```http
GET /api/git/suggested-tasks?repository=owner/repo&provider=github
Authorization: Bearer {jwt_token}
```

#### 获取分支列表
```http
GET /api/git/repository/branches?repository=owner/repo&provider=github
Authorization: Bearer {jwt_token}
```

### 4.2 MCP (Model Context Protocol) 接口

#### MCP 服务端点
```http
GET /mcp/
```

#### MCP 工具调用
```http
POST /mcp/tools/call
Content-Type: application/json

{
  "tool_name": "tool_name",
  "arguments": {}
}
```

## 5. 监控接口 (Monitoring APIs)

### 5.1 健康检查接口

#### 存活检查
```http
GET /api/alive
```

#### 健康状态
```http
GET /api/health
```

#### 服务器信息
```http
GET /api/server_info
```

### 5.2 轨迹记录接口

#### 获取轨迹数据
```http
GET /api/conversations/{conversation_id}/trajectory
```

#### 下载轨迹文件
```http
GET /api/conversations/{conversation_id}/trajectory/download
```

### 5.3 反馈接口

#### 提交反馈
```http
POST /api/submit-feedback
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "feedback_token",
  "polarity": "positive",
  "feedback": "反馈内容"
}
```

### 5.4 安全分析接口

#### 获取安全分析结果
```http
GET /api/conversations/{conversation_id}/security/analysis
```

#### 提交安全扫描
```http
POST /api/conversations/{conversation_id}/security/scan
Content-Type: application/json

{
  "code": "代码内容",
  "language": "python"
}
```

## 6. 认证和授权

### 6.1 JWT 认证

大多数 API 需要 JWT 令牌认证：

```http
Authorization: Bearer {jwt_token}
```

### 6.2 会话 API 密钥

对话相关的 API 需要会话 API 密钥：

```http
X-Session-API-Key: {session_api_key}
```

### 6.3 OAuth 集成

支持 GitHub、GitLab 等平台的 OAuth 认证：

```http
GET /api/auth/github/login
GET /api/auth/gitlab/login
```

## 7. 错误响应格式

### 7.1 标准错误响应

```json
{
  "error": "错误描述",
  "detail": "详细错误信息",
  "status_code": 400
}
```

### 7.2 常见错误代码

- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 认证失败
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `429 Too Many Requests` - 请求频率限制
- `500 Internal Server Error` - 服务器内部错误

## 8. 速率限制

### 8.1 API 限制

- 每用户每分钟最多 100 个请求
- 文件上传限制：默认无限制（可配置）
- WebSocket 连接：每用户最多 5 个并发连接

### 8.2 响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 9. 分页和排序

### 9.1 分页参数

```http
GET /api/conversations?page=1&per_page=10
```

### 9.2 排序参数

```http
GET /api/conversations?sort_by=created_at&sort_order=desc
```

### 9.3 分页响应格式

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "total_pages": 10
  }
}
```

## 10. WebSocket 事件参考

### 10.1 客户端发送事件

| 事件名 | 描述 | 参数 |
|--------|------|------|
| `connect` | 连接建立 | `auth` |
| `action` | 用户动作 | `action`, `args` |
| `disconnect` | 断开连接 | - |

### 10.2 服务器推送事件

| 事件名 | 描述 | 数据格式 |
|--------|------|----------|
| `oh_event` | OpenHands 事件 | `{id, source, message, timestamp}` |
| `error` | 错误事件 | `{message, data}` |
| `status` | 状态更新 | `{status, message}` |

这个 API 参考文档提供了 OpenHands 系统中所有主要接口的详细信息，包括请求格式、响应格式、认证方式和错误处理，为开发者提供了完整的接口使用指南。
