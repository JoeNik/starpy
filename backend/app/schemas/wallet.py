from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.wallet_transaction import WalletType, TransactionType


class TransactionCreate(BaseModel):
    """创建交易的输入Schema
    
    用于存款、取款等操作的输入验证
    """
    amount: Decimal = Field(
        ...,
        description="交易金额（必须大于0）"
    )
    remark: Optional[str] = Field(
        None,
        max_length=500,
        description="交易备注说明"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """验证金额必须大于0"""
        if v <= 0:
            raise ValueError("金额必须大于0")
        return v


class SavingsBoxResponse(BaseModel):
    """存钱罐响应Schema
    
    包含存钱罐的完整信息和计算属性
    """
    id: int
    child_id: int
    balance: Decimal
    total_interest: Decimal
    interest_rate: Decimal
    last_interest_date: Optional[date]
    today_interest: Decimal = Field(
        description="当日待结算利息（计算属性）"
    )
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PocketMoneyResponse(BaseModel):
    """零花钱响应Schema
    
    包含零花钱的基本信息
    """
    id: int
    child_id: int
    balance: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    """交易记录响应Schema
    
    包含完整的交易记录信息
    """
    id: int
    child_id: int
    wallet_type: str = Field(
        description="钱包类型"
    )
    transaction_type: str = Field(
        description="交易类型"
    )
    amount: Decimal
    balance_after: Decimal
    remark: Optional[str]
    interest_amount: Optional[Decimal]
    created_at: datetime
    
    @field_validator('wallet_type', mode='before')
    @classmethod
    def convert_wallet_type(cls, v) -> str:
        """转换WalletType枚举为字符串"""
        if isinstance(v, WalletType):
            return v.value
        return v
    
    @field_validator('transaction_type', mode='before')
    @classmethod
    def convert_transaction_type(cls, v) -> str:
        """转换TransactionType枚举为字符串"""
        if isinstance(v, TransactionType):
            return v.value
        return v
    
    class Config:
        from_attributes = True


class WalletOverview(BaseModel):
    """钱包总览响应Schema
    
    包含存钱罐、零花钱和最近交易记录的完整信息
    """
    savings_box: Optional[SavingsBoxResponse] = Field(
        None,
        description="存钱罐信息"
    )
    pocket_money: Optional[PocketMoneyResponse] = Field(
        None,
        description="零花钱信息"
    )
    recent_transactions: List[WalletTransactionResponse] = Field(
        default_factory=list,
        description="最近10条交易记录"
    )
    
    @field_validator('recent_transactions', mode='before')
    @classmethod
    def limit_transactions(cls, v):
        """限制最多返回10条交易记录"""
        if v is not None and len(v) > 10:
            return v[:10]
        return v
    
    class Config:
        from_attributes = True