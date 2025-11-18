"""
FastAPI应用主入口
对应Laravel: public/index.php

启动方式:
- 开发环境: uvicorn main:app --reload
- 生产环境: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic_core import ValidationError as PydanticValidationError

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppException, NotFoundError, ValidationError, ResourceNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库
    """
    # 启动时执行
    print("=" * 50)
    print("Starting FastAPI application...")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Debug mode: {settings.APP_DEBUG}")
    print("=" * 50)
    
    # 初始化数据库
    await init_db()
    print("✓ Database initialized")
    
    yield
    
    # 关闭时执行
    print("Shutting down FastAPI application...")


# 创建FastAPI应用实例
app = FastAPI(
    title="星星存折 API",
    description="儿童奖励系统后端API - Python FastAPI实现",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.APP_DEBUG else None,
    redoc_url="/api/redoc" if settings.APP_DEBUG else None,
)


# ==================== 中间件配置 ====================

# CORS配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义应用异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message}
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """处理404异常"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "message": exc.message}
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
    """处理资源未找到异常"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "message": exc.detail}
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """处理验证异常"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理Pydantic请求验证异常"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "请求参数验证失败", "errors": errors}
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """处理Pydantic核心验证异常(在endpoint内部初始化schema时抛出)"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "数据验证失败", "errors": errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    import traceback
    
    # 开发环境打印详细错误
    if settings.APP_DEBUG:
        print("=" * 50)
        print("UNHANDLED EXCEPTION:")
        print(traceback.format_exc())
        print("=" * 50)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False, 
                "message": f"服务器内部错误: {str(exc)}",
                "traceback": traceback.format_exc()
            }
        )
    
    # 生产环境隐藏错误细节
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "服务器内部错误"}
    )


# ==================== 路由注册 ====================

# 注册API v1路由
app.include_router(api_router, prefix="/api")

# 挂载静态文件服务(用于访问上传的图片)
# 对应Laravel: php artisan storage:link
app.mount(
    "/storage",
    StaticFiles(directory=settings.STORAGE_PATH),
    name="storage"
)

# 挂载静态文件服务(用于访问上传的图片)
# 对应Laravel: php artisan storage:link
app.mount(
    "/storage",
    StaticFiles(directory=settings.STORAGE_PATH),
    name="storage"
)


# ==================== 根路径 ====================

@app.get("/")
async def root():
    """
    根路径 - 健康检查
    """
    return {
        "success": True,
        "message": "星星存折 API v2.0 (FastAPI)",
        "docs": "/api/docs" if settings.APP_DEBUG else "文档已禁用"
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_DEBUG,
        log_level="info"
    )