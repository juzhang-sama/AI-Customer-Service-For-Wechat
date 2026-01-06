# -*- coding: utf-8 -*-
"""
Smart Context Selector
智能上下文选择器 - 改进点1
"""

import re
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class SmartContextSelector:
    """智能选择对话上下文，过滤噪声，识别话题转换"""
    
    def __init__(self):
        # 噪声模式（低价值消息）
        self.noise_patterns = [
            r'^[表情]$',  # 纯表情
            r'^\[.*\]$',  # 纯表情符号
            r'^在吗\??$',
            r'^嗯+$',
            r'^哦+$',
            r'^好的?$',
            r'^收到$',
            r'^明白$',
            r'^知道了$',
            r'^\?+$',
            r'^\.+$',
        ]
        
        # 话题转换关键词
        self.topic_change_keywords = [
            '对了', '另外', '还有', '换个话题', '问一下',
            '再问', '顺便问', '想了解', '咨询一下'
        ]
        
        # 高价值关键词（重要信息）
        self.high_value_keywords = [
            '价格', '多少钱', '费用', '成本',
            '效果', '怎么样', '好不好',
            '什么时候', '多久', '时间',
            '地址', '位置', '在哪',
            '怎么', '如何', '能不能',
            '购买', '下单', '付款', '支付',
            '优惠', '打折', '活动',
            '对比', '区别', '差异',
            '保证', '保障', '售后',
        ]
    
    def select_context(
        self, 
        messages: List[Dict], 
        max_tokens: int = 2000,
        min_messages: int = 3,
        customer_message: str = None,
        deepseek_adapter = None
    ) -> Tuple[List[Dict], Dict]:
        """
        智能选择上下文
        
        Args:
            messages: 原始消息列表
            max_tokens: 最大token数
            min_messages: 最少保留的消息数
            customer_message: 当前客户发送的消息（用于提取关键词）
            deepseek_adapter: DeepSeekAdapter实例（用于调用LLM）
        
        Returns:
            (selected_messages, metadata)
        """
        if not messages:
            return [], {"filtered_count": 0, "topic_changes": [], "high_value_count": 0}
        
        # 1. 过滤噪声
        filtered_messages = self._filter_noise(messages)
        
        # 2. 识别话题转换点
        topic_changes = self._detect_topic_changes(filtered_messages)
        
        # 3. 如果有话题转换，只保留最后一个话题的消息
        if topic_changes:
            last_topic_start = topic_changes[-1]
            filtered_messages = filtered_messages[last_topic_start:]
        
        # 4. 标记高价值消息 (混合模式：静态关键词 + 动态语义关键词)
        search_keywords = []
        if customer_message and deepseek_adapter:
            # 使用 LLM 提取动态关键词
            search_keywords = deepseek_adapter.extract_search_keywords(customer_message)
            print(f"[SmartContext] Extracted keywords: {search_keywords}")
        
        high_value_indices = self._mark_high_value_messages(filtered_messages, dynamic_keywords=search_keywords)
        
        # 5. 根据token限制选择消息
        selected_messages = self._select_by_token_limit(
            filtered_messages, 
            max_tokens, 
            min_messages,
            high_value_indices
        )
        
        # 6. 生成元数据
        metadata = {
            "filtered_count": len(messages) - len(filtered_messages),
            "topic_changes": topic_changes,
            "high_value_count": len(high_value_indices),
            "total_selected": len(selected_messages),
            "search_keywords": search_keywords
        }
        
        return selected_messages, metadata
    
    def _filter_noise(self, messages: List[Dict]) -> List[Dict]:
        """过滤噪声消息"""
        filtered = []
        for msg in messages:
            content = msg.get('content', '').strip()
            
            # 检查是否是噪声
            is_noise = False
            for pattern in self.noise_patterns:
                if re.match(pattern, content, re.IGNORECASE):
                    is_noise = True
                    break
            
            # 保留非噪声消息
            if not is_noise and len(content) > 0:
                filtered.append(msg)
        
        return filtered
    
    def _detect_topic_changes(self, messages: List[Dict]) -> List[int]:
        """检测话题转换点（返回转换点的索引）"""
        topic_changes = []
        
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            
            # 检查是否包含话题转换关键词
            for keyword in self.topic_change_keywords:
                if keyword in content:
                    topic_changes.append(i)
                    break
        
        return topic_changes
    
    def _mark_high_value_messages(self, messages: List[Dict], dynamic_keywords: List[str] = None) -> List[int]:
        """
        标记高价值消息（返回索引列表）
        结合静态关键词和动态关键词
        """
        high_value_indices = []
        
        # 合并关键词集合
        all_keywords = self.high_value_keywords.copy()
        if dynamic_keywords:
            all_keywords.extend(dynamic_keywords)
            
        # 去重
        all_keywords = list(set(all_keywords))
        
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            
            # 检查是否包含任何关键词
            for keyword in all_keywords:
                if keyword in content:
                    high_value_indices.append(i)
                    break
        
        return high_value_indices
    
    def _select_by_token_limit(
        self, 
        messages: List[Dict], 
        max_tokens: int,
        min_messages: int,
        high_value_indices: List[int]
    ) -> List[Dict]:
        """根据token限制选择消息，优先保留高价值消息"""
        if len(messages) <= min_messages:
            return messages
        
        # 粗略估算token数（1个汉字≈2tokens，1个英文单词≈1token）
        def estimate_tokens(text: str) -> int:
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            english_words = len(re.findall(r'[a-zA-Z]+', text))
            return chinese_chars * 2 + english_words
        
        # 从后往前选择消息
        selected = []
        total_tokens = 0
        
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            msg_tokens = estimate_tokens(msg.get('content', ''))
            
            # 如果是高价值消息，优先保留
            if i in high_value_indices:
                selected.insert(0, msg)
                total_tokens += msg_tokens
            # 如果还有token空间，保留
            elif total_tokens + msg_tokens <= max_tokens:
                selected.insert(0, msg)
                total_tokens += msg_tokens
            # 如果已经达到最少消息数，停止
            elif len(selected) >= min_messages:
                break
        
        # 确保至少保留min_messages条
        if len(selected) < min_messages:
            return messages[-min_messages:]
        
        return selected

