"""
Reward奖品业务逻辑Service
对应Laravel: app/Http/Controllers/RewardController.php
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.models import Reward, Child, RewardChild, StarRecord
from app.schemas.reward import RewardCreate, RewardUpdate, RewardRedeem, RedeemAllocation
from app.services.base_service import BaseService


class RewardService(BaseService[Reward]):
    """Reward奖品业务逻辑Service"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Reward, db)
    
    async def get_all_rewards(self) -> List[Reward]:
        """
        获取所有奖品列表(未兑换优先+计算进度)
        
        对应API: GET /api/rewards
        对应Laravel: RewardController@index
        
        返回顺序:
        1. 未兑换的奖品(按created_at降序)
        2. 已兑换的奖品(按redeemed_at降序)
        
        Returns:
            List[Reward]: 奖品列表(含关联的children和进度计算)
        """
        result = await self.db.execute(
            select(Reward)
            .options(
                selectinload(Reward.reward_children).selectinload(RewardChild.child)
            )
            .order_by(
                Reward.is_redeemed.asc(),  # 未兑换优先
                Reward.redeemed_at.desc(),  # 已兑换按兑换时间降序
                Reward.created_at.desc()    # 未兑换按创建时间降序
            )
        )
        rewards = result.scalars().all()
        return list(rewards)
    
    async def get_reward(self, reward_id: int) -> Optional[Reward]:
        """
        获取单个奖品详情(带关联数据)
        
        对应API: GET /api/rewards/{id}
        
        使用selectinload预加载关系,避免MissingGreenlet错误
        
        Args:
            reward_id: 奖品ID
            
        Returns:
            Optional[Reward]: 奖品对象或None
        """
        result = await self.db.execute(
            select(Reward)
            .options(
                selectinload(Reward.reward_children).selectinload(RewardChild.child)
            )
            .where(Reward.id == reward_id)
        )
        return result.scalar_one_or_none()
    
    async def create_reward(self, data: RewardCreate) -> Reward:
        """
        创建奖品
        
        对应API: POST /api/rewards
        对应Laravel: RewardController@store
        
        业务逻辑:
        1. 验证child_ids对应的小朋友都存在
        2. 创建奖品记录
        3. 创建reward_children关联记录
        
        Args:
            data: 奖品创建数据
            
        Returns:
            Reward: 创建的奖品对象
            
        Raises:
            ValidationError: child_ids为空或小朋友不存在
        """
        # 1. 验证child_ids
        if not data.child_ids:
            raise ValidationError("必须指定至少一个小朋友")
        
        # 2. 验证所有小朋友存在
        result = await self.db.execute(
            select(Child).where(Child.id.in_(data.child_ids))
        )
        children = result.scalars().all()
        
        if len(children) != len(data.child_ids):
            raise ValidationError("部分小朋友不存在")
        
        # 3. 创建奖品
        reward = Reward(
            name=data.name,
            image=data.image,
            star_cost=data.star_cost,
            is_redeemed=False,
            created_at=datetime.now()
        )
        self.db.add(reward)
        await self.db.flush()  # 获取reward.id
        
        # 4. 创建关联记录
        for child_id in data.child_ids:
            reward_child = RewardChild(
                reward_id=reward.id,
                child_id=child_id,
                deduction_amount=0  # 创建时默认为0
            )
            self.db.add(reward_child)
        
        await self.db.commit()
        await self.db.refresh(reward)
        
        return reward
    
    async def update_reward(self, reward_id: int, data: RewardUpdate) -> Reward:
        """
        更新奖品
        
        对应API: PUT /api/rewards/{id}
        对应Laravel: RewardController@update
        
        业务逻辑:
        1. 验证奖品存在且未兑换
        2. 如果提供了child_ids,删除旧关联并创建新关联
        3. 更新奖品信息
        
        Args:
            reward_id: 奖品ID
            data: 更新数据
            
        Returns:
            Reward: 更新后的奖品对象
            
        Raises:
            ResourceNotFoundError: 奖品不存在
            ValidationError: 奖品已兑换,禁止修改
        """
        # 1. 查询奖品
        reward = await self.get_by_id_or_404(reward_id)
        
        # 2. 验证未兑换
        if reward.is_redeemed:
            raise ValidationError("奖品已兑换,无法修改")
        
        # 3. 更新基本信息
        update_data = data.model_dump(exclude_unset=True, exclude={'child_ids'})
        for key, value in update_data.items():
            setattr(reward, key, value)
        
        # 4. 如果提供了child_ids,更新关联
        if data.child_ids is not None:
            if not data.child_ids:
                raise ValidationError("必须指定至少一个小朋友")
            
            # 验证所有小朋友存在
            result = await self.db.execute(
                select(Child).where(Child.id.in_(data.child_ids))
            )
            children = result.scalars().all()
            
            if len(children) != len(data.child_ids):
                raise ValidationError("部分小朋友不存在")
            
            # 删除旧关联
            await self.db.execute(
                RewardChild.__table__.delete().where(
                    RewardChild.reward_id == reward_id
                )
            )
            
            # 创建新关联
            for child_id in data.child_ids:
                reward_child = RewardChild(
                    reward_id=reward_id,
                    child_id=child_id,
                    deduction_amount=0
                )
                self.db.add(reward_child)
        
        await self.db.commit()
        await self.db.refresh(reward)
        
        return reward
    
    async def delete_reward(self, reward_id: int) -> None:
        """
        删除奖品
        
        对应API: DELETE /api/rewards/{id}
        对应Laravel: RewardController@destroy
        
        业务逻辑:
        1. 验证奖品存在且未兑换
        2. 删除关联记录(级联)
        3. 删除奖品
        
        Args:
            reward_id: 奖品ID
            
        Raises:
            ResourceNotFoundError: 奖品不存在
            ValidationError: 奖品已兑换,禁止删除
        """
        # 1. 查询奖品
        reward = await self.get_by_id_or_404(reward_id)
        
        # 2. 验证未兑换
        if reward.is_redeemed:
            raise ValidationError("奖品已兑换,无法删除")
        
        # 3. 删除(级联删除关联记录)
        await self.db.delete(reward)
        await self.db.commit()
    
    async def redeem_reward(self, reward_id: int, data: RewardRedeem) -> Reward:
        """
        兑换奖品
        
        对应API: POST /api/rewards/{id}/redeem
        对应Laravel: RewardController@redeem
        
        业务逻辑(4层验证):
        1. 验证奖品存在且未兑换
        2. 验证deductions中的child_ids都在奖品关联中
        3. 验证总扣除数量等于star_cost
        4. 验证每个小朋友的星星余额充足
        
        事务操作:
        1. 更新reward_children.deduction_amount
        2. 更新children.star_count
        3. 创建星星记录(type=redeem)
        4. 更新reward.is_redeemed和redeemed_at
        
        Args:
            reward_id: 奖品ID
            data: 兑换数据(包含每个小朋友的扣除数量)
            
        Returns:
            Reward: 兑换后的奖品对象
            
        Raises:
            ResourceNotFoundError: 奖品不存在
            ValidationError: 各种验证失败
        """
        # 1. 查询奖品(加载关联的children)
        result = await self.db.execute(
            select(Reward)
            .where(Reward.id == reward_id)
            .options(
                selectinload(Reward.reward_children).selectinload(RewardChild.child)
            )
            .with_for_update()  # 加锁
        )
        reward = result.scalar_one_or_none()
        
        if not reward:
            raise ResourceNotFoundError("Reward", reward_id)
        
        # 2. 验证未兑换
        if reward.is_redeemed:
            raise ValidationError("奖品已兑换")
        
        # 3. 验证deductions中的child_ids都在奖品关联中
        reward_child_ids = {rc.child_id for rc in reward.reward_children}
        deduction_child_ids = {alloc.child_id for alloc in data.deductions}
        
        if not deduction_child_ids.issubset(reward_child_ids):
            raise ValidationError("部分小朋友未关联此奖品")
        
        # 4. 验证总扣除数量
        total_deduction = sum(alloc.amount for alloc in data.deductions)
        if total_deduction != reward.star_cost:
            raise ValidationError(
                f"总扣除数量({total_deduction})必须等于所需星星数({reward.star_cost})"
            )
        
        # 5. 验证每个小朋友的余额(使用加锁查询)
        deduction_map = {alloc.child_id: alloc.amount for alloc in data.deductions}
        
        for reward_child in reward.reward_children:
            if reward_child.child_id in deduction_map:
                deduction = deduction_map[reward_child.child_id]
                child = reward_child.child
                
                if child.star_count < deduction:
                    raise ValidationError(
                        f"小朋友 {child.name} 的星星余额不足"
                        f"(当前: {child.star_count}, 需要: {deduction})"
                    )
        
        # 6. 在事务中执行兑换操作
        try:
            for reward_child in reward.reward_children:
                if reward_child.child_id in deduction_map:
                    deduction = deduction_map[reward_child.child_id]
                    child = reward_child.child
                    
                    # 6.1 更新deduction_amount
                    reward_child.deduction_amount = deduction
                    
                    # 6.2 更新星星余额
                    child.star_count -= deduction
                    
                    # 6.3 创建星星记录
                    star_record = StarRecord(
                        child_id=child.id,
                        type='redeem',
                        amount=deduction,
                        reason=f"兑换奖品: {reward.name}",
                        reward_id=reward.id,
                        created_at=datetime.now()
                    )
                    self.db.add(star_record)
            
            # 6.4 更新奖品状态
            reward.is_redeemed = True
            reward.redeemed_at = datetime.now().isoformat()
            
            # 提交事务
            await self.db.commit()
            
            # 重新加载奖品及关联数据(避免MissingGreenlet)
            result = await self.db.execute(
                select(Reward)
                .where(Reward.id == reward_id)
                .options(
                    selectinload(Reward.reward_children).selectinload(RewardChild.child)
                )
            )
            reward = result.scalar_one()
            
            return reward
        
        except Exception as e:
            # 回滚事务
            await self.db.rollback()
            raise ValidationError(f"兑换失败: {str(e)}")