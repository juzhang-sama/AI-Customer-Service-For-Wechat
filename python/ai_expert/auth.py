# -*- coding: utf-8 -*-
"""
API Authentication Module
API 认证模块 - 支持 JWT 和 API Key 两种认证方式
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, Tuple

# JWT 是可选依赖
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    jwt = None
    JWT_AVAILABLE = False
    print("[WARN] PyJWT not installed, JWT authentication disabled")

# 配置常量 (生产环境应从环境变量读取)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
API_KEY_HEADER = 'X-API-Key'

class AuthManager:
    """认证管理器"""
    
    def __init__(self, db=None):
        self.db = db
        self._api_keys_cache = {}  # 简单缓存
        self._cache_ttl = 300  # 5分钟缓存
        self._cache_time = None
    
    # ========== JWT 认证 ==========

    def generate_jwt_token(self, user_id: str, role: str = 'user') -> str:
        """生成 JWT Token"""
        if not JWT_AVAILABLE:
            raise RuntimeError("JWT authentication not available. Please install PyJWT.")
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def verify_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """验证 JWT Token"""
        if not JWT_AVAILABLE:
            return False, {'error': 'JWT authentication not available'}
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token已过期'}
        except jwt.InvalidTokenError:
            return False, {'error': 'Token无效'}
    
    # ========== API Key 认证 ==========
    
    def generate_api_key(self) -> str:
        """生成新的 API Key"""
        return f"sk-{secrets.token_hex(24)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """对 API Key 进行哈希处理（存储用）"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict]]:
        """验证 API Key"""
        if not api_key:
            return False, {'error': 'API Key 缺失'}
        
        # 检查缓存
        if self._is_cache_valid() and api_key in self._api_keys_cache:
            return True, self._api_keys_cache[api_key]
        
        # 从数据库验证 (如果有数据库)
        if self.db:
            hashed_key = self.hash_api_key(api_key)
            # 这里需要在数据库中添加 api_keys 表
            # 简化版：直接检查环境变量中的 API Key
        
        # 简化版：检查环境变量
        valid_key = os.environ.get('APP_API_KEY')
        if valid_key and api_key == valid_key:
            user_info = {'user_id': 'default', 'role': 'admin'}
            self._api_keys_cache[api_key] = user_info
            self._cache_time = datetime.now()
            return True, user_info
        
        return False, {'error': 'API Key 无效'}
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_time is None:
            return False
        return (datetime.now() - self._cache_time).seconds < self._cache_ttl


# ========== Flask 装饰器 ==========

auth_manager = AuthManager()

def require_auth(f):
    """
    认证装饰器 - 支持 JWT 和 API Key 两种方式
    
    使用方式:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            user = g.current_user  # 获取当前用户信息
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. 尝试 JWT 认证 (Authorization: Bearer <token>)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            valid, result = auth_manager.verify_jwt_token(token)
            if valid:
                g.current_user = result
                return f(*args, **kwargs)
            else:
                return jsonify({'success': False, 'error': result.get('error')}), 401
        
        # 2. 尝试 API Key 认证 (X-API-Key: <key>)
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key:
            valid, result = auth_manager.verify_api_key(api_key)
            if valid:
                g.current_user = result
                return f(*args, **kwargs)
            else:
                return jsonify({'success': False, 'error': result.get('error')}), 401
        
        # 3. 无认证信息
        return jsonify({
            'success': False, 
            'error': '需要认证。请提供 Authorization header (Bearer token) 或 X-API-Key header'
        }), 401
    
    return decorated


def optional_auth(f):
    """可选认证装饰器 - 有认证信息则验证，无则跳过"""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user = None
        
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            valid, result = auth_manager.verify_jwt_token(token)
            if valid:
                g.current_user = result
        
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key and g.current_user is None:
            valid, result = auth_manager.verify_api_key(api_key)
            if valid:
                g.current_user = result
        
        return f(*args, **kwargs)
    
    return decorated

