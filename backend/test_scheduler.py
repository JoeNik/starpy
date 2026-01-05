"""
定时任务测试脚本
用于测试每日利息结算功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.scheduler_service import scheduler_service
from app.core.database import init_db


async def test_interest_settlement():
    """测试利息结算功能"""
    print("=" * 60)
    print("开始测试每日利息结算任务")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    print("✓ 数据库初始化完成")
    
    # 手动触发利息结算
    result = await scheduler_service.trigger_settlement_now()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print(f"结果: {result}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_interest_settlement())