# -*- coding: utf-8 -*-
"""
Reply Generator
AI 回复生成器
"""

import asyncio
import concurrent.futures
from typing import List, Dict, Optional
from .deepseek_adapter import DeepSeekAdapter
from .prompt_builder import PromptBuilder
from .context_manager import ContextManager
from .database import AIExpertDatabase

class ReplyGenerator:
    def __init__(self, api_key: str, db: AIExpertDatabase):
        self.deepseek = DeepSeekAdapter(api_key)
        self.prompt_builder = PromptBuilder()
        self.context_manager = ContextManager(db)
        self.db = db
    
    def generate_three_versions(
        self,
        session_id: str,
        customer_message: str,
        system_prompt: str,
        prompt_id: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        并发生成三个版本的回复

        Args:
            session_id: 会话ID
            customer_message: 客户消息
            system_prompt: System Prompt
            prompt_id: 配置ID
            conversation_history: 可选的会话历史 [{"role": "user/assistant", "content": "..."}]

        Returns:
            {
                "aggressive": "进取型回复",
                "conservative": "保守型回复",
                "professional": "专业型回复",
                "objection_detected": bool,
                "objection_type": str,
                "tokens_used": int,
                "cost": float,
                "response_time": float
            }
        """
        # 构建上下文
        if conversation_history:
            # 使用传入的会话历史
            context = conversation_history
            # 确保最后一条是当前客户消息
            if not context or context[-1]['content'] != customer_message:
                context.append({
                    "role": "user",
                    "content": customer_message
                })
        else:
            # 从数据库获取会话历史
            context = self.context_manager.build_context_for_ai(session_id, customer_message)
        
        # 检测异议
        objection_type = self.context_manager.detect_objection_type(customer_message)
        objection_detected = objection_type != 'none'
        
        # 使用线程池并发生成
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交三个任务
            future_aggressive = executor.submit(
                self._generate_single_version,
                system_prompt,
                context,
                'aggressive'
            )
            
            future_conservative = executor.submit(
                self._generate_single_version,
                system_prompt,
                context,
                'conservative'
            )
            
            future_professional = executor.submit(
                self._generate_single_version,
                system_prompt,
                context,
                'professional'
            )
            
            # 等待所有任务完成
            result_aggressive = future_aggressive.result()
            result_conservative = future_conservative.result()
            result_professional = future_professional.result()
        
        # 汇总统计
        total_tokens = (
            result_aggressive['total_tokens'] +
            result_conservative['total_tokens'] +
            result_professional['total_tokens']
        )
        
        total_cost = (
            result_aggressive['cost'] +
            result_conservative['cost'] +
            result_professional['cost']
        )
        
        max_response_time = max(
            result_aggressive['response_time'],
            result_conservative['response_time'],
            result_professional['response_time']
        )
        
        # 记录 API 使用
        self.db.log_api_usage({
            'prompt_id': prompt_id,
            'model_name': 'deepseek-chat',
            'prompt_tokens': total_tokens // 2,  # 估算
            'completion_tokens': total_tokens // 2,
            'total_tokens': total_tokens,
            'estimated_cost': total_cost,
            'response_time': max_response_time,
            'success': all([
                result_aggressive['success'],
                result_conservative['success'],
                result_professional['success']
            ])
        })
        
        # 保存建议
        suggestion_id = self.db.save_suggestion({
            'session_id': session_id,
            'prompt_id': prompt_id,
            'customer_message': customer_message,
            'context': context,
            'suggestion_aggressive': result_aggressive['content'],
            'suggestion_conservative': result_conservative['content'],
            'suggestion_professional': result_professional['content']
        })
        
        return {
            'suggestion_id': suggestion_id,
            'aggressive': result_aggressive['content'],
            'conservative': result_conservative['content'],
            'professional': result_professional['content'],
            'objection_detected': objection_detected,
            'objection_type': objection_type,
            'tokens_used': total_tokens,
            'cost': total_cost,
            'response_time': max_response_time,
            'success': all([
                result_aggressive['success'],
                result_conservative['success'],
                result_professional['success']
            ])
        }
    
    def _generate_single_version(
        self,
        system_prompt: str,
        context: List[Dict],
        version_type: str
    ) -> Dict:
        """
        生成单个版本的回复
        
        Args:
            system_prompt: System Prompt
            context: 对话上下文
            version_type: 版本类型
        
        Returns:
            DeepSeek API 返回结果
        """
        # 添加版本特定的指令
        version_suffix = self.prompt_builder.build_version_suffix(version_type)
        enhanced_system_prompt = system_prompt + version_suffix
        
        # 构建完整消息
        messages = [
            {"role": "system", "content": enhanced_system_prompt}
        ] + context
        
        # 调用 DeepSeek API
        result = self.deepseek.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return result
    
    def generate_objection_handler(self, objection_type: str, customer_message: str) -> str:
        """
        生成异议处理建议
        
        Args:
            objection_type: 异议类型
            customer_message: 客户消息
        
        Returns:
            异议处理话术
        """
        objection_prompts = {
            'price': """客户提出了价格异议。请给出专业的价格异议处理话术：
1. 认同客户感受
2. 强调产品价值
3. 提供解决方案（分期、优惠等）""",
            
            'time': """客户表示需要时间考虑。请给出时间异议处理话术：
1. 理解客户需要时间
2. 询问具体顾虑
3. 提供限时优惠或紧迫性""",
            
            'need': """客户表示不需要或不合适。请给出需求异议处理话术：
1. 了解客户真实需求
2. 重新定位产品价值
3. 提供替代方案""",
            
            'trust': """客户表示信任疑虑。请给出信任异议处理话术：
1. 提供案例和证明
2. 展示专业度
3. 降低决策风险"""
        }
        
        prompt = objection_prompts.get(objection_type, "")
        if not prompt:
            return ""
        
        messages = [
            {"role": "system", "content": "你是一位专业的销售培训师，擅长处理客户异议。"},
            {"role": "user", "content": f"客户说：{customer_message}\n\n{prompt}"}
        ]
        
        result = self.deepseek.chat(messages, temperature=0.7, max_tokens=300)
        
        return result['content'] if result['success'] else ""

