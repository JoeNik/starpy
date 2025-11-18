"""
API依赖注入

提供数据库会话等通用依赖
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    FastAPI依赖注入,每个请求创建新的会话,请求结束后关闭
    
    Yields:
        AsyncSession: 数据库会话
    """
    async with AsyncSessionLocal() as session:
        yield session