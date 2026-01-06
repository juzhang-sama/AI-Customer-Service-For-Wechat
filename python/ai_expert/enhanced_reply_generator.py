# -*- coding: utf-8 -*-
"""
Enhanced Reply Generator
增强版回复生成器
整合所有5个改进点
"""

import time
from typing import Dict, List, Optional
import concurrent.futures
from .database import AIExpertDatabase
from .deepseek_adapter import DeepSeekAdapter
from .cost_calculator import calculate_deepseek_cost
from .enhanced_prompt_builder import EnhancedPromptBuilder
from .smart_context_selector import SmartContextSelector
from .intent_recognizer import IntentRecognizer, CustomerIntent
from .customer_memory import CustomerMemory
from .conversation_stage_manager import ConversationStageManager
from .feedback_learner import FeedbackLearner

class EnhancedReplyGenerator:
    """增强版回复生成器"""
    
    def __init__(self, api_key: str, db_instance, kb_manager=None):
        self.db = db_instance
        self.api_key = api_key
        self.deepseek = DeepSeekAdapter(api_key)
        self.context_selector = SmartContextSelector()
        self.intent_recognizer = IntentRecognizer(self.deepseek)
        self.customer_memory = CustomerMemory(self.db)
        self.prompt_builder = EnhancedPromptBuilder()
        self.stage_manager = ConversationStageManager(self.deepseek)
        self.kb_manager = kb_manager
        self.feedback_learner = FeedbackLearner(db_instance)
    
    def generate_three_versions(
        self,
        session_id: str,
        customer_message: str,
        system_prompt_config: Dict,
        prompt_id: int,
        conversation_history: List[Dict] = None
    ) -> Dict:
        """
        生成三个版本的回复（整合所有改进）
        
        Args:
            session_id: 会话ID
            customer_message: 客户消息
            system_prompt_config: System Prompt配置
            prompt_id: Prompt配置ID
            conversation_history: 会话历史
        
        Returns:
            {
                "success": bool,
                "aggressive": str,
                "conservative": str,
                "professional": str,
                "suggestion_id": int,
                "metadata": {
                    "intent": str,
                    "objection_type": str,
                    "conversation_stage": str,
                    "customer_stage": str,
                    "context_info": dict
                },
                "tokens_used": int,
                "cost": float,
                "response_time": float
            }
        """
        start_time = time.time()
        
        try:
            # ========== 改进点1: 智能上下文选择 ==========
            if conversation_history:
                selected_context, context_metadata = self.context_selector.select_context(
                    conversation_history,
                    max_tokens=2000,
                    min_messages=3,
                    customer_message=customer_message,
                    deepseek_adapter=self.deepseek
                )
            else:
                # 从数据库获取
                messages = self.db.get_recent_messages(session_id, limit=20)
                formatted_messages = [
                    {
                        "role": "user" if msg['is_customer'] else "assistant",
                        "content": msg['message'],
                        "timestamp": msg.get('timestamp')
                    }
                    for msg in messages
                ]
                selected_context, context_metadata = self.context_selector.select_context(
                    formatted_messages,
                    max_tokens=2000,
                    min_messages=3,
                    customer_message=customer_message,
                    deepseek_adapter=self.deepseek
                )
            
            # ========== 改进点2: 客户意图识别 ==========
            intent_result = self.intent_recognizer.recognize_intent(
                customer_message,
                selected_context
            )
            customer_intent = intent_result['intent']
            objection_type = intent_result.get('objection_type')
            
            # ========== 改进点3: 个性化记忆 ==========
            customer_memory = self.customer_memory.get_memory(session_id)
            
            # 更新互动次数
            self.customer_memory.increment_interaction(session_id)
            
            # 更新最后意图
            self.customer_memory.update_memory(session_id, {
                'last_intent': customer_intent.value if customer_intent else None,
                'last_objection_type': objection_type.value if objection_type else None
            })
            
            # ========== 改进点5 (RAG): 检索知识库 ==========
            retrieved_knowledge = []
            if self.kb_manager and customer_message:
                try:
                    # 传入当前 prompt_id 进行过滤
                    results = self.kb_manager.search(
                        query=customer_message, 
                        bound_prompt_id=prompt_id,
                        top_k=3, 
                        threshold=0.4
                    )
                    if results:
                        print(f"[RAG] Hit {len(results)} chunks")
                        for res in results:
                            retrieved_knowledge.append(f"[相关资料: {res['source']}] {res['content']}")
                except Exception as e:
                    print(f"[RAG] Search failed: {e}")

            # 合并检索到的知识到配置中
            if retrieved_knowledge:
                # 确保 knowledge_base 是列表
                current_kb = system_prompt_config.get('knowledge_base', [])
                if not isinstance(current_kb, list):
                    current_kb = []
                
                # 放在最前面，作为高优先级上下文
                system_prompt_config['knowledge_base'] = retrieved_knowledge + current_kb

            # ========== Phase 3: Dynamic Few-Shot Learning ==========
            # 从数据库获取“金牌话术”作为参考示例
            # 如果支持 RAG 语义搜索金牌话术更好，目前先使用“高频使用的金牌话术”
            golden_replies = []
            try:
                # 获取该 Prompt ID 下最热的 5 条金牌话术
                top_golden = self.db.get_golden_replies(prompt_id=prompt_id, limit=5)
                if top_golden:
                    print(f"[Learning] Injected {len(top_golden)} golden replies")
                    golden_formatted = []
                    for g in top_golden:
                        golden_formatted.append(f"Q: {g['question']}\nA: {g['reply']}")
                    
                    # 将金牌话术注入到 prompt_config 中 (需要 prompt_builder 支持，或者放入 knowledge_base)
                    # 放入 knowledge_base 是个简单有效的 hack
                    # 也可以作为一个单独的 section
                    system_prompt_config['few_shot_examples'] = golden_formatted
            except Exception as e:
                print(f"[Learning] Failed to fetch golden replies: {e}")

            # ========== 改进点4: 多轮对话优化 ==========
            conversation_stage = self.stage_manager.detect_stage(
                selected_context,
                customer_intent.value if customer_intent else None
            )
            stage_guidance = self.stage_manager.get_guidance(conversation_stage)
            
            # ========== 构建增强版 System Prompt ==========
            enhanced_system_prompt = self.prompt_builder.build_system_prompt(
                config=system_prompt_config,
                customer_memory=customer_memory,
                conversation_stage=conversation_stage,
                customer_intent=customer_intent,
                objection_type=objection_type,
                stage_guidance=stage_guidance
            )
            
            # 添加当前消息到上下文
            full_context = selected_context + [
                {"role": "user", "content": customer_message}
            ]
            
            # ========== 生成三个版本（并发优化） ==========
            versions = {}
            total_tokens = 0
            
            # 定义单个版本生成函数
            def _generate_version(v_type):
                # 添加版本特定的后缀
                version_prompt = enhanced_system_prompt + self.prompt_builder.build_version_suffix(v_type)
                
                # 构建完整消息
                messages = [
                    {"role": "system", "content": version_prompt}
                ] + full_context
                
                # 调用 DeepSeek API
                api_result = self.deepseek.chat(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=600 # 稍微增加长度限制
                )
                
                if not api_result.get('success'):
                    return v_type, None, 0, api_result.get('error')
                
                return v_type, api_result['content'], api_result.get('total_tokens', 0), None

            # 使用线程池并发执行
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(_generate_version, 'aggressive'),
                    executor.submit(_generate_version, 'conservative'),
                    executor.submit(_generate_version, 'professional')
                ]
                
                for future in concurrent.futures.as_completed(futures):
                    v_type, content, tokens, error = future.result()
                    if error:
                        print(f"[Error] Failed to generate {v_type}: {error}")
                        versions[v_type] = f"生成失败: {error}"
                    else:
                        versions[v_type] = content
                        total_tokens += tokens
            
            # 计算费用 (需要 prompt_tokens 和 completion_tokens，这里简化处理)
            # 假设 total_tokens 中 1/3 是 prompt, 2/3 是 completion
            prompt_tokens = total_tokens // 3
            completion_tokens = total_tokens - prompt_tokens
            cost = calculate_deepseek_cost(prompt_tokens, completion_tokens)
            response_time = time.time() - start_time
            
            # 保存建议到数据库
            suggestion_id = self._save_suggestion(
                session_id=session_id,
                prompt_id=prompt_id,
                customer_message=customer_message,
                versions=versions,
                tokens_used=total_tokens,
                cost=cost
            )
            
            # 返回结果
            return {
                "success": True,
                "aggressive": versions['aggressive'],
                "conservative": versions['conservative'],
                "professional": versions['professional'],
                "suggestion_id": suggestion_id,
                "metadata": {
                    "intent": customer_intent.value if customer_intent else None,
                    "objection_type": objection_type.value if objection_type else None,
                    "conversation_stage": conversation_stage.value if conversation_stage else None,
                    "customer_stage": customer_memory.get('stage'),
                    "context_info": context_metadata
                },
                "tokens_used": total_tokens,
                "cost": cost,
                "response_time": response_time
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "aggressive": "",
                "conservative": "",
                "professional": ""
            }

    def _save_suggestion(
        self,
        session_id: str,
        prompt_id: int,
        customer_message: str,
        versions: Dict,
        tokens_used: int,
        cost: float
    ) -> int:
        """保存生成的建议到数据库"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_suggestions
            (session_id, prompt_id, customer_message, suggestion_aggressive,
             suggestion_conservative, suggestion_professional, tokens_used, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            prompt_id,
            customer_message,
            versions['aggressive'],
            versions['conservative'],
            versions['professional'],
            tokens_used,
            cost
        ))

        suggestion_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return suggestion_id

    def record_version_selection(
        self,
        session_id: str,
        customer_message: str,
        selected_version: str,
        suggestion_id: int = None
    ):
        """
        记录用户选择的版本（改进点5：反馈学习）
        """
        self.feedback_learner.record_version_selection(
            session_id=session_id,
            customer_message=customer_message,
            selected_version=selected_version,
            suggestion_id=suggestion_id
        )

    def record_reply_modification(
        self,
        session_id: str,
        original_reply: str,
        modified_reply: str
    ):
        """
        记录用户对回复的修改（改进点5：反馈学习）
        """
        self.feedback_learner.record_modification(
            session_id=session_id,
            original_reply=original_reply,
            modified_reply=modified_reply
        )

    def get_learning_insights(self) -> Dict:
        """
        获取学习洞察（改进点5：反馈学习）

        Returns:
            {
                "version_preferences": dict,
                "modification_patterns": list,
                "effective_replies": list
            }
        """
        return {
            "version_preferences": self.feedback_learner.get_version_preference(),
            "modification_patterns": self.feedback_learner.get_modification_patterns(limit=10),
            "effective_replies": self.feedback_learner.get_effective_replies(limit=20)
        }


