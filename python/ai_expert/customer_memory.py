# -*- coding: utf-8 -*-
"""
Customer Memory
客户个性化记忆管理器 - 改进点3
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from .database import AIExpertDatabase

class CustomerStage:
    """客户阶段"""
    COLD = "cold"  # 冷线索
    WARM = "warm"  # 温线索
    HOT = "hot"  # 热线索
    CUSTOMER = "customer"  # 已成交客户
    LOST = "lost"  # 流失客户

class CustomerMemory:
    """管理客户的个性化记忆"""
    
    def __init__(self, db: AIExpertDatabase):
        self.db = db
        self._init_memory_table()
    
    def _init_memory_table(self):
        """初始化客户记忆表"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_memory (
                session_id TEXT PRIMARY KEY,
                customer_name TEXT,
                stage TEXT DEFAULT 'cold',
                preferences TEXT,  -- JSON: {"price_sensitive": bool, "concerns": [], "interests": []}
                provided_info TEXT,  -- JSON: 已提供的信息列表
                interaction_count INTEGER DEFAULT 0,
                last_intent TEXT,
                last_objection_type TEXT,
                notes TEXT,  -- 销售备注
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        # 不要关闭连接，因为它是共享的线程本地连接
    
    def get_memory(self, session_id: str) -> Dict:
        """获取客户记忆"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customer_memory WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            memory = dict(row)
            # 解析JSON字段
            memory['preferences'] = json.loads(memory.get('preferences') or '{}')
            memory['provided_info'] = json.loads(memory.get('provided_info') or '[]')
            return memory
        
        # 如果没有记忆，返回默认值
        return {
            'session_id': session_id,
            'customer_name': None,
            'stage': CustomerStage.COLD,
            'preferences': {},
            'provided_info': [],
            'interaction_count': 0,
            'last_intent': None,
            'last_objection_type': None,
            'notes': ''
        }
    
    def update_memory(self, session_id: str, updates: Dict):
        """更新客户记忆"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 检查是否存在
        cursor.execute("SELECT session_id FROM customer_memory WHERE session_id = ?", (session_id,))
        exists = cursor.fetchone()
        
        if exists:
            # 更新
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key in ['preferences', 'provided_info']:
                    value = json.dumps(value, ensure_ascii=False)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            values.append(datetime.now())
            values.append(session_id)
            
            sql = f"""
                UPDATE customer_memory 
                SET {', '.join(set_clauses)}, updated_at = ?
                WHERE session_id = ?
            """
            cursor.execute(sql, values)
        else:
            # 插入
            fields = ['session_id'] + list(updates.keys())
            placeholders = ['?'] * len(fields)
            
            values = [session_id]
            for key in updates.keys():
                value = updates[key]
                if key in ['preferences', 'provided_info']:
                    value = json.dumps(value, ensure_ascii=False)
                values.append(value)
            
            sql = f"""
                INSERT INTO customer_memory ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
            """
            cursor.execute(sql, values)
        
        conn.commit()
        conn.close()
    
    def add_preference(self, session_id: str, preference_key: str, preference_value):
        """添加客户偏好"""
        memory = self.get_memory(session_id)
        preferences = memory['preferences']
        preferences[preference_key] = preference_value
        
        self.update_memory(session_id, {'preferences': preferences})
    
    def add_provided_info(self, session_id: str, info: str):
        """记录已提供的信息（避免重复）"""
        memory = self.get_memory(session_id)
        provided_info = memory['provided_info']
        
        if info not in provided_info:
            provided_info.append({
                'info': info,
                'timestamp': datetime.now().isoformat()
            })
            self.update_memory(session_id, {'provided_info': provided_info})
    
    def update_stage(self, session_id: str, new_stage: str):
        """更新客户阶段"""
        self.update_memory(session_id, {'stage': new_stage})
    
    def increment_interaction(self, session_id: str):
        """增加互动次数"""
        memory = self.get_memory(session_id)
        new_count = memory['interaction_count'] + 1
        self.update_memory(session_id, {'interaction_count': new_count})
    
    def build_memory_context(self, session_id: str) -> str:
        """构建记忆上下文（用于AI Prompt）"""
        memory = self.get_memory(session_id)
        
        context_parts = []
        
        # 客户阶段
        stage_desc = {
            CustomerStage.COLD: "初次接触，需要建立信任",
            CustomerStage.WARM: "有一定兴趣，需要深入沟通",
            CustomerStage.HOT: "购买意向强烈，需要促成交易",
            CustomerStage.CUSTOMER: "已成交客户，维护关系",
            CustomerStage.LOST: "曾经流失，需要重新激活"
        }
        context_parts.append(f"客户阶段：{stage_desc.get(memory['stage'], '未知')}")
        
        # 偏好
        if memory['preferences']:
            prefs = []
            if memory['preferences'].get('price_sensitive'):
                prefs.append("对价格敏感")
            if memory['preferences'].get('concerns'):
                prefs.append(f"关注点：{', '.join(memory['preferences']['concerns'])}")
            if memory['preferences'].get('interests'):
                prefs.append(f"感兴趣：{', '.join(memory['preferences']['interests'])}")
            
            if prefs:
                context_parts.append("客户偏好：" + "；".join(prefs))
        
        # 已提供信息
        if memory['provided_info']:
            recent_info = [item['info'] for item in memory['provided_info'][-3:]]
            context_parts.append(f"已提供信息：{', '.join(recent_info)}")
        
        # 互动次数
        if memory['interaction_count'] > 0:
            context_parts.append(f"互动次数：{memory['interaction_count']}次")
        
        return "\n".join(context_parts)

