from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class StarRecord(BaseModel):
    """星星记录模型
    
    对应Laravel的StarRecord模型,记录所有星星操作:
    - type: add | subtract | redeem
    - amount: 变动数量(正数为加,负数为减)
    - reason: 操作原因
    - reward_id: 兑换时关联的奖品ID
    """
    __tablename__ = "star_records"
    
    # 基本字段
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, comment="小朋友ID")
    type = Column(String(20), nullable=False, comment="操作类型: add/subtract/redeem")
    amount = Column(Integer, nullable=False, comment="变动数量(正数为加,负数为减)")
    reason = Column(String(500), nullable=True, comment="操作原因")
    reward_id = Column(Integer, ForeignKey("rewards.id", ondelete="SET NULL"), nullable=True, comment="关联奖品ID(兑换时)")
    
    # 关系定义
    child = relationship(
        "Child",
        back_populates="star_records",
        lazy="selectin"
    )
    
    reward = relationship(
        "Reward",
        back_populates="star_records",
        lazy="selectin"
    )
    
    # 索引定义
    __table_args__ = (
        Index("idx_child_created", "child_id", "created_at"),
        Index("idx_child_type", "child_id", "type"),
        Index("idx_reward", "reward_id"),
    )
    
    def __repr__(self) -> str:
        return f"<StarRecord(id={self.id}, child_id={self.child_id}, type='{self.type}', amount={self.amount})>"