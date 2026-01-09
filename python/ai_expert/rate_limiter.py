# -*- coding: utf-8 -*-
"""
Rate Limiter - 请求频率限制器
基于滑动窗口算法的简单实现
"""

import time
import threading
from functools import wraps
from flask import request, jsonify
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """滑动窗口速率限制器"""
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def _get_client_id(self) -> str:
        """获取客户端标识（IP + User-Agent）"""
        ip = request.remote_addr or 'unknown'
        # 可以加入更多标识
        return ip
    
    def _cleanup_old_requests(self, client_id: str, window_seconds: int):
        """清理过期的请求记录"""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > cutoff
        ]
    
    def is_allowed(self, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        """
        检查请求是否被允许
        
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            (是否允许, 限制信息)
        """
        client_id = self._get_client_id()
        now = time.time()
        
        with self._lock:
            self._cleanup_old_requests(client_id, window_seconds)
            current_count = len(self._requests[client_id])
            
            if current_count >= max_requests:
                # 计算重置时间
                oldest = min(self._requests[client_id]) if self._requests[client_id] else now
                reset_after = int(oldest + window_seconds - now)
                
                return False, {
                    'limit': max_requests,
                    'remaining': 0,
                    'reset_after': max(reset_after, 1),
                    'window': window_seconds
                }
            
            # 记录本次请求
            self._requests[client_id].append(now)
            
            return True, {
                'limit': max_requests,
                'remaining': max_requests - current_count - 1,
                'reset_after': window_seconds,
                'window': window_seconds
            }


# 全局限制器实例
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    速率限制装饰器
    
    Args:
        max_requests: 时间窗口内最大请求数 (默认 60)
        window_seconds: 时间窗口秒数 (默认 60)
    
    使用示例:
        @app.route('/api/generate')
        @rate_limit(max_requests=10, window_seconds=60)  # 每分钟最多10次
        def generate():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            allowed, info = rate_limiter.is_allowed(max_requests, window_seconds)
            
            if not allowed:
                response = jsonify({
                    'success': False,
                    'error': '请求过于频繁，请稍后再试',
                    'rate_limit': info
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_after'])
                return response
            
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 添加速率限制头
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            
            return response
        
        return decorated
    return decorator


# 预定义的限制级别
def rate_limit_strict(f):
    """严格限制: 每分钟 10 次（用于 AI 生成等昂贵操作）"""
    return rate_limit(max_requests=10, window_seconds=60)(f)

def rate_limit_normal(f):
    """普通限制: 每分钟 60 次"""
    return rate_limit(max_requests=60, window_seconds=60)(f)

def rate_limit_relaxed(f):
    """宽松限制: 每分钟 120 次"""
    return rate_limit(max_requests=120, window_seconds=60)(f)

