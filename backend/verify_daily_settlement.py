import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Child, SavingsBox, WalletTransaction
from app.services.scheduler_service import scheduler_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def print_db_state(db: AsyncSession, child_id: int, message: str):
    """打印数据库状态"""
    logging.info(f"--- {message} ---")
    
    # 获取存钱罐
    savings_box = await db.get(SavingsBox, child_id)
    if not savings_box:
        logging.warning(f"未找到 child_id={child_id} 的存钱罐")
        return

    logging.info(f"存钱罐(ID={savings_box.id}): "
                 f"余额=¥{savings_box.balance}, "
                 f"上次计息日={savings_box.last_interest_date}")

    # 获取交易记录
    stmt = select(WalletTransaction).where(
        WalletTransaction.child_id == child_id,
        WalletTransaction.wallet_type == 'savings_box'
    ).order_by(WalletTransaction.created_at.desc()).limit(10)
    
    result = await db.execute(stmt)
    transactions = result.scalars().all()
    
    logging.info("最近10条交易记录:")
    if not transactions:
        logging.info("  (无)")
    for tx in transactions:
        logging.info(f"  - [{tx.created_at.strftime('%Y-%m-%d %H:%M')}] "
                     f"类型={tx.transaction_type}, "
                     f"金额=¥{tx.amount}, "
                     f"备注='{tx.remark}'")
    logging.info("-" * 20)


async def main():
    """主验证函数"""
    child_id_to_test = 1
    
    logging.info("=" * 60)
    logging.info("开始验证每日利息结算修复...")
    logging.info(f"测试目标儿童ID: {child_id_to_test}")
    logging.info("=" * 60)

    async with AsyncSessionLocal() as db:
        # 人为将上次计息日调回前天，以强制触发对昨天的结算
        logging.info(">>> 正在重置测试数据的上次计息日到前天...")
        savings_box_to_reset = await db.get(SavingsBox, child_id_to_test)
        if savings_box_to_reset:
            day_before_yesterday = date.today() - timedelta(days=2)
            savings_box_to_reset.last_interest_date = day_before_yesterday
            await db.commit()
            await db.refresh(savings_box_to_reset)
            logging.info(f"存钱罐(ID={savings_box_to_reset.id}) 的 last_interest_date 已重置为 {day_before_yesterday}")
        else:
            logging.warning(f"未找到用于重置的存钱罐 (child_id={child_id_to_test})")

        # 打印初始状态
        await print_db_state(db, child_id_to_test, "结算前状态")

        # 手动触发结算任务
        logging.info("\n>>> 正在手动触发每日利息结算任务...\n")
        try:
            await scheduler_service.daily_interest_settlement_job()
            logging.info("\n>>> 结算任务执行完成。\n")
        except Exception as e:
            logging.error(f"执行结算任务时发生错误: {e}", exc_info=True)
            return

        # 打印最终状态
        await print_db_state(db, child_id_to_test, "结算后状态")

    logging.info("=" * 60)
    logging.info("验证脚本执行完毕。请检查'结算后状态'中的余额和交易记录。")
    logging.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())