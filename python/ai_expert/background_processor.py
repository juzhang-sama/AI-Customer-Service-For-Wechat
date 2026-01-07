# -*- coding: utf-8 -*-
"""
Background Processor
后台异步生成流水线 - 自动监测新消息并预生成建议
"""

import threading
import time
import json
import logging
from typing import Optional
from .message_queue_manager import MessageQueueManager
from .enhanced_reply_generator import EnhancedReplyGenerator
from .database import AIExpertDatabase
from .knowledge_base_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

class BackgroundProcessor:
    def __init__(self, db: AIExpertDatabase, queue_manager: MessageQueueManager, generator: EnhancedReplyGenerator):
        self.db = db
        self.queue_manager = queue_manager
        self.generator = generator
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动后台线程"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("[Background] AI reply generator worker started.")

    def stop(self):
        """停止后台线程"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        """主循环：定期轮询待处理任务"""
        while self.running:
            try:
                # 1. 获取默认激活的 AI 专家
                active_prompt = self.db.get_active_prompt()
                if not active_prompt:
                    time.sleep(5) # 没有激活的专家，等会儿再试
                    continue

                # 2. 拉取前 5 条待处理任务
                pending_tasks = self.queue_manager.get_pending_tasks(limit=5)
                if not pending_tasks:
                    time.sleep(2)
                    continue

                logger.info(f"[Background] Processing {len(pending_tasks)} pending tasks...")

                # 3. 逐条生成建议
                for task in pending_tasks:
                    if not self.running: break
                    self._process_single_task(task, active_prompt)

            except Exception as e:
                logger.error(f"[Background Error] Core loop failed: {e}")
                time.sleep(5)

    def _process_single_task(self, task: dict, active_prompt: dict):
        """处理单条消息的生成"""
        task_id = task['id']
        session_id = task['session_id']
        message = task['raw_message']

        try:
            # 更新状态为 PROCESSING
            self.queue_manager.update_status(task_id, 'PROCESSING')

            # 构造配置
            system_prompt_config = {
                'role_definition': active_prompt.get('role_definition', ''),
                'business_logic': active_prompt.get('business_logic', ''),
                'tone_style': active_prompt.get('tone_style', 'professional'),
                'reply_length': active_prompt.get('reply_length', 'medium'),
                'emoji_usage': active_prompt.get('emoji_usage', 'occasional'),
                'knowledge_base': json.loads(active_prompt.get('knowledge_base', '[]')),
                'forbidden_words': json.loads(active_prompt.get('forbidden_words', '[]'))
            }

            # 获取历史记录
            history = self.db.get_recent_messages(session_id, limit=5)

            # 调用生成器
            result = self.generator.generate_three_versions(
                session_id=session_id,
                customer_message=message,
                system_prompt_config=system_prompt_config,
                prompt_id=active_prompt['id'],
                conversation_history=history
            )

            if result['success']:
                # 更新状态为 COMPLETED 并存储建议
                self.queue_manager.update_status(
                    task_id, 
                    'COMPLETED', 
                    ai_reply_options={
                        'aggressive': result['aggressive'],
                        'conservative': result['conservative'],
                        'professional': result['professional']
                    }
                )
                logger.info(f"[Background] Task {task_id} generated successfully.")
            else:
                self.queue_manager.update_status(task_id, 'FAILED', error_msg=result.get('error'))
                logger.error(f"[Background] Task {task_id} failed: {result.get('error')}")

        except Exception as e:
            logger.error(f"[Background Error] Failed to process task {task_id}: {e}")
            self.queue_manager.update_status(task_id, 'FAILED', error_msg=str(e))
