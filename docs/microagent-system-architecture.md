# OpenHands 微代理系统架构文档

## 概述

OpenHands的微代理(Microagent)系统是一个模块化的AI代理增强框架，通过提供特定领域的知识和指导来扩展AI代理的能力。本文档详细介绍微代理系统的技术架构、核心组件、设计模式和技术栈。

## 核心架构

### 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OpenHands 微代理系统                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        微代理类型层                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │ │
│  │  │   知识      │  │    仓库     │  │    任务     │                     │ │
│  │  │  微代理     │  │   微代理    │  │   微代理    │                     │ │
│  │  │(Knowledge)  │  │   (Repo)    │  │   (Task)    │                     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│           │                       │                       │                │
│           ▼                       ▼                       ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        微代理管理层                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │   加载器    │  │   验证器    │  │   注册器    │  │   触发器    │   │ │
│  │  │  (Loader)   │  │(Validator)  │  │(Registry)   │  │ (Trigger)   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│           │                       │                       │                │
│           ▼                       ▼                       ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        数据处理层                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │ Frontmatter │  │   Jinja2    │  │   Pydantic  │  │    正则     │   │ │
│  │  │   解析器    │  │   模板      │  │   验证      │  │   表达式    │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│           │                       │                       │                │
│           ▼                       ▼                       ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        存储层                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │ │
│  │  │  Markdown   │  │   元数据    │  │    MCP      │                     │ │
│  │  │    文件     │  │    存储     │  │   配置      │                     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. 技术栈组成

#### 核心技术
- **Python 3.12+**: 主要开发语言
- **Pydantic**: 数据验证和序列化
- **python-frontmatter**: Markdown frontmatter解析
- **Jinja2**: 模板引擎（用于提示词生成）
- **pathlib**: 文件路径处理

#### 数据格式
- **Markdown**: 微代理内容格式
- **YAML**: Frontmatter元数据格式
- **JSON**: 配置和数据交换格式

#### 设计模式
- **工厂模式**: 微代理类型创建
- **策略模式**: 不同类型微代理的处理策略
- **模板方法模式**: 微代理加载流程
- **观察者模式**: 触发词匹配机制

## 核心组件

### 1. 微代理类型系统

#### 1.1 MicroagentType枚举

```python
class MicroagentType(str, Enum):
    """微代理类型枚举"""

    KNOWLEDGE = 'knowledge'      # 知识微代理
    REPO_KNOWLEDGE = 'repo'      # 仓库微代理
    TASK = 'task'               # 任务微代理
```

**特点**:
- 类型安全的枚举定义
- 支持字符串比较
- 明确的语义分类

#### 1.2 元数据模型

```python
class MicroagentMetadata(BaseModel):
    """微代理元数据模型"""

    name: str = 'default'
    type: MicroagentType = Field(default=MicroagentType.REPO_KNOWLEDGE)
    version: str = Field(default='1.0.0')
    agent: str = Field(default='CodeActAgent')
    triggers: list[str] = []
    inputs: list[InputMetadata] = []
    mcp_tools: MCPConfig | None = None
```

**功能**:
- Pydantic数据验证
- 默认值处理
- 类型转换和验证
- 扩展性支持

### 2. 微代理基类架构

#### 2.1 BaseMicroagent

```python
class BaseMicroagent(BaseModel):
    """微代理基类"""

    name: str
    content: str
    metadata: MicroagentMetadata
    source: str
    type: MicroagentType

    @classmethod
    def load(cls, path, microagent_dir=None, file_content=None):
        """从文件加载微代理"""
```

**设计特点**:
- 统一的接口定义
- 工厂方法模式
- 类型推断机制
- 错误处理和验证

#### 2.2 加载流程

```python
def load_microagent_flow():
    """微代理加载流程"""

    # 1. 文件读取
    content = read_markdown_file(path)

    # 2. Frontmatter解析
    parsed = frontmatter.load(content)
    metadata_dict = parsed.metadata
    content = parsed.content

    # 3. 元数据验证
    metadata = MicroagentMetadata(**metadata_dict)

    # 4. 类型推断
    inferred_type = infer_microagent_type(metadata)

    # 5. 子类创建
    agent_class = get_microagent_class(inferred_type)
    return agent_class(name=name, content=content, metadata=metadata)
```

