"""
OpenHands FastAPI 应用程序主文件

这个文件定义了OpenHands的主要FastAPI应用程序，包括：
- 应用程序生命周期管理
- 路由注册和API端点配置
- MCP (Model Context Protocol) 服务器集成
- 中间件和依赖注入设置

技术栈：
- FastAPI: 现代化的Python Web框架
- asyncio: 异步编程支持
- Pydantic: 数据验证和序列化
- MCP: 模型上下文协议支持
"""

import contextlib
import warnings
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi.routing import Mount

# 忽略导入时的警告信息
with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
)

# 导入代理中心以注册所有可用的代理
import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands import __version__

# 导入所有API路由模块
from openhands.server.routes.conversation import (
    app as conversation_api_router,  # 对话API
)
from openhands.server.routes.feedback import app as feedback_api_router  # 反馈API
from openhands.server.routes.files import app as files_api_router  # 文件操作API
from openhands.server.routes.git import app as git_api_router  # Git操作API
from openhands.server.routes.health import add_health_endpoints  # 健康检查端点
from openhands.server.routes.manage_conversations import (  # 对话管理API
    app as manage_conversation_api_router,
)
from openhands.server.routes.mcp import mcp_server  # MCP服务器
from openhands.server.routes.public import app as public_api_router  # 公共API
from openhands.server.routes.secrets import app as secrets_router  # 密钥管理API
from openhands.server.routes.security import app as security_api_router  # 安全API
from openhands.server.routes.settings import app as settings_router  # 设置API
from openhands.server.routes.trajectory import app as trajectory_router  # 轨迹API
from openhands.server.shared import conversation_manager  # 共享对话管理器

# 创建MCP HTTP应用程序
mcp_app = mcp_server.http_app(path='/mcp')


def combine_lifespans(*lifespans):
    """
    组合多个生命周期管理器

    将多个异步上下文管理器组合成一个统一的生命周期管理器，
    用于管理应用程序启动和关闭时的资源初始化和清理。

    Args:
        *lifespans: 多个生命周期管理器函数

    Returns:
        function: 组合后的生命周期管理器

    Note:
        使用AsyncExitStack确保所有生命周期管理器都能正确启动和关闭
    """

    @contextlib.asynccontextmanager
    async def combined_lifespan(app):
        """组合生命周期的内部实现"""
        async with contextlib.AsyncExitStack() as stack:
            # 依次进入所有生命周期上下文
            for lifespan in lifespans:
                await stack.enter_async_context(lifespan(app))
            yield

    return combined_lifespan


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    应用程序生命周期管理器

    管理FastAPI应用程序的启动和关闭过程，主要负责：
    - 对话管理器的初始化和清理
    - 数据库连接的建立和关闭
    - 后台任务的启动和停止

    Args:
        app (FastAPI): FastAPI应用程序实例

    Yields:
        None: 应用程序运行期间
    """
    # 启动对话管理器
    async with conversation_manager:
        yield  # 应用程序运行期间
    # 对话管理器会在退出时自动清理资源


# 创建FastAPI应用程序实例
app = FastAPI(
    title='OpenHands',  # 应用程序标题
    description='OpenHands: Code Less, Make More',  # 应用程序描述
    version=__version__,  # 版本号
    lifespan=combine_lifespans(_lifespan, mcp_app.lifespan),  # 组合生命周期管理器
    routes=[Mount(path='/mcp', app=mcp_app)],  # 挂载MCP应用程序
)

# 注册所有API路由
# 注意：路由注册的顺序很重要，更具体的路由应该先注册

app.include_router(public_api_router)  # 公共API路由
app.include_router(files_api_router)  # 文件操作API路由
app.include_router(security_api_router)  # 安全API路由
app.include_router(feedback_api_router)  # 反馈API路由
app.include_router(conversation_api_router)  # 对话API路由
app.include_router(manage_conversation_api_router)  # 对话管理API路由
app.include_router(settings_router)  # 设置API路由
app.include_router(secrets_router)  # 密钥管理API路由
app.include_router(git_api_router)  # Git操作API路由
app.include_router(trajectory_router)  # 轨迹API路由

# 添加健康检查端点
add_health_endpoints(app)
