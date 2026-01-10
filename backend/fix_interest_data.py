"""
数据修复脚本：修复错误的利息计算并补偿正确利息

功能：
1. 删除所有错误的利息交易记录
2. 重置存钱罐余额和累计利息到初始状态
3. 从创建日期到今天重新计算所有应结算利息
4. 批量生成正确的利息交易记录
5. 更新存钱罐余额、累计利息和上次计息日期

修复原因：
- 之前的脚本使用了错误的公式 (interest_rate / 36500)
- 正确公式应该是 (interest_rate / 365)
- 导致每日利息计算结果相差100倍

使用方法：
python3 fix_interest_data.py
"""

import asyncio
import sys
from datetime import date, timedelta, datetime
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.models.savings_box import SavingsBox
from app.models.wallet_transaction import WalletTransaction, WalletType, TransactionType
from app.models.child import Child
from sqlalchemy import select, delete


async def fix_interest_data():
    """修复利息数据
    
    步骤：
    1. 清理错误的利息交易记录
    2. 重置存钱罐状态
    3. 使用正确公式重新计算所有利息
    4. 生成正确的利息交易记录
    """
    print("=" * 80)
    print("🔧 开始修复利息数据")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 查询所有存钱罐
            result = await db.execute(
                select(SavingsBox, Child.name)
                .join(Child, SavingsBox.child_id == Child.id)
            )
            savings_boxes = result.all()
            
            if not savings_boxes:
                print("❌ 未找到任何存钱罐数据")
                return
            
            total_fixed_interest = Decimal('0.00')
            
            for savings_box, child_name in savings_boxes:
                print(f"\n{'='*60}")
                print(f"📦 处理存钱罐: {child_name}")
                print(f"{'='*60}")
                print(f"[原始状态]")
                print(f"   余额: ¥{savings_box.balance}")
                print(f"   累计利息: ¥{savings_box.total_interest}")
                print(f"   创建时间: {savings_box.created_at.date()}")
                print(f"   上次计息日期: {savings_box.last_interest_date}")
                
                # 2. 删除所有利息交易记录
                delete_result = await db.execute(
                    delete(WalletTransaction)
                    .where(
                        WalletTransaction.child_id == savings_box.child_id,
                        WalletTransaction.wallet_type == WalletType.SAVINGS_BOX,
                        WalletTransaction.transaction_type == TransactionType.INTEREST
                    )
                )
                deleted_count = delete_result.rowcount
                print(f"\n[清理数据]")
                print(f"   删除错误利息记录: {deleted_count}条")
                
                # 3. 计算初始余额（减去累计错误利息）
                initial_balance = savings_box.balance - savings_box.total_interest
                print(f"   重置余额: ¥{savings_box.balance} - ¥{savings_box.total_interest} = ¥{initial_balance}")
                
                # 4. 重置存钱罐状态
                savings_box.balance = initial_balance
                savings_box.total_interest = Decimal('0.00')
                savings_box.last_interest_date = None
                
                # 5. 确定起始日期和结束日期
                # 起始日期：创建日期的第二天（创建当天不计息）
                start_date = savings_box.created_at.date() + timedelta(days=1)
                end_date = date.today()
                
                if start_date > end_date:
                    print(f"\n⚠️ 创建日期太晚，暂无需结算的利息")
                    continue
                
                # 6. 计算需要补偿的天数
                days_to_fix = (end_date - start_date).days + 1
                print(f"\n[重新计算利息]")
                print(f"   计息期间: {start_date} 到 {end_date} ({days_to_fix}天)")
                print(f"   初始余额: ¥{initial_balance}")
                print(f"   年化利率: {float(savings_box.interest_rate * 100):.2f}%")
                
                # 7. 逐日计算利息并创建交易记录
                # 注意：需要使用每日累积后的余额来计算次日利息（复利）
                current_balance = initial_balance
                total_interest_accumulated = Decimal('0.00')
                current_date = start_date
                daily_transactions = []
                
                print(f"\n[逐日计息明细]")
                while current_date <= end_date:
                    # ✅ 修复：使用正确的公式 (interest_rate / 365)
                    daily_rate = savings_box.interest_rate / Decimal('365')
                    daily_interest = (current_balance * daily_rate).quantize(Decimal('0.01'))
                    
                    if daily_interest > 0:
                        # 创建利息交易记录（使用当天的时间戳）
                        transaction_time = datetime.combine(current_date, datetime.min.time())
                        transaction = WalletTransaction(
                            child_id=savings_box.child_id,
                            wallet_type='SAVINGS_BOX',
                            transaction_type='INTEREST',
                            amount=daily_interest,
                            balance_after=current_balance + daily_interest,
                            remark=f'补偿{current_date}的每日利息',
                            interest_amount=daily_interest,
                            created_at=transaction_time
                        )
                        daily_transactions.append(transaction)
                        
                        # 累积利息和余额（复利）
                        current_balance += daily_interest
                        total_interest_accumulated += daily_interest
                        
                        print(f"   {current_date}: +¥{daily_interest:>6} → 余额 ¥{current_balance}")
                    
                    current_date += timedelta(days=1)
                
                # 8. 批量保存交易记录
                if daily_transactions:
                    db.add_all(daily_transactions)
                    print(f"\n[保存记录]")
                    print(f"   ✓ 创建了 {len(daily_transactions)} 条新的利息交易记录")
                
                # 9. 更新存钱罐数据
                savings_box.balance = current_balance
                savings_box.total_interest = total_interest_accumulated
                savings_box.last_interest_date = end_date
                
                print(f"\n[最终状态]")
                print(f"   ✓ 补偿利息总额: ¥{total_interest_accumulated}")
                print(f"   ✓ 最终余额: ¥{savings_box.balance}")
                print(f"   ✓ 累计利息: ¥{savings_box.total_interest}")
                print(f"   ✓ 计息日期: {savings_box.last_interest_date}")
                
                total_fixed_interest += total_interest_accumulated
            
            # 10. 提交所有更改
            await db.commit()
            
            print("\n" + "=" * 80)
            print(f"✅ 修复完成！")
            print(f"   共补偿正确利息: ¥{total_fixed_interest}")
            print(f"   请刷新前端页面查看更新后的数据")
            print("=" * 80)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 修复失败: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_interest_data())