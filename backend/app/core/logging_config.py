"""
日志配置模块
配置应用的日志系统,包括文件日志和控制台日志
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    配置应用日志系统
    
    Args:
        log_level: 日志级别,如果未指定则使用配置文件中的设置
    
    Returns:
        配置好的logger实例
    """
    # 确定日志级别
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建根logger
    logger = logging.getLogger("starpy")
    logger.setLevel(numeric_level)
    
    # 如果已经配置过处理器,则不重复配置
    if logger.handlers:
        return logger
    
    # 定义日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 文件处理器 - 使用RotatingFileHandler实现日志轮转
    log_file = log_dir / settings.LOG_FILE
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # 2. 控制台处理器 - 用于开发调试
    if settings.APP_DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
    
    # 记录初始化信息
    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {level}")
    logger.info(f"日志文件: {log_file.absolute()}")
    logger.info(f"日志大小限制: {settings.LOG_MAX_BYTES / 1024 / 1024:.1f}MB")
    logger.info(f"保留文件数: {settings.LOG_BACKUP_COUNT}")
    logger.info("=" * 60)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger
    
    Args:
        name: logger名称,通常使用模块的__name__
    
    Returns:
        logger实例
    """
    return logging.getLogger(f"starpy.{name}")