### 3. 微代理子类实现

#### 3.1 KnowledgeMicroagent

```python
class KnowledgeMicroagent(BaseMicroagent):
    """知识微代理"""

    def match_trigger(self, message: str) -> str | None:
        """匹配触发词"""
        message = message.lower()
        for trigger in self.triggers:
            if trigger.lower() in message:
                return trigger
        return None

    @property
    def triggers(self) -> list[str]:
        """获取触发词列表"""
        return self.metadata.triggers
```

**特点**:
- 关键词触发机制
- 不区分大小写匹配
- 灵活的触发条件

#### 3.2 RepoMicroagent

```python
class RepoMicroagent(BaseMicroagent):
    """仓库微代理"""

    def __init__(self, **data):
        super().__init__(**data)
        if self.type != MicroagentType.REPO_KNOWLEDGE:
            raise ValueError("Type mismatch")
```

**特点**:
- 始终激活状态
- 仓库特定上下文
- 项目级别的指导

#### 3.3 TaskMicroagent

```python
class TaskMicroagent(KnowledgeMicroagent):
    """任务微代理"""

    def extract_variables(self, content: str) -> list[str]:
        """提取变量"""
        pattern = r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        return re.findall(pattern, content)

    def requires_user_input(self) -> bool:
        """检查是否需要用户输入"""
        variables = self.extract_variables(self.content)
        return len(variables) > 0
```

**特点**:
- 变量替换支持
- 用户交互机制
- 动态参数收集

### 4. 微代理发现和加载

#### 4.1 目录扫描

```python
def load_microagents_from_dir(microagent_dir):
    """从目录加载微代理"""

    repo_agents = {}
    knowledge_agents = {}

    for file in microagent_dir.rglob('*.md'):
        if file.name == 'README.md':
            continue

        try:
            agent = BaseMicroagent.load(file, microagent_dir)

            if isinstance(agent, RepoMicroagent):
                repo_agents[agent.name] = agent
            elif isinstance(agent, KnowledgeMicroagent):
                knowledge_agents[agent.name] = agent

        except Exception as e:
            logger.error(f"Failed to load {file}: {e}")

    return repo_agents, knowledge_agents
```

**功能**:
- 递归目录扫描
- 自动类型分类
- 错误处理和日志
- 批量加载机制

#### 4.2 文件格式支持

```markdown
---
name: python-best-practices
type: knowledge
version: 1.0.0
triggers:
  - python
  - pep8
  - coding standards
---

# Python Best Practices

This microagent provides guidance on Python coding standards and best practices.

## Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Write docstrings for functions and classes
```

**特点**:
- YAML frontmatter元数据
- Markdown内容格式
- 灵活的配置选项

## 数据流和处理

### 1. 微代理激活流程

```
用户消息 → 触发词检测 → 微代理匹配 → 内容注入 → 代理增强
    ↓
关键词分析 → 模式匹配 → 微代理选择 → 上下文合并 → 提示词生成
```

### 2. 变量处理流程

```
模板内容 → 变量提取 → 用户输入 → 变量替换 → 最终内容
    ↓
正则匹配 → 参数收集 → 交互界面 → 值替换 → 内容生成
```

### 3. 类型推断逻辑

```python
def infer_microagent_type(metadata):
    """推断微代理类型"""

    if metadata.inputs:
        # 有输入参数 → 任务微代理
        return MicroagentType.TASK
    elif metadata.triggers:
        # 有触发词 → 知识微代理
        return MicroagentType.KNOWLEDGE
    else:
        # 无触发词 → 仓库微代理（始终激活）
        return MicroagentType.REPO_KNOWLEDGE
```

## 设计模式应用

### 1. 工厂模式

