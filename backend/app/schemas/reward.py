from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class RewardBase(BaseModel):
    """Reward基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="奖品名称")
    description: Optional[str] = Field(None, max_length=500, description="奖品描述")
    star_cost: int = Field(..., ge=1, description="所需星星数")


class RewardCreate(RewardBase):
    """创建奖品的请求Schema
    
    对应Laravel的RewardController@store验证规则
    需要包含child_ids数组
    """
    image: Optional[str] = Field(None, description="奖品图片路径")
    child_ids: List[int] = Field(..., min_length=1, description="参与的小朋友ID列表")


class RewardUpdate(BaseModel):
    """更新奖品的请求Schema
    
    对应Laravel的RewardController@update验证规则
    所有字段可选,但已兑换的奖品禁止更新
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="奖品名称")
    description: Optional[str] = Field(None, max_length=500, description="奖品描述")
    star_cost: Optional[int] = Field(None, ge=1, description="所需星星数")
    child_ids: Optional[List[int]] = Field(None, min_length=1, description="参与的小朋友ID列表")


class RedeemAllocation(BaseModel):
    """兑换分配Schema
    
    用于灵活分配各小朋友的扣除数量
    """
    child_id: int = Field(..., description="小朋友ID")
    amount: int = Field(..., ge=0, description="扣除的星星数")


class RewardRedeem(BaseModel):
    """兑换奖品的请求Schema
    
    对应Laravel的RewardController@redeem验证规则
    包含复杂的分配验证逻辑
    """
    deductions: List[RedeemAllocation] = Field(..., min_length=1, description="扣除分配列表")
    
    @field_validator('deductions')
    @classmethod
    def validate_deductions(cls, v):
        """验证扣除列表
        
        - 不能为空
        - 每个child_id只能出现一次
        """
        if not v:
            raise ValueError("分配列表不能为空")
        
        child_ids = [alloc.child_id for alloc in v]
        if len(child_ids) != len(set(child_ids)):
            raise ValueError("每个小朋友只能出现一次")
        
        return v


class ChildProgress(BaseModel):
    """小朋友的进度信息 (用于嵌套)"""
    id: int
    name: str
    star_count: int
    avatar: Optional[str]
    
    class Config:
        from_attributes = True


class RewardResponse(RewardBase):
    """奖品响应Schema
    
    对应Laravel的Reward资源,包含:
    - 基本信息
    - 计算属性: total_stars, is_achieved
    - 兑换状态
    - 参与的小朋友列表
    """
    id: int
    image: Optional[str] = None
    is_redeemed: bool
    redeemed_at: Optional[str] = None
    total_stars: int
    is_achieved: bool
    children: List[ChildProgress]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True