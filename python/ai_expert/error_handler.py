# -*- coding: utf-8 -*-
"""
Error Handler - 统一错误处理模块
提供细化的异常类型和用户友好的错误消息
"""

import logging
import traceback
from functools import wraps
from flask import jsonify
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


# ========== 自定义异常类 ==========

class AIExpertError(Exception):
    """AI 专家模块基础异常"""
    status_code = 500
    error_code = "INTERNAL_ERROR"
    user_message = "服务器内部错误，请稍后重试"
    
    def __init__(self, message: str = None, details: Dict = None):
        self.message = message or self.user_message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': False,
            'error': self.user_message,
            'error_code': self.error_code,
            'details': self.details if self.details else None
        }


class ValidationError(AIExpertError):
    """参数验证错误"""
    status_code = 400
    error_code = "VALIDATION_ERROR"
    user_message = "请求参数无效"


class AuthenticationError(AIExpertError):
    """认证错误"""
    status_code = 401
    error_code = "AUTH_ERROR"
    user_message = "认证失败，请检查凭证"


class NotFoundError(AIExpertError):
    """资源不存在"""
    status_code = 404
    error_code = "NOT_FOUND"
    user_message = "请求的资源不存在"


class RateLimitError(AIExpertError):
    """频率限制错误"""
    status_code = 429
    error_code = "RATE_LIMIT"
    user_message = "请求过于频繁，请稍后再试"


class APIKeyError(AIExpertError):
    """API Key 配置错误"""
    status_code = 500
    error_code = "API_KEY_ERROR"
    user_message = "AI 服务配置错误，请联系管理员"


class ExternalAPIError(AIExpertError):
    """外部 API 调用错误"""
    status_code = 502
    error_code = "EXTERNAL_API_ERROR"
    user_message = "AI 服务暂时不可用，请稍后重试"


class DatabaseError(AIExpertError):
    """数据库错误"""
    status_code = 500
    error_code = "DATABASE_ERROR"
    user_message = "数据服务异常，请稍后重试"


# ========== 错误处理装饰器 ==========

def handle_errors(f):
    """
    统一错误处理装饰器
    
    使用方式:
        @app.route('/api/example')
        @handle_errors
        def example():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except AIExpertError as e:
            # 自定义异常 - 返回用户友好消息
            logger.warning(f"[{e.error_code}] {e.message}", extra={'details': e.details})
            return jsonify(e.to_dict()), e.status_code
        
        except ValueError as e:
            # 值错误 - 通常是参数问题
            logger.warning(f"[VALIDATION] {str(e)}")
            return jsonify({
                'success': False,
                'error': '参数格式错误',
                'error_code': 'VALIDATION_ERROR',
                'details': {'message': str(e)}
            }), 400
        
        except ConnectionError as e:
            # 连接错误
            logger.error(f"[CONNECTION] {str(e)}")
            return jsonify({
                'success': False,
                'error': '网络连接失败，请检查网络',
                'error_code': 'CONNECTION_ERROR'
            }), 503
        
        except TimeoutError as e:
            # 超时错误
            logger.error(f"[TIMEOUT] {str(e)}")
            return jsonify({
                'success': False,
                'error': '请求超时，请稍后重试',
                'error_code': 'TIMEOUT_ERROR'
            }), 504
        
        except Exception as e:
            # 未知错误 - 记录详细日志但返回通用消息
            logger.exception(f"[UNEXPECTED] Unhandled exception in {f.__name__}")
            return jsonify({
                'success': False,
                'error': '服务器内部错误，请稍后重试',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated


# ========== 辅助函数 ==========

def validate_required_fields(data: Dict, required: list) -> Tuple[bool, str]:
    """
    验证必填字段
    
    Returns:
        (是否有效, 错误消息)
    """
    missing = [field for field in required if not data.get(field)]
    if missing:
        return False, f"缺少必填字段: {', '.join(missing)}"
    return True, ""

