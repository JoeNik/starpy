from decimal import Decimal
from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class PocketMoney(BaseModel):
    """零花钱模型
    
    存储小朋友的零花钱余额信息。
    
    特性：
    - 与Child模型一对一关系
    - 简单的余额管理
    - 无利息计算
    """
    __tablename__ = "pocket_money"
    
    # 基本字段
    child_id = Column(
        Integer, 
        ForeignKey("children.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True,
        comment="小朋友ID（唯一）"
    )
    
    balance = Column(
        Numeric(precision=10, scale=2), 
        nullable=False, 
        default=Decimal('0.00'),
        comment="当前余额"
    )
    
    # 关系定义
    child = relationship(
        "Child",
        back_populates="pocket_money",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<PocketMoney(id={self.id}, child_id={self.child_id}, balance={self.balance})>"