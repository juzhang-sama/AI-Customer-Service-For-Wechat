# -*- coding: utf-8 -*-
"""
Logger - 统一日志配置模块
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = 'ai_expert',
    level: int = logging.INFO,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    配置并返回 logger 实例
    
    Args:
        name: logger 名称
        level: 日志级别
        log_format: 日志格式
    
    Returns:
        配置好的 logger 实例
    """
    if log_format is None:
        log_format = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if not logger.handlers:
        logger.setLevel(level)
        
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S'))
        
        logger.addHandler(console_handler)
    
    return logger


# 预配置的 logger 实例
logger = setup_logger('ai_expert')

# 子模块 logger
api_logger = setup_logger('ai_expert.api')
db_logger = setup_logger('ai_expert.db')
generator_logger = setup_logger('ai_expert.generator')
sse_logger = setup_logger('ai_expert.sse')

