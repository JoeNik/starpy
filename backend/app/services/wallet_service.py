"""
钱包业务逻辑Service
实现存钱罐、零花钱的所有业务操作
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models import Child, SavingsBox, PocketMoney, WalletTransaction
from app.models.wallet_transaction import WalletType, TransactionType
from app.schemas.wallet import (
    SavingsBoxResponse,
    PocketMoneyResponse,
    WalletTransactionResponse,
    WalletOverview
)
from app.services.base_service import BaseService


class WalletService(BaseService[WalletTransaction]):
    """钱包业务逻辑Service"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(WalletTransaction, db)
    
    async def get_or_create_wallets(
        self,
        child_id: int
    ) -> Tuple[SavingsBox, PocketMoney]:
        """
        获取或创建指定小朋友的钱包（存钱罐和零花钱）
        
        业务逻辑:
        1. 验证小朋友存在
        2. 查询存钱罐和零花钱
        3. 如果不存在则自动创建，初始余额为0
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            Tuple[SavingsBox, PocketMoney]: 存钱罐和零花钱对象
            
        Raises:
            ResourceNotFoundError: 小朋友不存在
        """
        # 1. 验证小朋友存在
        child_result = await self.db.execute(
            select(Child).where(Child.id == child_id)
        )
        if not child_result.scalar_one_or_none():
            raise ResourceNotFoundError("Child", child_id)
        
        # 2. 查询或创建存钱罐
        savings_result = await self.db.execute(
            select(SavingsBox).where(SavingsBox.child_id == child_id)
        )
        savings_box = savings_result.scalar_one_or_none()
        
        if not savings_box:
            # 使用配置文件中的默认利率（转换为小数）
            default_rate = Decimal(str(settings.SAVINGS_BOX_ANNUAL_INTEREST_RATE / 100))
            savings_box = SavingsBox(
                child_id=child_id,
                balance=Decimal('0.00'),
                total_interest=Decimal('0.00'),
                interest_rate=default_rate,
                last_interest_date=None
            )
            self.db.add(savings_box)
        
        # 3. 查询或创建零花钱
        pocket_result = await self.db.execute(
            select(PocketMoney).where(PocketMoney.child_id == child_id)
        )
        pocket_money = pocket_result.scalar_one_or_none()
        
        if not pocket_money:
            pocket_money = PocketMoney(
                child_id=child_id,
                balance=Decimal('0.00')
            )
            self.db.add(pocket_money)
        
        # 提交创建的记录
        await self.db.commit()
        await self.db.refresh(savings_box)
        await self.db.refresh(pocket_money)
        
        return savings_box, pocket_money
    
    async def savings_box_deposit(
        self,
        child_id: int,
        amount: Decimal,
        remark: Optional[str] = None
    ) -> SavingsBoxResponse:
        """
        存钱罐转入（存款）
        
        业务逻辑:
        1. 获取或创建钱包
        2. 在事务中:
           - 更新余额
           - 记录交易
        
        Args:
            child_id: 小朋友ID
            amount: 存款金额
            remark: 交易备注
            
        Returns:
            SavingsBoxResponse: 更新后的存钱罐信息
        """
        try:
            # 1. 获取存钱罐（加锁）
            savings_box = await self._get_savings_box_for_update(child_id)
            
            # 2. 更新余额
            savings_box.balance += amount
            
            # 3. 记录交易
            transaction = WalletTransaction(
                child_id=child_id,
                wallet_type=WalletType.SAVINGS_BOX,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                balance_after=savings_box.balance,
                remark=remark,
                created_at=datetime.now()
            )
            self.db.add(transaction)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(savings_box)
            
            # 构造响应
            return SavingsBoxResponse(
                id=savings_box.id,
                child_id=savings_box.child_id,
                balance=savings_box.balance,
                total_interest=savings_box.total_interest,
                interest_rate=savings_box.interest_rate,
                last_interest_date=savings_box.last_interest_date,
                today_interest=await savings_box.calculate_pending_interest(self.db),
                created_at=savings_box.created_at,
                updated_at=savings_box.updated_at
            )
        
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"存钱罐存款失败: {str(e)}")
    
    async def savings_box_withdraw(
        self,
        child_id: int,
        amount: Decimal,
        remark: Optional[str] = None
    ) -> SavingsBoxResponse:
        """
        存钱罐转出（取款）
        
        业务逻辑:
        1. 获取存钱罐
        2. 验证余额是否充足
        3. 在事务中:
           - 更新余额
           - 记录交易
        
        Args:
            child_id: 小朋友ID
            amount: 取款金额
            remark: 交易备注
            
        Returns:
            SavingsBoxResponse: 更新后的存钱罐信息
            
        Raises:
            ValidationError: 余额不足
        """
        try:
            # 1. 获取存钱罐（加锁）
            savings_box = await self._get_savings_box_for_update(child_id)
            
            # 2. 验证余额
            if savings_box.balance < amount:
                raise ValidationError(
                    f"存钱罐余额不足(当前: {savings_box.balance}, 需要: {amount})"
                )
            
            # 3. 更新余额
            savings_box.balance -= amount
            
            # 4. 记录交易
            transaction = WalletTransaction(
                child_id=child_id,
                wallet_type=WalletType.SAVINGS_BOX,
                transaction_type=TransactionType.WITHDRAW,
                amount=amount,
                balance_after=savings_box.balance,
                remark=remark,
                created_at=datetime.now()
            )
            self.db.add(transaction)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(savings_box)
            
            # 构造响应
            return SavingsBoxResponse(
                id=savings_box.id,
                child_id=savings_box.child_id,
                balance=savings_box.balance,
                total_interest=savings_box.total_interest,
                interest_rate=savings_box.interest_rate,
                last_interest_date=savings_box.last_interest_date,
                today_interest=await savings_box.calculate_pending_interest(self.db),
                created_at=savings_box.created_at,
                updated_at=savings_box.updated_at
            )
        
        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"存钱罐取款失败: {str(e)}")
    
    async def get_savings_box(self, child_id: int) -> SavingsBoxResponse:
        """
        获取存钱罐信息
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            SavingsBoxResponse: 存钱罐信息（包含当日待结算利息）
        """
        savings_box, _ = await self.get_or_create_wallets(child_id)
        
        return SavingsBoxResponse(
            id=savings_box.id,
            child_id=savings_box.child_id,
            balance=savings_box.balance,
            total_interest=savings_box.total_interest,
            interest_rate=savings_box.interest_rate,
            last_interest_date=savings_box.last_interest_date,
            today_interest=await savings_box.calculate_pending_interest(self.db),
            created_at=savings_box.created_at,
            updated_at=savings_box.updated_at
        )
    
    async def get_savings_box_transactions(
        self,
        child_id: int,
        limit: int = 10
    ) -> List[WalletTransactionResponse]:
        """
        获取存钱罐交易明细
        
        Args:
            child_id: 小朋友ID
            limit: 返回记录数（默认10）
            
        Returns:
            List[WalletTransactionResponse]: 交易记录列表（按时间倒序）
        """
        # 验证小朋友存在
        await self.get_or_create_wallets(child_id)
        
        result = await self.db.execute(
            select(WalletTransaction)
            .where(
                WalletTransaction.child_id == child_id,
                WalletTransaction.wallet_type == WalletType.SAVINGS_BOX
            )
            .order_by(WalletTransaction.created_at.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()
        
        return [
            WalletTransactionResponse(
                id=t.id,
                child_id=t.child_id,
                wallet_type=t.wallet_type,
                transaction_type=t.transaction_type,
                amount=t.amount,
                balance_after=t.balance_after,
                remark=t.remark,
                interest_amount=t.interest_amount,
                created_at=t.created_at
            )
            for t in transactions
        ]
    
    async def pocket_money_deposit(
        self,
        child_id: int,
        amount: Decimal,
        remark: Optional[str] = None
    ) -> PocketMoneyResponse:
        """
        零花钱转入
        
        Args:
            child_id: 小朋友ID
            amount: 转入金额
            remark: 交易备注
            
        Returns:
            PocketMoneyResponse: 更新后的零花钱信息
        """
        try:
            # 1. 获取零花钱（加锁）
            pocket_money = await self._get_pocket_money_for_update(child_id)
            
            # 2. 更新余额
            pocket_money.balance += amount
            
            # 3. 记录交易
            transaction = WalletTransaction(
                child_id=child_id,
                wallet_type=WalletType.POCKET_MONEY,
                transaction_type=TransactionType.DEPOSIT,
                amount=amount,
                balance_after=pocket_money.balance,
                remark=remark,
                created_at=datetime.now()
            )
            self.db.add(transaction)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(pocket_money)
            
            return PocketMoneyResponse(
                id=pocket_money.id,
                child_id=pocket_money.child_id,
                balance=pocket_money.balance,
                created_at=pocket_money.created_at,
                updated_at=pocket_money.updated_at
            )
        
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"零花钱转入失败: {str(e)}")
    
    async def pocket_money_withdraw(
        self,
        child_id: int,
        amount: Decimal,
        remark: Optional[str] = None
    ) -> PocketMoneyResponse:
        """
        零花钱转出
        
        业务逻辑:
        1. 获取零花钱
        2. 验证余额是否充足
        3. 在事务中:
           - 更新余额
           - 记录交易
        
        Args:
            child_id: 小朋友ID
            amount: 转出金额
            remark: 交易备注
            
        Returns:
            PocketMoneyResponse: 更新后的零花钱信息
            
        Raises:
            ValidationError: 余额不足
        """
        try:
            # 1. 获取零花钱（加锁）
            pocket_money = await self._get_pocket_money_for_update(child_id)
            
            # 2. 验证余额
            if pocket_money.balance < amount:
                raise ValidationError(
                    f"零花钱余额不足(当前: {pocket_money.balance}, 需要: {amount})"
                )
            
            # 3. 更新余额
            pocket_money.balance -= amount
            
            # 4. 记录交易
            transaction = WalletTransaction(
                child_id=child_id,
                wallet_type=WalletType.POCKET_MONEY,
                transaction_type=TransactionType.WITHDRAW,
                amount=amount,
                balance_after=pocket_money.balance,
                remark=remark,
                created_at=datetime.now()
            )
            self.db.add(transaction)
            
            # 提交事务
            await self.db.commit()
            await self.db.refresh(pocket_money)
            
            return PocketMoneyResponse(
                id=pocket_money.id,
                child_id=pocket_money.child_id,
                balance=pocket_money.balance,
                created_at=pocket_money.created_at,
                updated_at=pocket_money.updated_at
            )
        
        except ValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise ValidationError(f"零花钱转出失败: {str(e)}")
    
    async def get_pocket_money(self, child_id: int) -> PocketMoneyResponse:
        """
        获取零花钱信息
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            PocketMoneyResponse: 零花钱信息
        """
        _, pocket_money = await self.get_or_create_wallets(child_id)
        
        return PocketMoneyResponse(
            id=pocket_money.id,
            child_id=pocket_money.child_id,
            balance=pocket_money.balance,
            created_at=pocket_money.created_at,
            updated_at=pocket_money.updated_at
        )
    
    async def get_pocket_money_transactions(
        self,
        child_id: int,
        limit: int = 10
    ) -> List[WalletTransactionResponse]:
        """
        获取零花钱交易明细
        
        Args:
            child_id: 小朋友ID
            limit: 返回记录数（默认10）
            
        Returns:
            List[WalletTransactionResponse]: 交易记录列表（按时间倒序）
        """
        # 验证小朋友存在
        await self.get_or_create_wallets(child_id)
        
        result = await self.db.execute(
            select(WalletTransaction)
            .where(
                WalletTransaction.child_id == child_id,
                WalletTransaction.wallet_type == WalletType.POCKET_MONEY
            )
            .order_by(WalletTransaction.created_at.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()
        
        return [
            WalletTransactionResponse(
                id=t.id,
                child_id=t.child_id,
                wallet_type=t.wallet_type,
                transaction_type=t.transaction_type,
                amount=t.amount,
                balance_after=t.balance_after,
                remark=t.remark,
                interest_amount=t.interest_amount,
                created_at=t.created_at
            )
            for t in transactions
        ]
    
    async def get_wallet_overview(self, child_id: int) -> WalletOverview:
        """
        获取钱包总览（包含存钱罐、零花钱和最近10条交易记录）
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            WalletOverview: 钱包总览信息
        """
        # 1. 获取存钱罐和零花钱
        savings_box, pocket_money = await self.get_or_create_wallets(child_id)
        
        # 2. 获取最近10条交易记录（所有钱包类型）
        result = await self.db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.child_id == child_id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(10)
        )
        transactions = result.scalars().all()
        
        # 3. 构造响应
        return WalletOverview(
            savings_box=SavingsBoxResponse(
                id=savings_box.id,
                child_id=savings_box.child_id,
                balance=savings_box.balance,
                total_interest=savings_box.total_interest,
                interest_rate=savings_box.interest_rate,
                last_interest_date=savings_box.last_interest_date,
                today_interest=await savings_box.calculate_pending_interest(self.db),
                created_at=savings_box.created_at,
                updated_at=savings_box.updated_at
            ),
            pocket_money=PocketMoneyResponse(
                id=pocket_money.id,
                child_id=pocket_money.child_id,
                balance=pocket_money.balance,
                created_at=pocket_money.created_at,
                updated_at=pocket_money.updated_at
            ),
            recent_transactions=[
                WalletTransactionResponse(
                    id=t.id,
                    child_id=t.child_id,
                    wallet_type=t.wallet_type,
                    transaction_type=t.transaction_type,
                    amount=t.amount,
                    balance_after=t.balance_after,
                    remark=t.remark,
                    interest_amount=t.interest_amount,
                    created_at=t.created_at
                )
                for t in transactions
            ]
        )
    
    async def calculate_and_settle_interest(
        self,
        savings_box: SavingsBox
    ) -> Tuple[Decimal, int]:
        """
        【新版 V2】逐日计算并结算利息，将每日收益逐笔存入零花钱
        
        业务逻辑:
        1.  确定计息周期（从上次结算日到昨天）。
        2.  获取周期内的所有本金交易（存款/取款），并按日期排序。
        3.  在事务中，逐日循环：
            a. 计算当天的本金余额。
            b. 计算当日产生的利息。
            c. 如果利息 > 0，创建一笔独立的、类型为INTEREST的交易记录，关联到零花钱钱包。
               - `created_at` 设置为当前时间，以便前端能计入“今日收益”。
               - `remark` 字段会注明利息归属的日期。
        4.  将所有产生的利息总额一次性加到零花钱余额和存钱罐累计利息中。
        5.  更新存钱罐的最后计息日期为昨天。
        
        Args:
            savings_box: 存钱罐对象
            
        Returns:
            Tuple[Decimal, int]: 一个元组，包含:
                                 - Decimal: 本次结算的总利息金额
                                 - int: 本次结算创建的每日利息交易记录数量
        """
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # 1. 确定计息周期
            # 如果从未计息，则从第一笔交易开始
            if savings_box.last_interest_date is None:
                first_tx_res = await self.db.execute(
                    select(WalletTransaction.created_at)
                    .where(
                        WalletTransaction.child_id == savings_box.child_id,
                        WalletTransaction.wallet_type == WalletType.SAVINGS_BOX
                    )
                    .order_by(WalletTransaction.created_at.asc())
                    .limit(1)
                )
                first_tx_date = first_tx_res.scalar_one_or_none()
                if not first_tx_date:
                    return Decimal('0.00'), 0 # 没有交易，没有利息
                start_date = first_tx_date.date()
            else:
                start_date = savings_box.last_interest_date + timedelta(days=1)

            if start_date > yesterday:
                return Decimal('0.00'), 0 # 已经结算到最新

            # 2. 获取周期内的所有本金交易
            transactions_res = await self.db.execute(
                select(WalletTransaction)
                .where(
                    WalletTransaction.child_id == savings_box.child_id,
                    WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
                    WalletTransaction.transaction_type.in_([TransactionType.DEPOSIT, TransactionType.WITHDRAW]),
                    WalletTransaction.created_at >= datetime.combine(start_date, datetime.min.time())
                )
                .order_by(WalletTransaction.created_at.asc())
            )
            transactions = transactions_res.scalars().all()

            # 获取计息开始前的余额
            balance_before_start_res = await self.db.execute(
                select(WalletTransaction.balance_after)
                .where(
                    WalletTransaction.child_id == savings_box.child_id,
                    WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
                    WalletTransaction.created_at < datetime.combine(start_date, datetime.min.time())
                )
                .order_by(WalletTransaction.created_at.desc())
                .limit(1)
            )
            current_balance = balance_before_start_res.scalar_one_or_none() or Decimal('0.00')

            daily_rate = savings_box.interest_rate / Decimal('365')
            total_new_interest = Decimal('0.00')
            transactions_created = 0
            
            # 获取零花钱账户（加锁）
            pocket_money = await self._get_pocket_money_for_update(savings_box.child_id)
            
            # 3. 逐日循环计算
            tx_idx = 0
            for day_offset in range((yesterday - start_date).days + 1):
                current_day = start_date + timedelta(days=day_offset)
                
                # 更新当天所有交易带来的余额变化
                while tx_idx < len(transactions) and transactions[tx_idx].created_at.date() == current_day:
                    tx = transactions[tx_idx]
                    if tx.transaction_type == TransactionType.DEPOSIT:
                        current_balance += tx.amount
                    elif tx.transaction_type == TransactionType.WITHDRAW:
                        current_balance -= tx.amount
                    tx_idx += 1

                # 用当天的最终余额计算利息
                if current_balance > 0:
                    daily_interest = current_balance * daily_rate
                    daily_interest = round(daily_interest, 4) # 保留4位小数以提高精度

                    if daily_interest > 0:
                        total_new_interest += daily_interest
                        
                        # 创建每日利息交易记录
                        interest_transaction = WalletTransaction(
                            child_id=savings_box.child_id,
                            wallet_type=WalletType.POCKET_MONEY,
                            transaction_type=TransactionType.INTEREST,
                            amount=daily_interest,
                            balance_after=pocket_money.balance + total_new_interest, # 预估交易后余额
                            remark=f"{current_day.strftime('%Y-%m-%d')} 的利息",
                            interest_amount=daily_interest,
                            created_at=datetime.now() # 使用当前时间
                        )
                        self.db.add(interest_transaction)
                        transactions_created += 1

            if total_new_interest <= 0:
                # 即使没有利息，也要更新日期
                savings_box.last_interest_date = yesterday
                await self.db.commit()
                return Decimal('0.00'), 0

            # 最终结算的总利息，四舍五入到分
            final_interest_to_settle = round(total_new_interest, 2)

            # 4. 更新账户
            pocket_money.balance += final_interest_to_settle
            savings_box.total_interest += final_interest_to_settle
            savings_box.last_interest_date = yesterday
            
            # 5. 提交事务
            await self.db.commit()
            await self.db.refresh(savings_box)
            await self.db.refresh(pocket_money)
            
            return final_interest_to_settle, transactions_created
        
        except Exception as e:
            await self.db.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"利息结算失败 (child_id={savings_box.child_id}): {str(e)}", exc_info=True)
            raise ValidationError(f"利息结算失败: {str(e)}")
    
    async def _get_savings_box_for_update(self, child_id: int) -> SavingsBox:
        """
        获取存钱罐（加行锁）
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            SavingsBox: 存钱罐对象
            
        Raises:
            ResourceNotFoundError: 存钱罐不存在
        """
        # 先确保钱包存在
        savings_box, _ = await self.get_or_create_wallets(child_id)
        
        # 重新查询并加锁
        result = await self.db.execute(
            select(SavingsBox)
            .where(SavingsBox.child_id == child_id)
            .with_for_update()
        )
        savings_box = result.scalar_one_or_none()
        
        if not savings_box:
            raise ResourceNotFoundError("SavingsBox", child_id)
        
        return savings_box
    
    async def _get_pocket_money_for_update(self, child_id: int) -> PocketMoney:
        """
        获取零花钱（加行锁）
        
        Args:
            child_id: 小朋友ID
            
        Returns:
            PocketMoney: 零花钱对象
            
        Raises:
            ResourceNotFoundError: 零花钱不存在
        """
        # 先确保钱包存在
        _, pocket_money = await self.get_or_create_wallets(child_id)
        
        # 重新查询并加锁
        result = await self.db.execute(
            select(PocketMoney)
            .where(PocketMoney.child_id == child_id)
            .with_for_update()
        )
        pocket_money = result.scalar_one_or_none()
        
        if not pocket_money:
            raise ResourceNotFoundError("PocketMoney", child_id)
        
        return pocket_money