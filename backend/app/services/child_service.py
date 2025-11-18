"""
Child业务逻辑Service
对应Laravel: app/Http/Controllers/ChildController.php
"""
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models import Child, StarRecord, RewardChild
from app.schemas.child import ChildCreate, ChildUpdate
from app.services.base_service import BaseService
from app.utils.file_handler import FileHandler


class ChildService(BaseService[Child]):
    """Child业务逻辑Service"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Child, db)
    
    async def get_all_children(self) -> List[Child]:
        """
        获取所有小朋友列表(按创建时间降序)
        
        对应API: GET /api/children
        对应Laravel: ChildController@index
        
        Returns:
            List[Child]: 小朋友列表
        """
        result = await self.db.execute(
            select(Child).order_by(Child.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_child_detail(self, child_id: int) -> Child:
        """
        获取小朋友详情(含最近20条星星记录和关联奖品)
        
        对应API: GET /api/children/{id}
        对应Laravel: ChildController@show with eager loading
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            Child: 小朋友详情
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        # 使用selectinload预加载关系(避免N+1查询)
        result = await self.db.execute(
            select(Child)
            .where(Child.id == child_id)
            .options(
                selectinload(Child.star_records),
                selectinload(Child.reward_children).selectinload(RewardChild.reward)
            )
        )
        child = result.scalar_one_or_none()
        
        if not child:
            raise ResourceNotFoundError("Child", child_id)
        
        return child
    
    async def create_child(
        self,
        data: ChildCreate,
        avatar_file: Optional[UploadFile] = None
    ) -> Child:
        """
        创建小朋友
        
        对应API: POST /api/children
        对应Laravel: ChildController@store
        
        Args:
            data: 小朋友创建数据
            avatar_file: 头像文件(可选)
            
        Returns:
            Child: 创建的小朋友
        """
        # 1. 处理头像上传
        avatar_path = None
        if avatar_file:
            avatar_path = await FileHandler.save_avatar(avatar_file)
        
        # 2. 创建小朋友记录
        child_data = data.model_dump(exclude={'avatar'})
        child_data['avatar'] = avatar_path
        child_data['star_count'] = 0  # 初始星星数为0
        
        child = Child(**child_data)
        self.db.add(child)
        await self.db.commit()
        await self.db.refresh(child)
        
        return child
    
    async def update_child(
        self,
        child_id: int,
        data: ChildUpdate,
        avatar_file: Optional[UploadFile] = None
    ) -> Child:
        """
        更新小朋友信息
        
        对应API: PUT /api/children/{id}
        对应Laravel: ChildController@update
        
        Args:
            child_id: 小朋友ID
            data: 更新数据
            avatar_file: 新头像文件(可选)
            
        Returns:
            Child: 更新后的小朋友
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        # 1. 查询小朋友
        child = await self.get_by_id_or_404(child_id)
        
        # 2. 处理头像更新
        if avatar_file:
            # 删除旧头像
            if child.avatar:
                await FileHandler.delete_file(child.avatar)
            
            # 保存新头像
            child.avatar = await FileHandler.save_avatar(avatar_file)
        
        # 3. 更新其他字段
        update_data = data.model_dump(exclude_unset=True, exclude={'avatar'})
        for field, value in update_data.items():
            if hasattr(child, field):
                setattr(child, field, value)
        
        await self.db.commit()
        await self.db.refresh(child)
        
        return child
    
    async def delete_child(self, child_id: int) -> None:
        """
        删除小朋友(级联删除相关记录)
        
        对应API: DELETE /api/children/{id}
        对应Laravel: ChildController@destroy
        
        Args:
            child_id: 小朋友ID
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        # 1. 查询小朋友
        child = await self.get_by_id_or_404(child_id)
        
        # 2. 删除头像文件
        if child.avatar:
            await FileHandler.delete_file(child.avatar)
        
        # 3. 删除数据库记录(SQLAlchemy会自动级联删除star_records和reward_children)
        await self.db.delete(child)
        await self.db.commit()
    
    async def get_star_records(
        self,
        child_id: int,
        limit: int = 20
    ) -> List[StarRecord]:
        """
        获取小朋友的星星记录
        
        Args:
            child_id: 小朋友ID
            limit: 返回记录数(默认20)
            
        Returns:
            List[StarRecord]: 星星记录列表
        """
        # 验证小朋友存在
        await self.get_by_id_or_404(child_id)
        
        result = await self.db.execute(
            select(StarRecord)
            .where(StarRecord.child_id == child_id)
            .order_by(StarRecord.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())