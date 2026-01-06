# -*- coding: utf-8 -*-
"""
Feedback Learner
反馈学习管理器 - 改进点5
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from .database import AIExpertDatabase

class FeedbackLearner:
    """学习用户反馈，优化回复质量"""
    
    def __init__(self, db: AIExpertDatabase):
        self.db = db
        self._init_feedback_tables()
    
    def _init_feedback_tables(self):
        """初始化反馈学习表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 版本选择记录
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_selection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                customer_message TEXT,
                selected_version TEXT,  -- aggressive/conservative/professional
                suggestion_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 回复修改记录
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reply_modification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                original_reply TEXT,
                modified_reply TEXT,
                modification_type TEXT,  -- length/tone/content
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 客户响应效果
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_response (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                our_reply TEXT,
                customer_response TEXT,
                response_type TEXT,  -- positive/negative/neutral
                response_time INTEGER,  -- 响应时间（秒）
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_version_selection(
        self, 
        session_id: str, 
        customer_message: str,
        selected_version: str,
        suggestion_id: int = None
    ):
        """记录用户选择的版本"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO version_selection 
            (session_id, customer_message, selected_version, suggestion_id)
            VALUES (?, ?, ?, ?)
        """, (session_id, customer_message, selected_version, suggestion_id))
        
        conn.commit()
        conn.close()
    
    def record_modification(
        self,
        session_id: str,
        original_reply: str,
        modified_reply: str
    ):
        """记录用户对回复的修改"""
        # 分析修改类型
        modification_type = self._analyze_modification(original_reply, modified_reply)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reply_modification
            (session_id, original_reply, modified_reply, modification_type)
            VALUES (?, ?, ?, ?)
        """, (session_id, original_reply, modified_reply, modification_type))
        
        conn.commit()
        conn.close()
    
    def record_customer_response(
        self,
        session_id: str,
        our_reply: str,
        customer_response: str,
        response_time: int = None
    ):
        """记录客户对我们回复的响应"""
        # 分析响应类型
        response_type = self._analyze_response_type(customer_response)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO customer_response
            (session_id, our_reply, customer_response, response_type, response_time)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, our_reply, customer_response, response_type, response_time))
        
        conn.commit()
        conn.close()
    
    def get_version_preference(self, session_id: str = None) -> Dict:
        """获取版本偏好统计"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if session_id:
            # 特定会话的偏好
            cursor.execute("""
                SELECT selected_version, COUNT(*) as count
                FROM version_selection
                WHERE session_id = ?
                GROUP BY selected_version
                ORDER BY count DESC
            """, (session_id,))
        else:
            # 全局偏好
            cursor.execute("""
                SELECT selected_version, COUNT(*) as count
                FROM version_selection
                GROUP BY selected_version
                ORDER BY count DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        total = sum(row['count'] for row in rows)
        
        preferences = {}
        for row in rows:
            version = row['selected_version']
            count = row['count']
            preferences[version] = {
                'count': count,
                'percentage': round(count / total * 100, 2) if total > 0 else 0
            }
        
        return preferences
    
    def get_modification_patterns(self, limit: int = 10) -> List[Dict]:
        """获取修改模式（学习用户如何修改回复）"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reply_modification
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_effective_replies(self, limit: int = 20) -> List[Dict]:
        """获取效果好的回复（客户响应积极）"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customer_response
            WHERE response_type = 'positive'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def _analyze_modification(self, original: str, modified: str) -> str:
        """分析修改类型"""
        len_diff = len(modified) - len(original)
        
        if abs(len_diff) > 20:
            return 'length'  # 长度调整
        elif '😊' in modified and '😊' not in original:
            return 'tone'  # 语气调整
        else:
            return 'content'  # 内容调整
    
    def _analyze_response_type(self, response: str) -> str:
        """分析客户响应类型"""
        positive_keywords = ['好的', '可以', '不错', '谢谢', '明白', '了解']
        negative_keywords = ['不', '算了', '不需要', '再说']
        
        response_lower = response.lower()
        
        positive_count = sum(1 for kw in positive_keywords if kw in response_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in response_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

