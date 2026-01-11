"""
数据修复脚本：重置并重新计算所有存钱罐的利息

功能：
1.  **重置**:
    -   删除所有历史利息交易记录。
    -   基于非利息交易（存款、取款）重新计算“纯本金”余额。
    -   将存钱罐的余额重置为纯本金余额，累计利息归零。
2.  **重新计算**:
    -   调用核心的 `WalletService.calculate_and_settle_interest` 方法。
    -   从头开始，逐日、精确地重新计算所有历史利息。
    -   生成全新的、正确的利息交易记录。
    -   更新存钱罐的最终余额、累计利息和最后计息日期。

使用方法：
python3 fix_interest_data.py
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# --- 路径修复 ---
# 脚本从项目根目录执行时，数据库的相对路径会出错。
# 此处动态构建数据库的绝对路径以解决此问题。

# 1. 获取 'backend' 目录的绝对路径
BACKEND_DIR = Path(__file__).parent.resolve()

# 2. 将 'backend' 目录添加到 sys.path 以便能正确导入 'app' 模块
sys.path.insert(0, str(BACKEND_DIR))

# 3. 先导入 settings，然后用绝对路径覆盖 DATABASE_URL
from app.core.config import settings
DB_PATH = BACKEND_DIR / "storage" / "app" / "database.sqlite"

# --- 新增调试和修复 ---
# 打印将要使用的数据库路径，并确保其父目录存在
print(f"[*] 动态构建的数据库绝对路径: {DB_PATH}")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
print(f"[*] 确保数据库目录 {DB_PATH.parent} 已存在。")
# --- 结束新增 ---

settings.DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 4. 现在再导入依赖于数据库连接的模块
from sqlalchemy import select, delete, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.savings_box import SavingsBox
from app.models.wallet_transaction import WalletTransaction, WalletType, TransactionType
from app.models.child import Child
from app.models.pocket_money import PocketMoney
from app.services.wallet_service import WalletService


async def reset_savings_box_state(db: AsyncSession):
    """
    阶段一：重置所有存钱罐到初始状态（纯本金）
    """
    print("\n" + "=" * 80)
    print("🚀 阶段一：开始重置所有存钱罐状态...")
    print("=" * 80)

    result = await db.execute(
        select(SavingsBox, Child.name).join(Child, SavingsBox.child_id == Child.id)
    )
    savings_boxes = result.all()

    if not savings_boxes:
        print("🟡 未找到任何存钱罐数据，跳过重置。")
        return []

    child_ids_to_recalculate = []
    for savings_box, child_name in savings_boxes:
        child_id = savings_box.child_id
        child_ids_to_recalculate.append(child_id)
        
        print(f"\n--- 处理小朋友: {child_name} (ID: {child_id}) ---")
        print(f"[原始状态] 余额: ¥{savings_box.balance}, 累计利息: ¥{savings_box.total_interest}")

        # 1. 删除所有旧的利息记录 (无论是在存钱罐还是零花钱)
        delete_stmt = delete(WalletTransaction).where(
            WalletTransaction.child_id == child_id,
            WalletTransaction.transaction_type == TransactionType.INTEREST,
        )
        delete_result = await db.execute(delete_stmt)
        print(f"  - 已删除旧利息记录: {delete_result.rowcount}条")

        # 2. 计算纯本金余额 (存款为正, 取款为负)
        balance_stmt = select(
            func.sum(
                case(
                    (WalletTransaction.transaction_type == TransactionType.WITHDRAW, -WalletTransaction.amount),
                    else_=WalletTransaction.amount
                )
            )
        ).where(
            WalletTransaction.child_id == child_id,
            WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
            WalletTransaction.transaction_type.in_([TransactionType.DEPOSIT, TransactionType.WITHDRAW]),
        )
        base_balance = (await db.execute(balance_stmt)).scalar_one_or_none() or Decimal("0.00")
        
        # 3. 重置存钱罐状态
        savings_box.balance = base_balance
        savings_box.total_interest = Decimal("0.00")
        savings_box.last_interest_date = None
        print(f"  - [重置后] 存钱罐纯本金余额: ¥{base_balance}, 累计利息: ¥0.00")

        # 4. 计算并重置零花钱的纯本金余额
        pocket_money_res = await db.execute(select(PocketMoney).where(PocketMoney.child_id == child_id))
        pocket_money = pocket_money_res.scalar_one_or_none()

        if pocket_money:
            pocket_money_balance_stmt = select(
                func.sum(
                    case(
                        (WalletTransaction.transaction_type == TransactionType.WITHDRAW, -WalletTransaction.amount),
                        else_=WalletTransaction.amount
                    )
                )
            ).where(
                WalletTransaction.child_id == child_id,
                WalletTransaction.wallet_type == WalletType.POCKET_MONEY,
                WalletTransaction.transaction_type.in_([TransactionType.DEPOSIT, TransactionType.WITHDRAW]),
            )
            pocket_money_base_balance = (await db.execute(pocket_money_balance_stmt)).scalar_one_or_none() or Decimal("0.00")
            
            pocket_money.balance = pocket_money_base_balance
            print(f"  - [重置后] 零花钱纯本金余额: ¥{pocket_money_base_balance}")
        else:
            print(f"  - 警告: 未找到小朋友 {child_name} 的零花钱账户。")

    await db.commit()
    print("\n✅ 阶段一完成：所有存钱罐状态已重置为纯本金。")
    return child_ids_to_recalculate


async def recalculate_interest(db: AsyncSession, child_ids: list[int]):
    """
    阶段二：为所有已重置的存钱罐重新计算利息
    """
    print("\n" + "=" * 80)
    print("🚀 阶段二：开始重新计算历史利息...")
    print("=" * 80)

    if not child_ids:
        print("🟡 没有需要重新计算的存钱罐，跳过。")
        return

    wallet_service = WalletService(db)
    total_new_interest = Decimal("0.00")

    for child_id in child_ids:
        # 获取小朋友姓名用于打印
        child_name_res = await db.execute(select(Child.name).where(Child.id == child_id))
        child_name = child_name_res.scalar_one_or_none() or f"未知(ID: {child_id})"
        print(f"\n--- 重新计算小朋友: {child_name} ---")

        # 1. 获取存钱罐实例
        savings_box_res = await db.execute(
            select(SavingsBox).where(SavingsBox.child_id == child_id)
        )
        savings_box = savings_box_res.scalar_one_or_none()

        if not savings_box:
            print(f"  - 警告: 找不到小朋友 {child_name} 的存钱罐，跳过。")
            continue

        # 2. 调用服务进行利息计算和结算
        #    该服务会计算从 last_interest_date (现在是 None) 到昨天的所有利息，
        #    该服务会从头开始，逐日计算所有历史利息，并为每一天生成一条独立的交易记录。
        print("  - 调用核心服务进行逐日利息计算和结算...")
        total_new_interest_for_child, transactions_created = await wallet_service.calculate_and_settle_interest(savings_box)

        if transactions_created > 0:
            # 刷新对象以获取最新状态
            await db.refresh(savings_box)
            
            # 获取零花钱账户并刷新
            pocket_money_res = await db.execute(select(PocketMoney).where(PocketMoney.child_id == child_id))
            pocket_money = pocket_money_res.scalar_one()
            await db.refresh(pocket_money)

            print(f"  - [结算成功] 共生成 {transactions_created} 条每日利息记录。")
            print(f"  - [结算成功] 新增总利息: ¥{total_new_interest_for_child:.4f} (已全部存入零花钱)")
            print(f"  - [结算后] 存钱罐余额 (本金不变): ¥{savings_box.balance:.2f}")
            print(f"  - [结算后] 存钱罐累计利息 (更新): ¥{savings_box.total_interest:.4f}")
            print(f"  - [结算后] 零花钱最新余额: ¥{pocket_money.balance:.2f}")
            total_new_interest += total_new_interest_for_child
        else:
            print("  - 无需计算利息（可能没有存款或存款时间不足）。")

    # 注意：calculate_and_settle_interest 方法内部已经包含了 commit,
    # 所以在这里不需要再次执行 db.commit()。
    print(f"\n✅ 阶段二完成：所有历史利息已重新计算，总计 ¥{total_new_interest:.4f}")


async def main():
    """主执行函数"""
    print("=" * 80)
    print("🔧 开始执行存钱罐利息重置和重新计算脚本")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        try:
            # 阶段一：重置
            child_ids = await reset_savings_box_state(db)
            
            # 阶段二：重新计算
            await recalculate_interest(db, child_ids)

            print("\n" + "=" * 80)
            print("🎉 全部任务成功完成！数据已修复。")
            print("=" * 80)

        except Exception as e:
            await db.rollback()
            print(f"\n❌ 操作失败，已回滚所有更改: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())