# -*- coding: utf-8 -*-
"""
Context Manager
对话上下文管理器
"""

import re
from typing import List, Dict
from .database import AIExpertDatabase

class ContextManager:
    def __init__(self, db: AIExpertDatabase):
        self.db = db
        
        # 异议关键词
        self.objection_keywords = {
            'price': ['贵', '便宜', '价格', '多少钱', '打折', '优惠'],
            'time': ['考虑', '再说', '不着急', '以后', '过段时间'],
            'need': ['不需要', '不合适', '不感兴趣', '算了'],
            'trust': ['骗人', '假的', '不信', '靠谱吗']
        }
    
    def extract_context(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        提取对话上下文
        
        Args:
            session_id: 会话ID
            limit: 最多提取多少条消息
        
        Returns:
            格式化的消息列表 [{"role": "user/assistant", "content": "..."}]
        """
        messages = self.db.get_recent_messages(session_id, limit)
        
        formatted_messages = []
        for msg in messages:
            role = "user" if msg['is_customer'] else "assistant"
            content = msg['message']
            
            # 过滤噪声
            if not self.is_noise(content):
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        return formatted_messages
    
    def is_noise(self, message: str) -> bool:
        """
        判断是否为噪声消息（表情包、系统消息等）
        
        Args:
            message: 消息内容
        
        Returns:
            True 表示是噪声，应该过滤
        """
        # 过滤条件
        if not message or len(message.strip()) == 0:
            return True
        
        # 过滤纯表情
        if re.match(r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+$', message):
            return True
        
        # 过滤系统消息
        system_patterns = [
            r'^\[.*?\]$',  # [图片] [视频] 等
            r'^收到.*?转账',
            r'^.*?拍了拍你',
            r'^.*?撤回了一条消息'
        ]
        
        for pattern in system_patterns:
            if re.match(pattern, message):
                return True
        
        return False
    
    def detect_customer_intent(self, message: str) -> str:
        """
        检测客户意图
        
        Args:
            message: 客户消息
        
        Returns:
            'inquiry' | 'objection' | 'interest' | 'closing' | 'unknown'
        """
        message_lower = message.lower()
        
        # 检测异议
        for objection_type, keywords in self.objection_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return 'objection'
        
        # 检测成交意向
        closing_keywords = ['怎么买', '购买', '下单', '付款', '支付', '要了']
        if any(kw in message_lower for kw in closing_keywords):
            return 'closing'
        
        # 检测兴趣
        interest_keywords = ['了解', '详细', '介绍', '怎么样', '效果']
        if any(kw in message_lower for kw in interest_keywords):
            return 'interest'
        
        # 检测咨询
        inquiry_keywords = ['?', '？', '吗', '呢', '什么', '哪个', '多少']
        if any(kw in message_lower for kw in inquiry_keywords):
            return 'inquiry'
        
        return 'unknown'
    
    def detect_objection_type(self, message: str) -> str:
        """
        检测异议类型
        
        Args:
            message: 客户消息
        
        Returns:
            'price' | 'time' | 'need' | 'trust' | 'none'
        """
        message_lower = message.lower()
        
        for objection_type, keywords in self.objection_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return objection_type
        
        return 'none'
    
    def summarize_long_context(self, messages: List[Dict]) -> str:
        """
        压缩长对话上下文
        
        Args:
            messages: 消息列表
        
        Returns:
            摘要文本
        """
        if len(messages) <= 10:
            return ""
        
        # 简单摘要：提取前3轮和后7轮
        early_messages = messages[:6]  # 前3轮（客户+销售）
        recent_messages = messages[-14:]  # 后7轮
        
        summary = "【早期对话摘要】\n"
        for msg in early_messages:
            role = "客户" if msg['role'] == 'user' else "销售"
            summary += f"{role}: {msg['content'][:50]}...\n"
        
        summary += "\n【最近对话】\n"
        for msg in recent_messages:
            role = "客户" if msg['role'] == 'user' else "销售"
            summary += f"{role}: {msg['content']}\n"
        
        return summary
    
    def build_context_for_ai(self, session_id: str, current_message: str) -> List[Dict]:
        """
        为 AI 构建完整的上下文
        
        Args:
            session_id: 会话ID
            current_message: 当前客户消息
        
        Returns:
            完整的消息列表（包含历史和当前消息）
        """
        # 获取历史上下文
        history = self.extract_context(session_id, limit=10)
        
        # 添加当前消息
        history.append({
            "role": "user",
            "content": current_message
        })
        
        return history

