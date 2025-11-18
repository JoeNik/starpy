# 星星存折 - FastAPI标准化实施方案

## 🎯 目标

使用FastAPI框架,创建一个**标准化、可复用、生产级**的后端实现,完全替换Laravel后端,保持前端零改动。

---

## 📐 标准化架构设计

### 核心设计原则

1. **分层架构** - 清晰的职责分离
2. **依赖注入** - 松耦合,易测试
3. **类型安全** - 完整的类型提示
4. **异步优先** - 高性能异步处理
5. **可复用性** - 通用组件封装

### 目录结构 (标准版)

```
newpro/
├── backend/                      # Python后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # 应用入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   │
│   │   ├── core/                # 核心基础设施 (可复用)
│   │   │   ├── __init__.py
│   │   │   ├── base_model.py   # 基础模型类
│   │   │   ├── base_service.py # 基础服务类
│   │   │   ├── base_schema.py  # 基础Schema
│   │   │   ├── deps.py         # 依赖注入
│   │   │   ├── response.py     # 统一响应格式
│   │   │   └── exceptions.py   # 自定义异常
│   │   │
│   │   ├── models/              # 数据库模型
│   │   │   ├── __init__.py
│   │   │   ├── child.py
│   │   │   ├── reward.py
│   │   │   ├── star_record.py
│   │   │   └── associations.py # 多对多关联表
│   │   │
│   │   ├── schemas/             # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── child.py
│   │   │   ├── reward.py
│   │   │   └── star.py
│   │   │
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── child_service.py
│   │   │   ├── star_service.py
│   │   │   └── reward_service.py
│   │   │
│   │   ├── api/                 # API路由
│   │   │   ├── __init__.py
│   │   │   ├── deps.py         # 路由依赖
│   │   │   └── v1/             # API版本
│   │   │       ├── __init__.py
│   │   │       ├── children.py
│   │   │       ├── stars.py
│   │   │       └── rewards.py
│   │   │
│   │   ├── utils/               # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── file_handler.py # 文件处理
│   │   │   ├── helpers.py      # 通用辅助
│   │   │   └── validators.py   # 自定义验证
│   │   │
│   │   └── middleware/          # 中间件
│   │       ├── __init__.py
│   │       └── error_handler.py
│   │
│   ├── alembic/                 # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── storage/                 # 文件存储
│   │   ├── avatars/
│   │   ├── rewards/
│   │   └── database.sqlite
│   │
│   ├── tests/                   # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py         # pytest配置
│   │   ├── test_children.py
│   │   ├── test_stars.py
│   │   └── test_rewards.py
│   │
│   ├── .env.example
│   ├── .gitignore
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── pyproject.toml          # 项目配置
│   └── README.md
│
├── frontend/                    # Vue前端 (复用原项目)
│   └── (链接到 ../star/frontend)
│
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
└── README.md
```

---

## 🧱 核心可复用组件

### 1. 基础模型类 (`core/base_model.py`)

```python
"""
可复用的SQLAlchemy基础模型
提供通用字段和方法
"""
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class TimestampMixin:
    """时间戳混入类"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class BaseModel(Base, TimestampMixin):
    """基础模型,包含通用功能"""
    __abstract__ = True
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### 2. 基础服务类 (`core/base_service.py`)

```python
"""
可复用的Service基类
提供标准CRUD操作
"""
from typing import Generic, Type, TypeVar, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.base_model import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """通用Service基类"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """获取单条记录"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[ModelType]:
        """获取所有记录"""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, obj: ModelType) -> ModelType:
        """创建记录"""
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def update(self, obj: ModelType) -> ModelType:
        """更新记录"""
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        """删除记录"""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
```

### 3. 统一响应格式 (`core/response.py`)

```python
"""
统一的API响应格式
与Laravel格式保持一致
"""
from typing import Any, Optional
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    errors: Optional[dict[str, list[str]]] = None
    message: Optional[str] = None


def success_response(
    data: Any = None,
    message: Optional[str] = None
) -> dict:
    """构建成功响应"""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def error_response(
    message: str,
    errors: Optional[dict] = None,
    status_code: int = 400
) -> dict:
    """构建错误响应"""
    response = {
        "success": False,
        "message": message
    }
    if errors:
        response["errors"] = errors
    return response
