from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class WalletType(str, Enum):
    """钱包类型枚举"""
    SAVINGS_BOX = "savings_box"
    POCKET_MONEY = "pocket_money"


class TransactionType(str, Enum):
    """交易类型枚举"""
    DEPOSIT = "deposit"        # 转入
    WITHDRAW = "withdraw"      # 转出
    INTEREST = "interest"      # 利息收益
    TRANSFER_IN = "transfer_in"    # 内部转入
    TRANSFER_OUT = "transfer_out"  # 内部转出


class WalletTransaction(BaseModel):
    """钱包交易记录模型
    
    记录所有钱包相关的交易操作，包括：
    - 存取款操作
    - 利息结算
    - 钱包间转账
    
    特性：
    - 完整的交易追溯
    - 记录交易后余额
    - 支持备注说明
    - 优化的查询索引
    """
    __tablename__ = "wallet_transactions"
    
    # 基本字段
    child_id = Column(
        Integer, 
        ForeignKey("children.id", ondelete="CASCADE"), 
        nullable=False,
        comment="小朋友ID"
    )
    
    wallet_type = Column(
        SQLEnum(WalletType),
        nullable=False,
        comment="钱包类型: savings_box/pocket_money"
    )
    
    transaction_type = Column(
        SQLEnum(TransactionType),
        nullable=False,
        comment="交易类型: deposit/withdraw/interest/transfer_in/transfer_out"
    )
    
    amount = Column(
        Numeric(precision=10, scale=2), 
        nullable=False,
        comment="交易金额（正数）"
    )
    
    balance_after = Column(
        Numeric(precision=10, scale=2), 
        nullable=False,
        comment="交易后余额"
    )
    
    remark = Column(
        String(500), 
        nullable=True,
        comment="备注说明"
    )
    
    interest_amount = Column(
        Numeric(precision=10, scale=2), 
        nullable=True,
        comment="利息金额（仅利息交易有效）"
    )
    
    # 关系定义
    child = relationship(
        "Child",
        back_populates="wallet_transactions",
        lazy="selectin"
    )
    
    # 索引定义
    __table_args__ = (
        Index("idx_child_created", "child_id", "created_at"),
        Index("idx_child_wallet", "child_id", "wallet_type"),
        Index("idx_transaction_type", "transaction_type"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<WalletTransaction(id={self.id}, child_id={self.child_id}, "
            f"wallet={self.wallet_type.value}, type={self.transaction_type.value}, "
            f"amount={self.amount})>"
        )