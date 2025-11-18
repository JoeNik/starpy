"""
泛型基础Service类
提供标准的CRUD操作,其他Service可继承扩展
对应设计模式:Repository Pattern
"""
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError

# 泛型类型变量
ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType]):
    """
    泛型基础Service类
    
    使用示例:
        class ChildService(BaseService[Child]):
            def __init__(self, db: AsyncSession):
                super().__init__(Child, db)
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        初始化Service
        
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据ID查询单条记录
        
        Args:
            id: 记录ID
            
        Returns:
            ModelType: 查询结果,不存在返回None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_or_404(self, id: int) -> ModelType:
        """
        根据ID查询单条记录,不存在抛出404异常
        
        Args:
            id: 记录ID
            
        Returns:
            ModelType: 查询结果
            
        Raises:
            ResourceNotFoundError: 记录不存在
        """
        record = await self.get_by_id(id)
        if not record:
            raise ResourceNotFoundError(self.model.__name__, id)
        return record
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        **filters
    ) -> List[ModelType]:
        """
        查询所有记录(支持分页和过滤)
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            order_by: 排序字段(如'-created_at'表示降序)
            **filters: 过滤条件(如status='active')
            
        Returns:
            List[ModelType]: 记录列表
        """
        query = select(self.model)
        
        # 添加过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        # 添加排序
        if order_by:
            if order_by.startswith('-'):
                # 降序
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                # 升序
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        
        # 分页
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, **filters) -> int:
        """
        统计记录数
        
        Args:
            **filters: 过滤条件
            
        Returns:
            int: 记录总数
        """
        query = select(func.count()).select_from(self.model)
        
        # 添加过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """
        创建新记录
        
        Args:
            obj_data: 记录数据字典
            
        Returns:
            ModelType: 创建的记录
        """
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, id: int, obj_data: Dict[str, Any]) -> ModelType:
        """
        更新记录
        
        Args:
            id: 记录ID
            obj_data: 更新数据字典
            
        Returns:
            ModelType: 更新后的记录
            
        Raises:
            ResourceNotFoundError: 记录不存在
        """
        db_obj = await self.get_by_id_or_404(id)
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: int) -> None:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Raises:
            ResourceNotFoundError: 记录不存在
        """
        db_obj = await self.get_by_id_or_404(id)
        await self.db.delete(db_obj)
        await self.db.commit()
    
    async def exists(self, id: int) -> bool:
        """
        判断记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            bool: 是否存在
        """
        result = await self.db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        count = result.scalar_one()
        return count > 0