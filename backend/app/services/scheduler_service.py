"""
定时任务调度器服务
使用APScheduler实现每日利息结算等定时任务
"""
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import SavingsBox

# 配置日志
logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度器服务"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    def setup_scheduler(self) -> AsyncIOScheduler:
        """
        创建并配置APScheduler调度器
        
        Returns:
            AsyncIOScheduler: 配置好的调度器实例
        """
        if self.scheduler is not None:
            logger.warning("调度器已存在,跳过重复初始化")
            return self.scheduler
        
        # 创建调度器实例
        self.scheduler = AsyncIOScheduler()
        
        # 添加每日利息结算任务
        # 每天凌晨0:05执行（避开0点整点可能的系统负载）
        # ⚠️ 诊断日志: 检查时区配置
        trigger = CronTrigger(hour=0, minute=5, timezone='Asia/Shanghai')
        self.scheduler.add_job(
            self.daily_interest_settlement_job,
            trigger=trigger,
            id='daily_interest_settlement',
            name='每日利息结算',
            replace_existing=True
        )
        
        logger.info("=" * 60)
        logger.info("定时任务调度器配置完成")
        logger.info(f"已添加任务: 每日利息结算")
        logger.info(f"触发器配置: {trigger}")
        logger.info(f"时区: Asia/Shanghai")
        logger.info(f"执行时间: 每天 00:05 (Asia/Shanghai)")
        logger.info("=" * 60)
        
        return self.scheduler
    
    async def daily_interest_settlement_job(self):
        """
        每日利息结算任务
        
        业务逻辑:
        1. 获取所有存钱罐
        2. 遍历每个存钱罐，计算并结算利息
        3. 记录执行结果和错误
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"开始执行每日利息结算任务 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        success_count = 0
        error_count = 0
        total_interest = 0.0
        
        # 创建独立的数据库会话
        async with AsyncSessionLocal() as db:
            try:
                # 1. 获取所有存钱罐
                result = await db.execute(select(SavingsBox))
                savings_boxes = result.scalars().all()
                
                total_count = len(savings_boxes)
                logger.info(f"共找到 {total_count} 个存钱罐需要结算")
                
                # 2. 遍历每个存钱罐进行利息结算
                for savings_box in savings_boxes:
                    try:
                        # 🔍 诊断日志: 打印存钱罐详细信息
                        logger.info(
                            f"📊 检查存钱罐 [ID={savings_box.id}, child_id={savings_box.child_id}] "
                            f"余额=¥{savings_box.balance}, "
                            f"last_interest_date={savings_box.last_interest_date}, "
                            f"interest_rate={savings_box.interest_rate}"
                        )
                        
                        # 计算待结算利息
                        interest = savings_box.calculate_pending_interest()
                        
                        # 🔍 诊断日志: 打印计算结果
                        logger.info(f"💰 计算待结算利息: ¥{interest}")
                        
                        if interest > 0:
                            # 导入WalletService进行结算
                            from app.services.wallet_service import WalletService
                            wallet_service = WalletService(db)
                            
                            # 结算利息
                            settled_interest = await wallet_service.calculate_and_settle_interest(
                                savings_box
                            )
                            
                            # 🔧 修复: 在外层会话中再次提交，确保事务真正持久化
                            await db.commit()
                            
                            success_count += 1
                            total_interest += float(settled_interest)
                            
                            logger.info(
                                f"✓ 小朋友ID={savings_box.child_id} 利息结算成功: "
                                f"¥{settled_interest:.2f} (余额: ¥{savings_box.balance:.2f})"
                            )
                        else:
                            # 无需结算（余额为0或已结算）
                            logger.debug(
                                f"- 小朋友ID={savings_box.child_id} 无需结算 "
                                f"(余额: ¥{savings_box.balance:.2f})"
                            )
                    
                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"✗ 小朋友ID={savings_box.child_id} 利息结算失败: {str(e)}",
                            exc_info=True
                        )
                        # 继续处理下一个账户，不中断整个任务
                        continue
                
            except Exception as e:
                logger.error(f"利息结算任务执行失败: {str(e)}", exc_info=True)
                raise
        
        # 3. 记录执行结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("每日利息结算任务执行完成")
        logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"执行耗时: {duration:.2f} 秒")
        logger.info(f"成功结算: {success_count} 个")
        logger.info(f"失败数量: {error_count} 个")
        logger.info(f"总利息: ¥{total_interest:.2f}")
        logger.info("=" * 60)
    
    def start(self):
        """启动调度器"""
        if self.scheduler is None:
            raise RuntimeError("调度器未初始化，请先调用 setup_scheduler()")
        
        self.scheduler.start()
        
        # 🔍 诊断日志: 打印调度器状态和所有任务
        logger.info("=" * 60)
        logger.info("定时任务调度器已启动")
        logger.info(f"调度器状态: {self.scheduler.state}")
        logger.info("已注册的任务列表:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - [{job.id}] {job.name}")
            logger.info(f"    触发器: {job.trigger}")
            logger.info(f"    下次执行: {job.next_run_time}")
        logger.info("=" * 60)
    
    def shutdown(self, wait: bool = True):
        """
        关闭调度器
        
        Args:
            wait: 是否等待正在执行的任务完成
        """
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=wait)
            logger.info("定时任务调度器已关闭")
    
    async def trigger_settlement_now(self) -> dict:
        """
        手动触发利息结算（用于测试）
        
        Returns:
            dict: 执行结果
        """
        logger.info("手动触发利息结算任务")
        await self.daily_interest_settlement_job()
        return {
            "success": True,
            "message": "利息结算任务已手动触发完成"
        }


# 全局调度器实例
scheduler_service = SchedulerService()