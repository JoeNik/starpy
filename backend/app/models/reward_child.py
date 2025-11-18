from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class RewardChild(BaseModel):
    """奖品-小朋友关联表模型
    
    对应Laravel的reward_children中间表,实现多对多关系:
    - reward_id: 奖品ID
    - child_id: 小朋友ID
    - deduction_amount: 兑换时从该小朋友扣除的星星数
    
    这是一个pivot表,但包含额外的deduction_amount字段
    用于记录灵活分配的兑换数量
    """
    __tablename__ = "reward_children"
    
    # 外键字段
    reward_id = Column(
        Integer, 
        ForeignKey("rewards.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="奖品ID"
    )
    
    child_id = Column(
        Integer, 
        ForeignKey("children.id", ondelete="CASCADE"), 
        nullable=False, 
        comment="小朋友ID"
    )
    
    # Pivot字段
    deduction_amount = Column(
        Integer, 
        default=0, 
        nullable=False, 
        comment="兑换时扣除的星星数"
    )
    
    # 关系定义
    reward = relationship(
        "Reward",
        back_populates="reward_children",
        lazy="selectin"
    )
    
    child = relationship(
        "Child",
        back_populates="reward_children",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<RewardChild(reward_id={self.reward_id}, child_id={self.child_id}, deduction={self.deduction_amount})>"