```python
class MicroagentFactory:
    """微代理工厂"""

    _type_map = {
        MicroagentType.KNOWLEDGE: KnowledgeMicroagent,
        MicroagentType.REPO_KNOWLEDGE: RepoMicroagent,
        MicroagentType.TASK: TaskMicroagent,
    }

    @classmethod
    def create(cls, microagent_type: MicroagentType, **kwargs):
        """创建微代理实例"""
        agent_class = cls._type_map.get(microagent_type)
        if not agent_class:
            raise ValueError(f"Unknown microagent type: {microagent_type}")
        return agent_class(**kwargs)
```

### 2. 策略模式

```python
class TriggerStrategy:
    """触发策略接口"""

    def match(self, message: str, triggers: list[str]) -> str | None:
        raise NotImplementedError

class KeywordTriggerStrategy(TriggerStrategy):
    """关键词触发策略"""

    def match(self, message: str, triggers: list[str]) -> str | None:
        message = message.lower()
        for trigger in triggers:
            if trigger.lower() in message:
                return trigger
        return None

class RegexTriggerStrategy(TriggerStrategy):
    """正则表达式触发策略"""

    def match(self, message: str, triggers: list[str]) -> str | None:
        for trigger in triggers:
            if re.search(trigger, message, re.IGNORECASE):
                return trigger
        return None
```

### 3. 模板方法模式

```python
class MicroagentProcessor:
    """微代理处理器模板"""

    def process(self, microagent: BaseMicroagent, context: dict):
        """处理微代理的模板方法"""

        # 1. 预处理
        self.preprocess(microagent, context)

        # 2. 内容处理
        content = self.process_content(microagent, context)

        # 3. 后处理
        return self.postprocess(content, context)

    def preprocess(self, microagent, context):
        """预处理（子类可重写）"""
        pass

    def process_content(self, microagent, context):
        """内容处理（抽象方法）"""
        raise NotImplementedError

    def postprocess(self, content, context):
        """后处理（子类可重写）"""
        return content
```

### 4. 观察者模式

```python
class MicroagentEventManager:
    """微代理事件管理器"""

    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        """订阅事件"""
        self.observers.append(observer)

    def notify(self, event_type: str, microagent: BaseMicroagent):
        """通知观察者"""
        for observer in self.observers:
            observer.on_microagent_event(event_type, microagent)

class MicroagentLogger:
    """微代理日志观察者"""

    def on_microagent_event(self, event_type: str, microagent: BaseMicroagent):
        logger.info(f"Microagent {event_type}: {microagent.name}")

class MicroagentMetrics:
    """微代理指标观察者"""

    def on_microagent_event(self, event_type: str, microagent: BaseMicroagent):
        self.record_metric(f"microagent.{event_type}", microagent.type)
```

## 扩展机制

### 1. 自定义微代理类型

```python
class CustomMicroagent(BaseMicroagent):
    """自定义微代理"""

    def __init__(self, **data):
        super().__init__(**data)
        # 自定义初始化逻辑

    def custom_method(self):
        """自定义方法"""
        pass

# 注册自定义类型
MicroagentFactory.register_type('custom', CustomMicroagent)
```

### 2. 插件系统

```python
class MicroagentPlugin:
    """微代理插件接口"""

    def on_load(self, microagent: BaseMicroagent):
        """加载时回调"""
        pass

    def on_trigger(self, microagent: BaseMicroagent, message: str):
        """触发时回调"""
        pass

class AnalyticsMicroagentPlugin(MicroagentPlugin):
    """分析插件"""

    def on_trigger(self, microagent: BaseMicroagent, message: str):
        # 记录使用统计
        analytics.track('microagent_triggered', {
            'name': microagent.name,
            'type': microagent.type,
            'trigger': microagent.match_trigger(message)
        })
```

### 3. 配置扩展

```python
class ExtendedMicroagentMetadata(MicroagentMetadata):
    """扩展的微代理元数据"""

    # 新增字段
    category: str = 'general'
    tags: list[str] = []
    priority: int = 0
    enabled: bool = True

    # 自定义配置
    custom_config: dict = {}
```

## 性能优化

### 1. 懒加载机制