```

### 4. 自定义异常 (`core/exceptions.py`)

```python
"""
自定义业务异常
"""
from typing import Optional


class AppException(Exception):
    """应用基础异常"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors
        super().__init__(message)


class NotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    """验证异常"""
    
    def __init__(self, message: str, errors: dict):
        super().__init__(
            message,
            status_code=422,
            errors=errors
        )


class BusinessException(AppException):
    """业务逻辑异常"""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)
```

### 5. 文件处理工具 (`utils/file_handler.py`)

```python
"""
标准化的文件上传处理
支持图片验证、存储、删除
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image


class FileHandler:
    """文件处理器"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    MAX_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_image(
        self,
        file: UploadFile,
        subfolder: str = ""
    ) -> str:
        """
        保存图片文件
        返回相对路径
        """
        # 验证文件类型
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {self.ALLOWED_EXTENSIONS}"
            )
        
        # 读取文件
        content = await file.read()
        
        # 验证文件大小
        if len(content) > self.MAX_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {self.MAX_SIZE} bytes"
            )
        
        # 验证是否为有效图片
        try:
            image = Image.open(file.file)
            image.verify()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}{ext}"
        
        # 创建子目录
        save_dir = self.storage_path / subfolder
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = save_dir / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 返回相对路径
        return str(Path(subfolder) / filename)
    
    def delete_file(self, relative_path: str) -> bool:
        """删除文件"""
        try:
            file_path = self.storage_path / relative_path
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"Failed to delete file: {e}")
        return False
    
    def get_url(self, relative_path: Optional[str]) -> Optional[str]:
        """生成访问URL"""
        if not relative_path:
            return None
        return f"/storage/{relative_path}"
```

---

## 🔧 标准化实现细节

### 数据库配置 (`database.py`)

```python
"""
异步数据库配置
使用SQLAlchemy 2.0 + aiosqlite
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from app.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """
    依赖注入: 获取数据库会话
    用法: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 配置管理 (`config.py`)

```python
"""
环境配置管理
使用pydantic-settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "Star Savings API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/database.sqlite"
    
    # 文件存储
    STORAGE_PATH: str = "./storage"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    # 文件上传
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### 主应用入口 (`main.py`)

```python
"""
FastAPI应用入口
配置中间件、路由、异常处理
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import AppException
from app.core.response import error_response
from app.api.v1 import children, stars, rewards


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 静态文件服务
app.mount(
    "/storage",
    StaticFiles(directory=settings.STORAGE_PATH),
    name="storage"
)


# 全局异常处理
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理自定义异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            errors=exc.errors
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal server error"
        )
    )


# 注册路由
app.include_router(
    children.router,
    prefix="/api/children",
    tags=["children"]
)

app.include_router(
    stars.router,
    prefix="/api/children",
    tags=["stars"]
)

app.include_router(
    rewards.router,
    prefix="/api/rewards",
    tags=["rewards"]
)


@app.get("/")
async def root():
    """健康检查"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }
```

---

## 📦 依赖清单 (`requirements.txt`)

```txt
# Web框架
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20

# 数据库
sqlalchemy==2.0.36
aiosqlite==0.20.0
alembic==1.14.0

# 数据验证
pydantic==2.10.5
pydantic-settings==2.7.1

# 图片处理
Pillow==11.1.0

# 工具
python-dotenv==1.0.1

# 测试
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
```

---

## 🔄 数据库迁移策略

### Alembic配置 (`alembic.ini`)

```ini
[alembic]
script_location = alembic
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s
sqlalchemy.url = sqlite+aiosqlite:///./storage/database.sqlite

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

### 迁移命令

```bash
# 创建迁移
alembic revision --autogenerate -m "create children table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 🧪 测试框架 (`tests/conftest.py`)

```python
"""
pytest配置和通用fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db
from app.core.base_model import Base


# 测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """提供测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """提供测试客户端"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

---

## 📝 实施步骤

### 阶段1: 基础搭建 (1-2天)

```bash
# 1. 创建项目目录
mkdir -p newpro/backend
cd newpro/backend

