# -*- coding: utf-8 -*-
"""
Config Manager - 统一配置管理
从环境变量和配置文件加载配置，优先级：环境变量 > .env 文件 > 默认值
"""

import os
from pathlib import Path
from typing import Optional

# 尝试加载 python-dotenv
try:
    from dotenv import load_dotenv
    # 加载 .env 文件
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[Config] Loaded .env from {env_path}")
except ImportError:
    print("[Config] python-dotenv not installed, using environment variables only")


class Config:
    """应用配置类"""
    
    # ========== 安全配置 ==========
    @staticmethod
    def get_jwt_secret() -> str:
        """获取 JWT 密钥"""
        return os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @staticmethod
    def get_app_api_key() -> Optional[str]:
        """获取应用 API Key"""
        return os.environ.get('APP_API_KEY')
    
    # ========== DeepSeek API 配置 ==========
    @staticmethod
    def get_deepseek_api_key() -> str:
        """获取 DeepSeek API Key (优先环境变量，其次配置文件)"""
        # 1. 优先从环境变量获取
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if api_key:
            return api_key

        # 2. 兼容旧版：从 ai_config.json 获取
        import json
        # 配置文件在项目根目录的 config 文件夹中
        # python/ai_expert/config.py -> python/ai_expert -> python -> 项目根目录 -> config
        config_path = Path(__file__).parent.parent.parent / 'config' / 'ai_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('deepseek_api_key', '')
            except Exception:
                pass

        return ''
    
    # ========== CORS 配置 ==========
    @staticmethod
    def get_allowed_origins() -> list:
        """获取允许的 CORS 域名"""
        origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000')
        return [o.strip() for o in origins.split(',')]
    
    # ========== 数据库配置 ==========
    @staticmethod
    def get_database_path() -> str:
        """获取数据库路径"""
        return os.environ.get('DATABASE_PATH', 'ai_expert.db')
    
    # ========== 监控配置 ==========
    @staticmethod
    def get_monitor_keyword() -> str:
        """获取监控关键词"""
        return os.environ.get('MONITOR_KEYWORD', '客户')
    
    @staticmethod
    def get_monitor_match_mode() -> str:
        """获取监控匹配模式"""
        return os.environ.get('MONITOR_MATCH_MODE', 'contains')
    
    # ========== 日志配置 ==========
    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return os.environ.get('LOG_LEVEL', 'INFO')
    
    # ========== 环境判断 ==========
    @staticmethod
    def is_production() -> bool:
        """是否为生产环境"""
        return os.environ.get('FLASK_ENV', 'development') == 'production'
    
    @staticmethod
    def is_debug() -> bool:
        """是否为调试模式"""
        return os.environ.get('FLASK_DEBUG', '0') == '1'


# 全局配置实例
config = Config()