```python
class LazyMicroagentLoader:
    """懒加载微代理加载器"""

    def __init__(self, microagent_dir: Path):
        self.microagent_dir = microagent_dir
        self._cache = {}
        self._metadata_cache = {}

    def get_microagent(self, name: str) -> BaseMicroagent:
        """获取微代理（懒加载）"""
        if name not in self._cache:
            self._cache[name] = self._load_microagent(name)
        return self._cache[name]

    def get_metadata(self, name: str) -> MicroagentMetadata:
        """获取元数据（仅解析frontmatter）"""
        if name not in self._metadata_cache:
            self._metadata_cache[name] = self._load_metadata_only(name)
        return self._metadata_cache[name]
```

### 2. 缓存策略

```python
from functools import lru_cache

class CachedMicroagentManager:
    """带缓存的微代理管理器"""

    @lru_cache(maxsize=100)
    def match_triggers(self, message: str) -> list[str]:
        """缓存触发词匹配结果"""
        matched = []
        for agent in self.knowledge_agents.values():
            trigger = agent.match_trigger(message)
            if trigger:
                matched.append(agent.name)
        return matched

    def invalidate_cache(self):
        """清除缓存"""
        self.match_triggers.cache_clear()
```

### 3. 批量处理

```python
class BatchMicroagentProcessor:
    """批量微代理处理器"""

    def process_batch(self, microagents: list[BaseMicroagent], context: dict):
        """批量处理微代理"""
        results = []

        # 按类型分组
        grouped = self.group_by_type(microagents)

        # 批量处理每种类型
        for microagent_type, agents in grouped.items():
            processor = self.get_processor(microagent_type)
            batch_results = processor.process_batch(agents, context)
            results.extend(batch_results)

        return results
```

## 安全和验证

### 1. 内容验证

```python
class MicroagentValidator:
    """微代理验证器"""

    def validate_content(self, content: str) -> bool:
        """验证内容安全性"""

        # 检查恶意代码
        if self.contains_malicious_code(content):
            return False

        # 检查敏感信息
        if self.contains_sensitive_info(content):
            return False

        # 检查内容长度
        if len(content) > self.max_content_length:
            return False

        return True

    def contains_malicious_code(self, content: str) -> bool:
        """检查恶意代码"""
        dangerous_patterns = [
            r'import\s+os',
            r'subprocess\.',
            r'eval\s*\(',
            r'exec\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                return True
        return False
```

### 2. 权限控制

```python
class MicroagentPermissionManager:
    """微代理权限管理器"""

    def __init__(self):
        self.permissions = {}

    def check_permission(self, microagent: BaseMicroagent, action: str) -> bool:
        """检查权限"""
        agent_permissions = self.permissions.get(microagent.name, set())
        return action in agent_permissions

    def grant_permission(self, microagent_name: str, action: str):
        """授予权限"""
        if microagent_name not in self.permissions:
            self.permissions[microagent_name] = set()
        self.permissions[microagent_name].add(action)
```

### 3. 沙箱执行

```python
class SandboxedMicroagentExecutor:
    """沙箱化微代理执行器"""

    def execute_safely(self, microagent: BaseMicroagent, context: dict):
        """安全执行微代理"""

        # 创建受限环境
        restricted_context = self.create_restricted_context(context)

        # 设置资源限制
        with self.resource_limits():
            try:
                return self.execute(microagent, restricted_context)
            except Exception as e:
                logger.error(f"Microagent execution failed: {e}")
                return None

    def create_restricted_context(self, context: dict) -> dict:
        """创建受限上下文"""
        # 移除敏感信息
        safe_context = {k: v for k, v in context.items()
                       if not self.is_sensitive_key(k)}
        return safe_context
```

## 监控和调试

### 1. 执行跟踪

```python
class MicroagentTracer:
    """微代理执行跟踪器"""

    def __init__(self):
        self.traces = []

    def trace_execution(self, microagent: BaseMicroagent, context: dict):
        """跟踪执行"""
        trace = {
            'timestamp': datetime.now(),
            'microagent': microagent.name,
            'type': microagent.type,
            'context_keys': list(context.keys()),
            'content_length': len(microagent.content)
        }
        self.traces.append(trace)

    def get_execution_stats(self) -> dict:
        """获取执行统计"""
        return {
            'total_executions': len(self.traces),
            'by_type': self.group_by_type(),
            'by_microagent': self.group_by_microagent(),
            'recent_activity': self.get_recent_activity()
        }
```

