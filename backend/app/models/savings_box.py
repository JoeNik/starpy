from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel
from app.core.config import settings
from app.models.wallet_transaction import WalletTransaction, WalletType, TransactionType
import logging

# 配置日志
logger = logging.getLogger(__name__)


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
    
    async def calculate_pending_interest(self, db: AsyncSession) -> Decimal:
        """【重构】计算待结算利息 (每日计息)
        
        根据上次计息日期到昨日的每一天的日终余额来计算应得利息。
        
        Args:
            db: 数据库会话
            
        Returns:
            Decimal: 待结算利息金额
        """
        # 计息起始日期: 如果有上次计息日, 则从其后一天开始; 否则从账户创建日开始
        start_date = (self.last_interest_date + timedelta(days=1)) if self.last_interest_date else self.created_at.date()
        
        # 计息结束日期: 昨天
        end_date = date.today() - timedelta(days=1)
        
        logger.debug(f"[InterestCalc] child_id={self.child_id}: 开始计算, 周期: {start_date} -> {end_date}")
        
        # 如果起始日期晚于结束日期, 说明无需计息
        if start_date > end_date:
            logger.debug(f"[InterestCalc] child_id={self.child_id}: 无需计息, start_date ({start_date}) > end_date ({end_date}).")
            return Decimal('0.00')
            
        # --- 1. 获取计息周期内的所有交易 ---
        transactions_result = await db.execute(
            select(WalletTransaction)
            .where(
                WalletTransaction.child_id == self.child_id,
                WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
                func.date(WalletTransaction.created_at) >= start_date,
                func.date(WalletTransaction.created_at) <= end_date
            )
            .order_by(WalletTransaction.created_at.asc())
        )
        transactions = transactions_result.scalars().all()
        
        # --- 2. 获取计息周期的期初余额 (即 start_date 之前的最后余额) ---
        last_tx_before_start_result = await db.execute(
            select(WalletTransaction)
            .where(
                WalletTransaction.child_id == self.child_id,
                WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
                func.date(WalletTransaction.created_at) < start_date
            )
            .order_by(WalletTransaction.created_at.desc())
            .limit(1)
        )
        last_tx = last_tx_before_start_result.scalar_one_or_none()
        
        current_balance = last_tx.balance_after if last_tx else Decimal('0.00')
        logger.debug(f"[InterestCalc] child_id={self.child_id}: 期初余额 ({start_date}): {current_balance}")

        # --- 3. 逐日计算利息 ---
        total_interest = Decimal('0.00')
        daily_rate = self.daily_interest_rate
        tx_idx = 0
        
        iter_date = start_date
        while iter_date <= end_date:
            # 继承上一天的日终余额作为今天的期初余额
            day_end_balance = current_balance
            
            # 应用当天的所有交易, 更新日终余额
            while tx_idx < len(transactions) and transactions[tx_idx].created_at.date() == iter_date:
                tx = transactions[tx_idx]
                day_end_balance = tx.balance_after
                tx_idx += 1
            
            # 计息: 使用当天的日终余额
            if day_end_balance > 0:
                daily_interest = day_end_balance * daily_rate
                total_interest += daily_interest
                logger.debug(f"[InterestCalc] child_id={self.child_id}: {iter_date} - 日终余额: {day_end_balance:.2f}, 当日利息: {daily_interest:.4f}")
            else:
                logger.debug(f"[InterestCalc] child_id={self.child_id}: {iter_date} - 日终余额: {day_end_balance:.2f}, 无利息")
            
            # 为下一天的循环更新期初余额
            current_balance = day_end_balance
            # 前进到下一天
            iter_date += timedelta(days=1)

        result = total_interest.quantize(Decimal('0.01'))
        logger.info(f"[InterestCalc] child_id={self.child_id}: 计算完成. 周期: {start_date} -> {end_date}, 总利息: {result}")
        
        return result
    
    def __repr__(self) -> str:
        return f"<SavingsBox(id={self.id}, child_id={self.child_id}, balance={self.balance}, interest={self.total_interest})>"