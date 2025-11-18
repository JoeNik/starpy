from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class Reward(BaseModel):
    """奖品模型
    
    对应Laravel的Reward模型,包含:
    - 基本信息: name, description, image, star_cost
    - 状态字段: is_redeemed, redeemed_at
    - 计算属性: total_stars (所有参与小朋友的星星总和)
    - 计算属性: is_achieved (是否达到兑换条件)
    - 关系: reward_children (多对多关联), star_records
    """
    __tablename__ = "rewards"
    
    # 基本字段
    name = Column(String(100), nullable=False, comment="奖品名称")
    description = Column(String(500), nullable=True, comment="奖品描述")
    image = Column(String(255), nullable=True, comment="奖品图片路径")
    star_cost = Column(Integer, nullable=False, comment="所需星星数")
    is_redeemed = Column(Boolean, default=False, nullable=False, comment="是否已兑换")
    redeemed_at = Column(String, nullable=True, comment="兑换时间")
    
    # 关系定义
    reward_children = relationship(
        "RewardChild",
        back_populates="reward",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    star_records = relationship(
        "StarRecord",
        back_populates="reward",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    @property
    def children(self):
        """从reward_children提取children列表
        
        这个属性用于Pydantic序列化,将多对多关系转换为children列表
        
        Returns:
            List[Child]: 参与此奖品的小朋友列表
        """
        return [rc.child for rc in self.reward_children if rc.child]
    
    @property
    def total_stars(self) -> int:
        """计算所有参与小朋友的星星总和
        
        对应Laravel中的getTotalStarsAttribute()方法
        Returns:
            int: 总星星数
        """
        if not self.reward_children:
            return 0
        
        return sum(rc.child.star_count for rc in self.reward_children if rc.child)
    
    @property
    def is_achieved(self) -> bool:
        """判断是否达到兑换条件
        
        对应Laravel中的getIsAchievedAttribute()方法
        Returns:
            bool: 是否可以兑换
        """
        return self.total_stars >= self.star_cost
    
    def __repr__(self) -> str:
        return f"<Reward(id={self.id}, name='{self.name}', required={self.star_cost}, redeemed={self.is_redeemed})>"