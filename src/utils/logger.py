"""日志配置模块"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logger(
    name: str = "mi-monitor",
    log_file: Optional[str] = None,
    level: str = "INFO",
    max_size: int = 10,
    backup_count: int = 5,
    console: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_size: 日志文件最大大小(MB)
        backup_count: 保留的日志文件数量
        console: 是否输出到控制台
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过,直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size * 1024 * 1024,  # 转换为字节
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 添加控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 使用彩色日志(如果可用)
        if COLORLOG_AVAILABLE:
            color_format = (
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s'
            )
            console_formatter = colorlog.ColoredFormatter(
                color_format,
                datefmt=date_format,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            console_formatter = logging.Formatter(log_format, date_format)
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器
    """
    return logging.getLogger(name)
