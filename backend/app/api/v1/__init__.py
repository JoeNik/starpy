"""
API v1版本路由

统一导入所有v1路由,在main.py中注册
"""
from fastapi import APIRouter

from app.api.v1 import children, stars, rewards

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(children.router, prefix="/children", tags=["Children"])
api_router.include_router(stars.router, prefix="/children", tags=["Stars"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["Rewards"])

__all__ = ["api_router"]