# -*- coding: utf-8 -*-
"""
Unit Tests - AI Expert 模块单元测试
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_expert.rate_limiter import RateLimiter
from ai_expert.error_handler import (
    ValidationError, APIKeyError, ExternalAPIError,
    validate_required_fields
)
from ai_expert.constants import (
    RATE_LIMIT_AI_GENERATE, RATE_LIMIT_WINDOW,
    MAX_MESSAGES_PER_SESSION
)


class TestRateLimiter:
    """速率限制器测试"""
    
    def test_rate_limiter_allows_requests_under_limit(self):
        """测试在限制内的请求应该被允许"""
        limiter = RateLimiter()
        
        # 模拟请求
        for i in range(5):
            allowed, info = limiter.is_allowed(10, 60)
            assert allowed is True
            assert info['remaining'] == 10 - i - 1
    
    def test_rate_limiter_blocks_requests_over_limit(self):
        """测试超过限制的请求应该被阻止"""
        limiter = RateLimiter()
        
        # 先发送达到限制的请求
        for _ in range(10):
            limiter.is_allowed(10, 60)
        
        # 下一个请求应该被阻止
        allowed, info = limiter.is_allowed(10, 60)
        assert allowed is False
        assert info['remaining'] == 0


class TestErrorHandler:
    """错误处理器测试"""
    
    def test_validation_error_properties(self):
        """测试 ValidationError 属性"""
        error = ValidationError('测试错误', details={'field': 'test'})
        
        assert error.status_code == 400
        assert error.error_code == 'VALIDATION_ERROR'
        assert error.details == {'field': 'test'}
    
    def test_api_key_error_properties(self):
        """测试 APIKeyError 属性"""
        error = APIKeyError('API Key 未配置')
        
        assert error.status_code == 500
        assert error.error_code == 'API_KEY_ERROR'
    
    def test_external_api_error_properties(self):
        """测试 ExternalAPIError 属性"""
        error = ExternalAPIError('外部服务不可用')
        
        assert error.status_code == 502
        assert error.error_code == 'EXTERNAL_API_ERROR'
    
    def test_error_to_dict(self):
        """测试错误转换为字典"""
        error = ValidationError('参数无效', details={'missing': ['name']})
        result = error.to_dict()
        
        assert result['success'] is False
        assert result['error_code'] == 'VALIDATION_ERROR'
        assert result['details'] == {'missing': ['name']}
    
    def test_validate_required_fields_success(self):
        """测试必填字段验证 - 成功"""
        data = {'name': 'test', 'value': 123}
        valid, msg = validate_required_fields(data, ['name', 'value'])
        
        assert valid is True
        assert msg == ''
    
    def test_validate_required_fields_failure(self):
        """测试必填字段验证 - 失败"""
        data = {'name': 'test'}
        valid, msg = validate_required_fields(data, ['name', 'value'])
        
        assert valid is False
        assert 'value' in msg


class TestConstants:
    """常量测试"""
    
    def test_rate_limit_values(self):
        """测试速率限制常量值"""
        assert RATE_LIMIT_AI_GENERATE == 20
        assert RATE_LIMIT_WINDOW == 60
    
    def test_message_constants(self):
        """测试消息相关常量"""
        assert MAX_MESSAGES_PER_SESSION == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