# 2. 初始化Python环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建基础结构
mkdir -p app/{core,models,schemas,services,api/v1,utils,middleware}
mkdir -p storage/{avatars,rewards}
mkdir -p tests

# 5. 配置环境变量
cp .env.example .env
```

### 阶段2: 核心组件 (1天)

- ✅ 实现 [`base_model.py`](star/backend/app/Models/User.php:1)
- ✅ 实现 [`base_service.py`](star/backend/app/Http/Controllers/Controller.php:1)
- ✅ 实现 [`response.py`](star/backend/routes/api.php:1)
- ✅ 实现 [`exceptions.py`](star/backend/app/Http/Controllers/ChildController.php:1)
- ✅ 实现 [`file_handler.py`](star/backend/app/Http/Controllers/ChildController.php:116)

### 阶段3: 数据模型 (1-2天)

- ✅ 实现 [`Child`](star/backend/app/Models/Child.php:1) 模型
- ✅ 实现 [`Reward`](star/backend/app/Models/Reward.php:1) 模型
- ✅ 实现 [`StarRecord`](star/backend/app/Models/StarRecord.php:1) 模型
- ✅ 实现关联表
- ✅ 创建Alembic迁移
- ✅ 编写Schemas

### 阶段4: 服务层 (2天)

- ✅ [`ChildService`](star/backend/app/Http/Controllers/ChildController.php:11) - 小朋友业务逻辑
- ✅ [`StarService`](star/backend/app/Http/Controllers/StarController.php:12) - 星星操作业务逻辑
- ✅ [`RewardService`](star/backend/app/Http/Controllers/RewardController.php:14) - 奖品业务逻辑

### 阶段5: API路由 (2天)

- ✅ Children API
- ✅ Stars API
- ✅ Rewards API
- ✅ 文件上传处理

### 阶段6: 测试与部署 (2天)

- ✅ 单元测试
- ✅ 集成测试
- ✅ Docker配置
- ✅ 文档编写

---

## 🚀 运行方式

### 开发模式

```bash
# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问
# API: http://localhost:8000/api
# 文档: http://localhost:8000/docs
```

### 生产模式 (Docker)

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 访问应用
# 完整应用: http://localhost:8008
```

---

## ✅ 验收标准

### 功能验收
- [ ] 所有API接口功能完整
- [ ] 事务处理正确无误
- [ ] 文件上传下载正常
- [ ] 数据验证准确
- [ ] 错误处理完善

### 性能验收
- [ ] API响应 < 200ms
- [ ] 并发支持 > 100 req/s
- [ ] 内存占用 < 200MB

### 代码质量
- [ ] 类型提示 100%
- [ ] 测试覆盖率 > 80%
- [ ] 符合PEP8规范
- [ ] 文档完整清晰

### 兼容性
- [ ] 前端零改动可用
- [ ] API格式完全兼容
- [ ] 响应格式一致

---

## 🎯 优势总结

### 相比Laravel的提升

1. **性能提升**
   - 异步处理,并发能力更强
   - 内存占用更低
   - 启动速度更快

2. **开发体验**
   - 类型安全,减少bug
   - 自动生成API文档
   - 简洁的异步语法

3. **可维护性**
   - 清晰的分层架构
   - 标准化的代码结构
   - 完善的测试框架

4. **可扩展性**
   - 易于添加新功能
   - 组件高度复用
   - 依赖注入灵活

---

## 📚 参考资料

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0文档](https://docs.sqlalchemy.org/)
- [Pydantic V2文档](https://docs.pydantic.dev/)
- [Alembic文档](https://alembic.sqlalchemy.org/)

---

## 🎉 总结

本方案提供了一个**标准化、可复用、生产级**的FastAPI实现架构,可以直接应用于本项目,也可以作为模板用于其他FastAPI项目开发。

核心特点:
- ✅ 标准的分层架构
- ✅ 可复用的基础组件
- ✅ 完善的类型提示
- ✅ 健全的测试框架
- ✅ 清晰的文档说明
- ✅ 容器化部署

准备好开始实施了吗? 🚀