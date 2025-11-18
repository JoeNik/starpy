from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ChildBase(BaseModel):
    """Child基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    birthday: date = Field(..., description="生日")
    gender: str = Field(..., pattern="^(male|female)$", description="性别: male/female")


class ChildCreate(ChildBase):
    """创建小朋友的请求Schema
    
    对应Laravel的ChildController@store验证规则
    """
    pass


class ChildUpdate(BaseModel):
    """更新小朋友的请求Schema
    
    对应Laravel的ChildController@update验证规则
    所有字段可选
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    birthday: Optional[date] = Field(None, description="生日")
    gender: Optional[str] = Field(None, pattern="^(male|female)$", description="性别")


class StarRecordSimple(BaseModel):
    """简化的星星记录Schema (用于嵌套)"""
    id: int
    type: str
    amount: int
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RewardSimple(BaseModel):
    """简化的奖品Schema (用于嵌套)"""
    id: int
    name: str
    star_cost: int
    image: Optional[str]
    
    class Config:
        from_attributes = True


class ChildResponse(ChildBase):
    """小朋友响应Schema
    
    对应Laravel的Child资源,包含:
    - 基本信息
    - 计算属性: age
    - 星星数量: star_count
    - 可选: 最近20条记录 (详情页)
    - 可选: 关联的奖品列表 (详情页)
    """
    id: int
    avatar: Optional[str] = None
    star_count: int
    age: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 可选字段 (仅详情页返回)
    star_records: Optional[List[StarRecordSimple]] = None
    rewards: Optional[List[RewardSimple]] = None
    
    @field_validator('star_records', mode='before')
    @classmethod
    def limit_star_records(cls, v):
        """限制最多返回20条记录"""
        if v is not None and len(v) > 20:
            return v[:20]
        return v
    
    class Config:
        from_attributes = True