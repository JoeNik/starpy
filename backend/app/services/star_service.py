"""
Star操作业务逻辑Service
对应Laravel: app/Http/Controllers/StarController.php
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.models import Child, StarRecord
from app.schemas.star import StarAdd, StarSubtract
from app.services.base_service import BaseService


class StarService(BaseService[StarRecord]):
    """Star操作业务逻辑Service"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(StarRecord, db)
    
    async def add_stars(
        self,
        child_id: int,
        data: StarAdd
    ) -> dict:
        """
        给小朋友加星星
        
        对应API: POST /api/children/{id}/stars/add
        对应Laravel: StarController@add
        
        业务逻辑:
        1. 验证小朋友存在
        2. 在事务中:
           - 插入star_records记录
           - 更新children.star_count
        
        Args:
            child_id: 小朋友ID
            data: 加星数据(amount, reason)
            
        Returns:
            dict: 包含更新后的小朋友信息和新增的星星记录
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        # 1. 查询小朋友(加锁,避免并发问题)
        child = await self._get_child_for_update(child_id)
        
        # 2. 在事务中执行操作
        try:
            # 2.1 创建星星记录
            star_record = StarRecord(
                child_id=child_id,
                type='add',
                amount=data.amount,
                reason=data.reason,
                created_at=datetime.now()
            )
            self.db.add(star_record)
            
            # 2.2 更新小朋友星星总数
            child.star_count += data.amount
            
            # 提交事务
            await self.db.commit()
            
            # 刷新对象以获取最新数据
            await self.db.refresh(child)
            await self.db.refresh(star_record)
            
            return {
                "child": child,
                "record": star_record
            }
        
        except Exception as e:
            # 回滚事务
            await self.db.rollback()
            raise ValidationError(f"加星失败: {str(e)}")
    
    async def subtract_stars(
        self,
        child_id: int,
        data: StarSubtract
    ) -> dict:
        """
        给小朋友减星星
        
        对应API: POST /api/children/{id}/stars/subtract
        对应Laravel: StarController@subtract
        
        业务逻辑:
        1. 验证小朋友存在
        2. 验证星星余额充足
        3. 在事务中:
           - 插入star_records记录
           - 更新children.star_count
        
        Args:
            child_id: 小朋友ID
            data: 减星数据(amount, reason)
            
        Returns:
            dict: 包含更新后的小朋友信息和新增的星星记录
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
            ValidationError: 星星余额不足
        """
        # 1. 查询小朋友(加锁)
        child = await self._get_child_for_update(child_id)
        
        # 2. 验证余额
        if child.star_count < data.amount:
            raise ValidationError(
                f"星星余额不足(当前: {child.star_count}, 需要: {data.amount})"
            )
        
        # 3. 在事务中执行操作
        try:
            # 3.1 创建星星记录
            star_record = StarRecord(
                child_id=child_id,
                type='subtract',
                amount=data.amount,
                reason=data.reason,
                created_at=datetime.now()
            )
            self.db.add(star_record)
            
            # 3.2 更新小朋友星星总数
            child.star_count -= data.amount
            
            # 提交事务
            await self.db.commit()
            
            # 刷新对象
            await self.db.refresh(child)
            await self.db.refresh(star_record)
            
            return {
                "child": child,
                "record": star_record
            }
        
        except Exception as e:
            # 回滚事务
            await self.db.rollback()
            raise ValidationError(f"减星失败: {str(e)}")
    
    async def get_records(self, child_id: int) -> list[StarRecord]:
        """
        获取小朋友的星星记录列表
        
        对应API: GET /api/children/{id}/stars
        对应Laravel: StarController@index
        
        业务逻辑:
        1. 验证小朋友存在
        2. 查询该小朋友的所有星星记录
        3. 按创建时间降序排序
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            list[StarRecord]: 星星记录列表
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        from sqlalchemy import select
        
        # 1. 验证小朋友存在
        child_result = await self.db.execute(
            select(Child).where(Child.id == child_id)
        )
        if not child_result.scalar_one_or_none():
            raise ResourceNotFoundError("Child", child_id)
        
        # 2. 查询星星记录
        result = await self.db.execute(
            select(StarRecord)
            .where(StarRecord.child_id == child_id)
            .order_by(StarRecord.created_at.desc())
        )
        records = result.scalars().all()
        
        return list(records)
    
    async def _get_child_for_update(self, child_id: int) -> Child:
        """
        获取小朋友(加行锁)
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            Child: 小朋友对象
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(Child)
            .where(Child.id == child_id)
            .with_for_update()  # 加行锁,避免并发问题
        )
        child = result.scalar_one_or_none()
        
        if not child:
            raise ResourceNotFoundError("Child", child_id)
        
        return child