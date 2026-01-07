# -*- coding: utf-8 -*-
"""
AI Expert Database Module
管理 AI 专家模块的数据库操作
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class AIExpertDatabase:
    def __init__(self, db_path: str = "ai_expert.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接，增强并发能力"""
        conn = sqlite3.connect(self.db_path, timeout=30.0) # 提高超时容忍度
        conn.row_factory = sqlite3.Row  # 返回字典格式
        # 开启 WAL 模式，支持并发读写，减少 Database Locked 概率
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 行业提示词配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role_definition TEXT,
                business_logic TEXT,
                tone_style TEXT,
                reply_length TEXT,
                emoji_usage TEXT,
                knowledge_base TEXT,
                forbidden_words TEXT,
                system_prompt TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_customer BOOLEAN DEFAULT 1
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session 
            ON conversation_history(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON conversation_history(timestamp)
        """)
        
        # 3. AI建议记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                prompt_id INTEGER,
                customer_message TEXT,
                context TEXT,
                suggestion_aggressive TEXT,
                suggestion_conservative TEXT,
                suggestion_professional TEXT,
                selected_type TEXT,
                edited_content TEXT,
                is_sent BOOLEAN DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
            )
        """)
        
        # 4. 收藏话术表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER,
                question_type TEXT,
                customer_question TEXT,
                reply_text TEXT NOT NULL,
                tags TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
            )
        """)
        
        # 5. API使用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER,
                model_name TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                estimated_cost REAL,
                response_time REAL,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
            )
        """)

        # 6. 关键词匹配规则表（新增）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyword_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                match_type TEXT DEFAULT 'startswith',
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_keyword
            ON keyword_rules(keyword, is_active)
        """)

        # 7. 预设问答表（新增）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preset_qa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                question_pattern TEXT NOT NULL,
                answer TEXT NOT NULL,
                match_type TEXT DEFAULT 'contains',
                priority INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_preset_qa_prompt
            ON preset_qa(prompt_id, is_active)
        """)

        # 8. 文件表 (RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL, -- pdf, docx, txt, image
                file_size INTEGER,
                bound_prompt_id INTEGER, -- 绑定的 Prompt ID，NULL表示全局
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

        # 9. 切片表 (RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        """)

        # 10. 回复反馈表 (Phase 3: Self-Evolution)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reply_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                prompt_id INTEGER,
                user_query TEXT,
                original_reply TEXT,
                final_reply TEXT,
                action TEXT, -- 'ACCEPTED', 'MODIFIED', 'REJECTED'
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 11. 金牌话术表 (Phase 3: Self-Evolution)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS golden_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER,
                question TEXT,
                reply TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 12. 消息任务队列表 (Phase 5: Production Readiness)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                customer_name TEXT,
                raw_message TEXT NOT NULL,
                ai_reply_options TEXT, -- JSON 存储三个版本的回复
                status TEXT DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, SENT, FAILED
                error_msg TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引提高查询效率
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_status 
            ON message_queue(status)
        """)

        conn.commit()
        conn.close()

        # 执行数据库迁移（添加缺失的列）
        self._migrate_database()

        print("[OK] AI Expert database initialized successfully")
    
    def _migrate_database(self):
        """数据库迁移：添加缺失的列"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查 ai_suggestions 表是否有 tokens_used 列
            cursor.execute("PRAGMA table_info(ai_suggestions)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'tokens_used' not in columns:
                print("[INFO] Adding tokens_used column to ai_suggestions table...")
                cursor.execute("""
                    ALTER TABLE ai_suggestions 
                    ADD COLUMN tokens_used INTEGER DEFAULT 0
                """)
                print("[OK] tokens_used column added")
            
            if 'cost' not in columns:
                print("[INFO] Adding cost column to ai_suggestions table...")
                cursor.execute("""
                    ALTER TABLE ai_suggestions 
                    ADD COLUMN cost REAL DEFAULT 0.0
                """)
                print("[OK] cost column added")
            
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"[WARN] Database migration note: {e}")
            # 列可能已存在，忽略错误
            pass
        finally:
            conn.close()
    
    # ========== Prompt 配置管理 ==========
    
    def create_prompt(self, data: Dict) -> int:
        """创建新的提示词配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_prompts (
                name, role_definition, business_logic, tone_style,
                reply_length, emoji_usage, knowledge_base, 
                forbidden_words, system_prompt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['name'],
            data.get('role_definition', ''),
            data.get('business_logic', ''),
            data.get('tone_style', 'professional'),
            data.get('reply_length', 'medium'),
            data.get('emoji_usage', 'occasional'),
            json.dumps(data.get('knowledge_base', []), ensure_ascii=False),
            json.dumps(data.get('forbidden_words', []), ensure_ascii=False),
            data.get('system_prompt', '')
        ))
        
        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prompt_id
    
    def get_active_prompt(self) -> Optional[Dict]:
        """获取当前激活的配置"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ai_prompts WHERE is_active = 1 LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict]:
        """根据 ID 获取配置"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ai_prompts WHERE id = ?
        """, (prompt_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_prompts(self) -> List[Dict]:
        """获取所有配置"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ai_prompts ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_prompt(self, prompt_id: int, data: Dict):
        """更新提示词配置"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_prompts SET
                name = ?,
                role_definition = ?,
                business_logic = ?,
                tone_style = ?,
                reply_length = ?,
                emoji_usage = ?,
                knowledge_base = ?,
                forbidden_words = ?,
                system_prompt = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            data['name'],
            data['role_definition'],
            data['business_logic'],
            data['tone_style'],
            data['reply_length'],
            data['emoji_usage'],
            json.dumps(data['knowledge_base'], ensure_ascii=False),
            json.dumps(data['forbidden_words'], ensure_ascii=False),
            data['system_prompt'],
            datetime.now(),
            prompt_id
        ))

        conn.commit()
        conn.close()

    def full_update_prompt_transactional(self, prompt_id: int, data: Dict):
        """
        [原子性修复] 全量更新事务。
        一次性完成：配置更新 + 旧规则清理 + 新规则插入。
        有效预防 Database Locked 并彻底清除历史冗余。
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            # 1. 更新主配置
            cursor.execute("""
                UPDATE ai_prompts SET
                    name = ?,
                    role_definition = ?,
                    business_logic = ?,
                    tone_style = ?,
                    reply_length = ?,
                    emoji_usage = ?,
                    knowledge_base = ?,
                    forbidden_words = ?,
                    system_prompt = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                data['name'],
                data.get('role_definition', ''),
                data.get('business_logic', ''),
                data.get('tone_style', 'professional'),
                data.get('reply_length', 'medium'),
                data.get('emoji_usage', 'occasional'),
                json.dumps(data.get('knowledge_base', []), ensure_ascii=False),
                json.dumps(data.get('forbidden_words', []), ensure_ascii=False),
                data.get('system_prompt', ''),
                datetime.now(),
                prompt_id
            ))

            # 2. 清理并重写关键词规则
            cursor.execute("DELETE FROM keyword_rules WHERE prompt_id = ?", (prompt_id,))
            keywords = data.get('keywords', [])
            for kw in keywords:
                cursor.execute("""
                    INSERT INTO keyword_rules (prompt_id, keyword, match_type, priority)
                    VALUES (?, ?, ?, ?)
                """, (prompt_id, kw.get('keyword'), kw.get('match_type', 'contains'), kw.get('priority', 0)))

            # 3. 清理并重写预设问答
            cursor.execute("DELETE FROM preset_qa WHERE prompt_id = ?", (prompt_id,))
            preset_qa = data.get('preset_qa', [])
            for qa in preset_qa:
                # 兼容多种格式
                q_pattern = qa.get('question_pattern')
                if not q_pattern and qa.get('question_patterns'):
                    q_pattern = qa['question_patterns'][0]
                
                if q_pattern:
                    cursor.execute("""
                        INSERT INTO preset_qa (prompt_id, question_pattern, answer, match_type, priority)
                        VALUES (?, ?, ?, ?, ?)
                    """, (prompt_id, q_pattern, qa.get('answer'), qa.get('match_type', 'contains'), qa.get('priority', 0)))

            conn.commit()
            print(f"[DB] Full transactional update success for prompt {prompt_id}")
        except Exception as e:
            conn.rollback()
            print(f"[DB ERROR] Transaction failed: {e}")
            raise e
        finally:
            conn.close()

    def activate_prompt(self, prompt_id: int):
        """激活指定配置（同时取消其他配置）"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 先取消所有激活
        cursor.execute("UPDATE ai_prompts SET is_active = 0")

        # 激活指定配置
        cursor.execute("""
            UPDATE ai_prompts SET is_active = 1, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), prompt_id))

        conn.commit()
        conn.close()

    def delete_prompt(self, prompt_id: int):
        """删除配置"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ai_prompts WHERE id = ?", (prompt_id,))

        conn.commit()
        conn.close()

    # ========== 对话历史管理 ==========

    def add_message(self, session_id: str, sender: str, message: str, is_customer: bool = True):
        """添加对话消息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO conversation_history (session_id, sender, message, is_customer)
            VALUES (?, ?, ?, ?)
        """, (session_id, sender, message, is_customer))

        conn.commit()
        conn.close()

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Dict]:
        """获取最近的对话消息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))

        rows = cursor.fetchall()
        conn.close()

        # 反转顺序（从旧到新）
        return [dict(row) for row in reversed(rows)]

    def cleanup_old_conversations(self, days: int = 30):
        """清理N天前的对话历史"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            DELETE FROM conversation_history
            WHERE timestamp < ?
        """, (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def delete_message(self, message_id: int):
        """删除单条消息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM conversation_history
            WHERE id = ?
        """, (message_id,))

        conn.commit()
        conn.close()

    def delete_session_messages(self, session_id: str):
        """删除整个会话的所有消息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM conversation_history
            WHERE session_id = ?
        """, (session_id,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    # ========== AI建议管理 ==========

    def save_suggestion(self, data: Dict) -> int:
        """保存AI生成的建议"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_suggestions (
                session_id, prompt_id, customer_message, context,
                suggestion_aggressive, suggestion_conservative, suggestion_professional
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['session_id'],
            data.get('prompt_id'),
            data['customer_message'],
            json.dumps(data.get('context', []), ensure_ascii=False),
            data['suggestion_aggressive'],
            data['suggestion_conservative'],
            data['suggestion_professional']
        ))

        suggestion_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return suggestion_id

    def update_suggestion_feedback(self, suggestion_id: int, selected_type: str,
                                   edited_content: str, is_sent: bool):
        """更新建议的反馈信息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_suggestions
            SET selected_type = ?, edited_content = ?, is_sent = ?
            WHERE id = ?
        """, (selected_type, edited_content, is_sent, suggestion_id))

        conn.commit()
        conn.close()

    # ========== 收藏话术管理 ==========

    def add_favorite(self, data: Dict) -> int:
        """添加收藏话术"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO favorite_replies (
                prompt_id, question_type, customer_question, reply_text, tags
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('prompt_id'),
            data.get('question_type', ''),
            data.get('customer_question', ''),
            data['reply_text'],
            json.dumps(data.get('tags', []), ensure_ascii=False)
        ))

        favorite_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return favorite_id

    def get_favorites(self, prompt_id: Optional[int] = None) -> List[Dict]:
        """获取收藏话术"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if prompt_id:
            cursor.execute("""
                SELECT * FROM favorite_replies
                WHERE prompt_id = ?
                ORDER BY usage_count DESC, created_at DESC
            """, (prompt_id,))
        else:
            cursor.execute("""
                SELECT * FROM favorite_replies
                ORDER BY usage_count DESC, created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def increment_favorite_usage(self, favorite_id: int):
        """增加收藏话术的使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE favorite_replies
            SET usage_count = usage_count + 1
            WHERE id = ?
        """, (favorite_id,))

        conn.commit()
        conn.close()

    def delete_favorite(self, favorite_id: int):
        """删除收藏话术"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM favorite_replies
            WHERE id = ?
        """, (favorite_id,))

        conn.commit()
        conn.close()

    # ========== 关键词规则管理 ==========

    def add_keyword_rule(self, prompt_id: int, keyword: str, match_type: str = 'startswith', priority: int = 0) -> int:
        """添加关键词匹配规则"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO keyword_rules (prompt_id, keyword, match_type, priority)
            VALUES (?, ?, ?, ?)
        """, (prompt_id, keyword, match_type, priority))

        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return rule_id

    def get_keyword_rules(self, prompt_id: Optional[int] = None) -> List[Dict]:
        """获取关键词规则"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if prompt_id:
            cursor.execute("""
                SELECT kr.*, ap.name as prompt_name
                FROM keyword_rules kr
                LEFT JOIN ai_prompts ap ON kr.prompt_id = ap.id
                WHERE kr.prompt_id = ? AND kr.is_active = 1
                ORDER BY kr.priority DESC, kr.created_at DESC
            """, (prompt_id,))
        else:
            cursor.execute("""
                SELECT kr.*, ap.name as prompt_name
                FROM keyword_rules kr
                LEFT JOIN ai_prompts ap ON kr.prompt_id = ap.id
                WHERE kr.is_active = 1
                ORDER BY kr.priority DESC, kr.created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_keyword_rule(self, rule_id: int):
        """删除关键词规则"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM keyword_rules WHERE id = ?
        """, (rule_id,))

        conn.commit()
        conn.close()

    def match_keyword_to_prompt(self, session_name: str) -> Optional[int]:
        """根据会话名匹配对应的 Prompt ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 获取所有激活的关键词规则，按优先级排序
        cursor.execute("""
            SELECT kr.*, ap.is_active as prompt_active
            FROM keyword_rules kr
            LEFT JOIN ai_prompts ap ON kr.prompt_id = ap.id
            WHERE kr.is_active = 1 AND ap.is_active = 1
            ORDER BY kr.priority DESC, kr.created_at DESC
        """)

        rules = cursor.fetchall()
        conn.close()

        print(f"[DEBUG] Matching session '{session_name}' against {len(rules)} rules")

        # 按优先级匹配
        for rule in rules:
            keyword = rule['keyword']
            match_type = rule['match_type']
            print(f"[DEBUG] Testing rule: keyword='{keyword}', type={match_type}, priority={rule['priority']}")

            if match_type == 'startswith' and session_name.startswith(keyword):
                print(f"[DEBUG] ✓ Matched! Using prompt_id={rule['prompt_id']}")
                return rule['prompt_id']
            elif match_type == 'contains' and keyword in session_name:
                print(f"[DEBUG] ✓ Matched! Using prompt_id={rule['prompt_id']}")
                return rule['prompt_id']
            elif match_type == 'exact' and session_name == keyword:
                print(f"[DEBUG] ✓ Matched! Using prompt_id={rule['prompt_id']}")
                return rule['prompt_id']

        print(f"[DEBUG] No keyword match found for session '{session_name}'")
        return None

    # ========== 预设问答管理 ==========

    def add_preset_qa(self, prompt_id: int, question_pattern: str, answer: str,
                      match_type: str = 'contains', priority: int = 0) -> int:
        """添加预设问答"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO preset_qa (prompt_id, question_pattern, answer, match_type, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (prompt_id, question_pattern, answer, match_type, priority))

        qa_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return qa_id

    def get_preset_qa(self, prompt_id: int) -> List[Dict]:
        """获取预设问答列表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM preset_qa
            WHERE prompt_id = ? AND is_active = 1
            ORDER BY priority DESC, created_at DESC
        """, (prompt_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_preset_qa(self, qa_id: int, question_pattern: str, answer: str):
        """更新预设问答"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE preset_qa
            SET question_pattern = ?, answer = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (question_pattern, answer, qa_id))

        conn.commit()
        conn.close()

    def delete_preset_qa(self, qa_id: int):
        """删除预设问答"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM preset_qa WHERE id = ?
        """, (qa_id,))

        conn.commit()
        conn.close()

    def match_preset_answer(self, prompt_id: int, question: str, deepseek_adapter=None) -> Optional[str]:
        """
        匹配预设答案 (支持关键词匹配和 LLM 语义匹配)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM preset_qa
            WHERE prompt_id = ? AND is_active = 1
            ORDER BY priority DESC, created_at DESC
        """, (prompt_id,))

        qa_list = cursor.fetchall()
        conn.close()

        # 1. 传统规则匹配 (速度快，优先)
        for qa in qa_list:
            pattern = qa['question_pattern']
            match_type = qa['match_type']
            qa_id = qa['id']

            if match_type == 'contains' and pattern in question:
                self.increment_preset_qa_usage(qa_id)
                print(f"[Preset Match] 'contains' matched: {pattern}")
                return qa['answer']
            elif match_type == 'exact' and question == pattern:
                self.increment_preset_qa_usage(qa_id)
                print(f"[Preset Match] 'exact' matched: {pattern}")
                return qa['answer']
            elif match_type == 'startswith' and question.startswith(pattern):
                self.increment_preset_qa_usage(qa_id)
                print(f"[Preset Match] 'startswith' matched: {pattern}")
                return qa['answer']
        
        # 2. 语义匹配 (如果提供了 adapter)
        if deepseek_adapter:
            print("[Preset Match] Trying semantic match...")
            # 简单的初步筛选：如果有 1000 条预设，不能全跑 LLM。
            # 这里先假设数量不多 (<50)，或者可以增加简单的关键词重合度筛选
            
            candidates = []
            for qa in qa_list:
                # 只对那些没明确指定 match_type 或者 允许语义匹配的进行检查
                # 这里假设所有未匹配的都值得一试，或者可以限制 match_type='semantic'
                candidates.append(qa)
            
            # 遍历候选者，调用 LLM 判断
            for qa in candidates:
                pattern = qa['question_pattern']
                # 跳过太不相关的 (可选：比如长度差异巨大)
                
                similarity = deepseek_adapter.check_similarity(question, pattern)
                print(f"[Preset Match] Semantic check: '{question}' vs '{pattern}' -> {similarity}")
                
                if similarity >= 0.85: # 阈值可调
                    self.increment_preset_qa_usage(qa['id'])
                    return qa['answer']

        return None

    def increment_preset_qa_usage(self, qa_id: int):
        """增加预设问答使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE preset_qa
            SET usage_count = usage_count + 1
            WHERE id = ?
        """, (qa_id,))

        conn.commit()
        conn.close()

    # ========== Phase 3: Self-Evolution ==========

    def add_reply_feedback(self, session_id: str, prompt_id: int, user_query: str, 
                          original_reply: str, final_reply: str, action: str):
        """记录回复反馈"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reply_feedback (session_id, prompt_id, user_query, original_reply, final_reply, action)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, prompt_id, user_query, original_reply, final_reply, action))
        
        conn.commit()
        conn.close()

    def add_golden_reply(self, prompt_id: int, question: str, reply: str):
        """添加金牌话术 (如果已存在相同的问题+回答，则增加引用计数)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 简单查重
        cursor.execute("""
            SELECT id FROM golden_replies 
            WHERE prompt_id = ? AND question = ? AND reply = ?
        """, (prompt_id, question, reply))
        
        row = cursor.fetchone()
        if row:
            # 已存在，增加计数
            cursor.execute("UPDATE golden_replies SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
        else:
            # 新增
            cursor.execute("""
                INSERT INTO golden_replies (prompt_id, question, reply, usage_count, last_used)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """, (prompt_id, question, reply))
            
        conn.commit()
        conn.close()

    def get_golden_replies(self, prompt_id: int, limit: int = 50) -> List[Dict]:
        """获取金牌话术列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM golden_replies 
            WHERE prompt_id = ? 
            ORDER BY usage_count DESC, created_at DESC
            LIMIT ?
        """, (prompt_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

        conn.commit()
        conn.close()

    # ========== API使用统计 ==========

    def log_api_usage(self, data: Dict):
        """记录API使用情况"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_usage_stats (
                prompt_id, model_name, prompt_tokens, completion_tokens,
                total_tokens, estimated_cost, response_time, success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('prompt_id'),
            data.get('model_name', 'deepseek-chat'),
            data.get('prompt_tokens', 0),
            data.get('completion_tokens', 0),
            data.get('total_tokens', 0),
            data.get('estimated_cost', 0.0),
            data.get('response_time', 0.0),
            data.get('success', True),
            data.get('error_message', '')
        ))

        conn.commit()
        conn.close()

    def get_usage_stats(self, period: str = 'today') -> Dict:
        """获取使用统计"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 计算时间范围
        now = datetime.now()
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = datetime.min

        cursor.execute("""
            SELECT
                COUNT(*) as requests,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(estimated_cost), 0.0) as total_cost,
                COALESCE(AVG(response_time), 0.0) as avg_response_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests
            FROM api_usage_stats
            WHERE created_at >= ?
        """, (start_date,))

        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['success_rate'] = (result['successful_requests'] / result['requests'] * 100) if result['requests'] > 0 else 0
            return result

        return {
            'requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'avg_response_time': 0.0,
            'successful_requests': 0,
            'success_rate': 0.0
        }