### 2. 性能监控

```python
class MicroagentPerformanceMonitor:
    """微代理性能监控器"""

    def __init__(self):
        self.metrics = {}

    def measure_execution_time(self, microagent_name: str):
        """测量执行时间"""
        return self.timer_context(f"microagent.{microagent_name}.execution_time")

    def record_memory_usage(self, microagent_name: str, memory_mb: float):
        """记录内存使用"""
        self.metrics[f"microagent.{microagent_name}.memory_usage"] = memory_mb

    def get_performance_report(self) -> dict:
        """获取性能报告"""
        return {
            'execution_times': self.get_execution_times(),
            'memory_usage': self.get_memory_usage(),
            'error_rates': self.get_error_rates()
        }
```

### 3. 调试工具

```python
class MicroagentDebugger:
    """微代理调试器"""

    def debug_trigger_matching(self, message: str, microagents: list[BaseMicroagent]):
        """调试触发词匹配"""
        results = []
        for agent in microagents:
            if hasattr(agent, 'match_trigger'):
                trigger = agent.match_trigger(message)
                results.append({
                    'agent': agent.name,
                    'matched_trigger': trigger,
                    'all_triggers': agent.triggers
                })
        return results

    def debug_variable_extraction(self, microagent: TaskMicroagent):
        """调试变量提取"""
        variables = microagent.extract_variables(microagent.content)
        return {
            'extracted_variables': variables,
            'requires_input': microagent.requires_user_input(),
            'content_preview': microagent.content[:200] + '...'
        }
```

## 最佳实践

### 1. 微代理设计原则

1. **单一职责**: 每个微代理专注于特定领域
2. **松耦合**: 微代理之间相互独立
3. **可组合**: 支持多个微代理组合使用
4. **可测试**: 提供清晰的测试接口
5. **可扩展**: 支持功能扩展和定制

### 2. 内容编写指南

```markdown
---
name: react-hooks
type: knowledge
version: 1.0.0
triggers:
  - react hooks
  - useState
  - useEffect
---

# React Hooks Best Practices

## useState Hook
- Use descriptive state variable names
- Initialize state with appropriate default values
- Avoid complex objects in state when possible

## useEffect Hook
- Always include dependency array
- Clean up side effects in return function
- Separate concerns into multiple useEffect calls
```

### 3. 性能优化建议

1. **内容优化**: 保持微代理内容简洁明了
2. **触发词优化**: 使用精确的触发词避免误触发
3. **缓存策略**: 合理使用缓存减少重复加载
4. **懒加载**: 按需加载微代理内容
5. **批量处理**: 对相似操作进行批量处理

### 4. 安全注意事项

1. **内容审查**: 定期审查微代理内容
2. **权限控制**: 实施适当的权限管理
3. **输入验证**: 验证所有用户输入
4. **沙箱执行**: 在受限环境中执行
5. **监控日志**: 记录所有重要操作

## 总结

OpenHands的微代理系统具有以下特点：

### 技术优势
1. **模块化设计**: 清晰的类型分层和组件分离
2. **类型安全**: Pydantic确保数据类型安全
3. **灵活扩展**: 支持自定义微代理类型和插件
4. **高性能**: 懒加载和缓存优化

### 架构特色
1. **工厂模式**: 统一的微代理创建机制
2. **策略模式**: 灵活的触发和处理策略
3. **模板方法**: 标准化的处理流程
4. **观察者模式**: 事件驱动的扩展机制

### 应用价值
1. **知识增强**: 为AI代理提供专业领域知识
2. **上下文感知**: 提供项目和仓库特定指导
3. **交互式任务**: 支持用户参与的复杂任务
4. **可维护性**: 模块化的知识管理和更新

这个微代理系统为OpenHands提供了强大的知识增强能力，使AI代理能够在特定领域表现出更专业的能力。
