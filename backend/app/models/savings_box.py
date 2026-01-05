from decimal import Decimal
from datetime import date
from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel
from app.core.config import settings


class SavingsBox(BaseModel):
    """存钱罐模型
    
    存储小朋友的存款信息，支持利息计算功能。
    
    特性：
    - 与Child模型一对一关系
    - 支持每日利息计算
    - 记录累计利息收益
    - 利率可配置
    """
    __tablename__ = "savings_boxes"
    
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
    
    total_interest = Column(
        Numeric(precision=10, scale=2), 
        nullable=False, 
        default=Decimal('0.00'),
        comment="累计利息收益"
    )
    
    last_interest_date = Column(
        Date, 
        nullable=True,
        comment="最后一次计算利息的日期"
    )
    
    interest_rate = Column(
        Numeric(precision=5, scale=4), 
        nullable=False, 
        default=Decimal('0.0500'),  # 默认5%年化利率
        comment="存款年化利率"
    )
    
    # 关系定义
    child = relationship(
        "Child",
        back_populates="savings_box",
        lazy="selectin"
    )
    
    @property
    def daily_interest_rate(self) -> Decimal:
        """计算日利率
        
        将年化利率转换为日利率
        Returns:
            Decimal: 日利率
        """
        return self.interest_rate / Decimal('365')
    
    def calculate_pending_interest(self) -> Decimal:
        """计算待结算利息
        
        根据上次计息日期到今天的天数计算应得利息
        Returns:
            Decimal: 待结算利息金额
        """
        if not self.last_interest_date or self.balance <= 0:
            return Decimal('0.00')
        
        today = date.today()
        days = (today - self.last_interest_date).days
        
        if days <= 0:
            return Decimal('0.00')
        
        # 日利息 = 余额 * 日利率 * 天数
        interest = self.balance * self.daily_interest_rate * Decimal(str(days))
        return interest.quantize(Decimal('0.01'))  # 保留2位小数
    
    def __repr__(self) -> str:
        return f"<SavingsBox(id={self.id}, child_id={self.child_id}, balance={self.balance}, interest={self.total_interest})>"