"""
OpenHands 服务器依赖注入模块

这个模块定义了FastAPI的依赖注入函数，主要用于：
- API密钥验证
- 会话认证
- 权限检查
- 请求预处理

依赖注入是FastAPI的核心特性，用于在路由处理函数执行前进行通用的验证和处理。
"""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

# 从环境变量获取会话API密钥
_SESSION_API_KEY = os.getenv('SESSION_API_KEY')

# 定义API密钥头部验证器
_SESSION_API_KEY_HEADER = APIKeyHeader(name='X-Session-API-Key', auto_error=False)


def check_session_api_key(
    session_api_key: str | None = Depends(_SESSION_API_KEY_HEADER),
):
    """
    检查会话API密钥

    验证请求头中的X-Session-API-Key是否与环境变量中设置的密钥匹配。
    如果密钥不匹配，抛出401未授权异常。

    Args:
        session_api_key (str | None): 从请求头获取的API密钥

    Raises:
        HTTPException: 当API密钥不匹配时抛出401错误

    Note:
        作为依赖项使用时，会自动出现在OpenAPI文档中
    """
    if session_api_key != _SESSION_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


def get_dependencies() -> list[Depends]:
    """
    获取依赖项列表

    根据配置动态构建依赖项列表。如果设置了SESSION_API_KEY环境变量，
    则添加API密钥检查依赖项。

    Returns:
        list[Depends]: 依赖项列表

    Note:
        这个函数允许根据配置有条件地启用某些依赖项
    """
    result = []
    if _SESSION_API_KEY:
        result.append(Depends(check_session_api_key))
    return result
