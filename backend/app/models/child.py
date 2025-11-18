from datetime import date
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class Child(BaseModel):
    """小朋友模型
    
    对应Laravel的Child模型,包含:
    - 基本信息: name, birthday, gender, avatar
    - 星星数量冗余字段: star_count
    - 计算属性: age (根据生日自动计算)
    - 关系: star_records, rewards (多对多通过reward_children)
    """
    __tablename__ = "children"
    
    # 基本字段
    name = Column(String(100), nullable=False, comment="姓名")
    birthday = Column(Date, nullable=False, comment="生日")
    gender = Column(String(10), nullable=False, comment="性别: male/female")
    avatar = Column(String(255), nullable=True, comment="头像路径")
    star_count = Column(Integer, default=0, nullable=False, comment="当前星星总数(冗余字段)")
    
    # 关系定义
    star_records = relationship(
        "StarRecord",
        back_populates="child",
        cascade="all, delete-orphan",
        order_by="StarRecord.created_at.desc()",
        lazy="selectin"
    )
    
    reward_children = relationship(
        "RewardChild",
        back_populates="child",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    @property
    def age(self) -> int:
        """计算当前年龄
        
        对应Laravel中的getAgeAttribute()方法
        Returns:
            int: 周岁年龄
        """
        if not self.birthday:
            return 0
        
        today = date.today()
        age = today.year - self.birthday.year
        
        # 如果今年生日还没到,年龄减1
        if (today.month, today.day) < (self.birthday.month, self.birthday.day):
            age -= 1
            
        return max(0, age)
    
    def __repr__(self) -> str:
        return f"<Child(id={self.id}, name='{self.name}', age={self.age}, stars={self.star_count})>"