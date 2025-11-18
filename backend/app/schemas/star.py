from typing import Optional
from pydantic import BaseModel, Field


class StarAdd(BaseModel):
    """加星操作的请求Schema
    
    对应Laravel的StarController@add验证规则
    """
    amount: int = Field(
        ..., 
        ge=1, 
        le=50, 
        description="加星数量 (1-50)"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=500, 
        description="加星原因"
    )


class StarSubtract(BaseModel):
    """减星操作的请求Schema
    
    对应Laravel的StarController@subtract验证规则
    """
    amount: int = Field(
        ..., 
        ge=1, 
        le=50, 
        description="减星数量 (1-50)"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=500, 
        description="减星原因"
    )