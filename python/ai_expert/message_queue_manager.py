# -*- coding: utf-8 -*-
"""
Message Queue Manager
消息任务队列管理器 - Phase 5 生产级优化
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from .database import AIExpertDatabase

logger = logging.getLogger(__name__)

class MessageQueueManager:
    """管理消息处理队列，支持持久化、异步生成和重试"""
    
    def __init__(self, db: AIExpertDatabase):
        self.db = db
        
    def enqueue_message(self, session_id: str, customer_name: str, message: str) -> int:
        """进入队列"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO message_queue (session_id, customer_name, raw_message, status)
                VALUES (?, ?, ?, 'PENDING')
            """, (session_id, customer_name, message))
            
            queue_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Enqueued message from {customer_name} (ID: {queue_id})")
            return queue_id
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return -1
        finally:
            conn.close()

    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """获取待处理任务"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM message_queue 
            WHERE status = 'PENDING' 
            ORDER BY created_at ASC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_kanban_tasks(self, limit: int = 50) -> List[Dict]:
        """获取看板任务（包括待处理、处理中、已生成待审阅）"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM message_queue 
            WHERE status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_status(self, queue_id: int, status: str, ai_reply_options: Dict = None, error_msg: str = None):
        """更新任务状态"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        update_fields = ["status = ?", "updated_at = ?"]
        params = [status, datetime.now()]
        
        if ai_reply_options:
            update_fields.append("ai_reply_options = ?")
            params.append(json.dumps(ai_reply_options, ensure_ascii=False))
            
        if error_msg:
            update_fields.append("error_msg = ?")
            params.append(error_msg)
            
        params.append(queue_id)
        
        query = f"UPDATE message_queue SET {', '.join(update_fields)} WHERE id = ?"
        
        try:
            cursor.execute(query, tuple(params))
            conn.commit()
            logger.info(f"[Queue] Updated task {queue_id} to status: {status}")
        except Exception as e:
            logger.error(f"[Queue Error] Failed to update status for {queue_id}: {e}")
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """按 ID 获取特定任务"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM message_queue WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_task_by_session(self, session_id: str) -> Optional[Dict]:
        """获取特定会话的最新任务"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM message_queue 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def cleanup_completed_tasks(self, days: int = 7):
        """清理已完成的旧任务"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            DELETE FROM message_queue 
            WHERE status IN ('COMPLETED', 'SENT') AND created_at < ?
        """, (cutoff,))
        
        conn.commit()
        conn.close()
