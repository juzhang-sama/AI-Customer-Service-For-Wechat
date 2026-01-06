# -*- coding: utf-8 -*-
"""
Enhanced Prompt Builder
增强版 System Prompt 构建器
整合所有改进点，生成更详细、更智能的 System Prompt
"""

import json
from typing import Dict, List, Optional
from .intent_recognizer import CustomerIntent, ObjectionType
from .conversation_stage_manager import ConversationStage

class EnhancedPromptBuilder:
    """构建增强版 System Prompt"""
    
    def build_system_prompt(
        self,
        config: Dict,
        customer_memory: Optional[Dict] = None,
        conversation_stage: Optional[ConversationStage] = None,
        customer_intent: Optional[CustomerIntent] = None,
        objection_type: Optional[ObjectionType] = None,
        stage_guidance: Optional[Dict] = None
    ) -> str:
        """
        构建完整的 System Prompt
        
        Args:
            config: 基础配置（角色定义、业务逻辑等）
            customer_memory: 客户记忆（偏好、已提供信息等）
            conversation_stage: 当前对话阶段
            customer_intent: 客户意图
            objection_type: 异议类型（如果有）
            stage_guidance: 阶段指导建议
        
        Returns:
            完整的 System Prompt
        """
        sections = []
        
        # ========== 第1部分：角色定义 ==========
        sections.append(self._build_role_section(config))
        
        # ========== 第2部分：业务目标 ==========
        sections.append(self._build_business_section(config))
        
        # ========== 第3部分：当前对话情境 ==========
        sections.append(self._build_context_section(
            customer_memory,
            conversation_stage,
            customer_intent,
            objection_type,
            stage_guidance
        ))
        
        # ========== 第4部分：话术规范 ==========
        sections.append(self._build_tone_section(config))
        
        # ========== 第5部分：知识库 ==========
        if config.get('knowledge_base'):
            sections.append(self._build_knowledge_section(config))
        
        # ========== 第6部分：禁忌规则 ==========
        if config.get('forbidden_words'):
            sections.append(self._build_forbidden_section(config))
        
        # ========== 第7部分：策略指导 ==========
        sections.append(self._build_strategy_section(
            conversation_stage,
            customer_intent,
            objection_type,
            stage_guidance
        ))
        
        # ========== 第8部分：Dynamic Few-Shot (Phase 3) ==========
        if config.get('few_shot_examples'):
            sections.append(self._build_few_shot_section(config))

        # ========== 第9部分：输出要求 ==========
        sections.append(self._build_output_section())
        
        return "\n\n".join(filter(None, sections))
    
    def _build_role_section(self, config: Dict) -> str:
        """构建角色定义部分"""
        role = config.get('role_definition', '你是一名专业的销售顾问')
        return f"""# 🎭 角色定义
{role}

你的核心职责：
- 理解客户真实需求
- 提供专业的解决方案
- 建立信任关系
- 促成交易转化"""
    
    def _build_business_section(self, config: Dict) -> str:
        """构建业务目标部分"""
        business = config.get('business_logic', '')
        if not business:
            return ""
        
        return f"""# 🎯 业务目标
{business}"""
    
    def _build_context_section(
        self,
        customer_memory: Optional[Dict],
        conversation_stage: Optional[ConversationStage],
        customer_intent: Optional[CustomerIntent],
        objection_type: Optional[ObjectionType],
        stage_guidance: Optional[Dict]
    ) -> str:
        """构建当前对话情境部分"""
        parts = ["# 📊 当前对话情境"]
        
        # 对话阶段
        if conversation_stage:
            stage_names = {
                ConversationStage.GREETING: "破冰阶段",
                ConversationStage.NEED_DISCOVERY: "需求挖掘阶段",
                ConversationStage.SOLUTION_PRESENTATION: "方案推荐阶段",
                ConversationStage.OBJECTION_HANDLING: "异议处理阶段",
                ConversationStage.CLOSING: "促成交易阶段",
                ConversationStage.FOLLOW_UP: "后续跟进阶段"
            }
            stage_name = stage_names.get(conversation_stage, "未知阶段")
            parts.append(f"**对话阶段**：{stage_name}")
            
            if stage_guidance:
                parts.append(f"**阶段目标**：{stage_guidance.get('goal', '')}")
        
        # 客户意图
        if customer_intent:
            intent_names = {
                CustomerIntent.INQUIRY: "咨询了解",
                CustomerIntent.OBJECTION: "提出异议",
                CustomerIntent.INTEREST: "表示兴趣",
                CustomerIntent.CLOSING: "成交意向",
                CustomerIntent.CHITCHAT: "闲聊",
                CustomerIntent.COMPLAINT: "投诉抱怨"
            }
            intent_name = intent_names.get(customer_intent, "未知")
            parts.append(f"**客户意图**：{intent_name}")
        
        # 异议类型
        if objection_type:
            objection_names = {
                ObjectionType.PRICE: "价格异议",
                ObjectionType.TIME: "时间异议",
                ObjectionType.NEED: "需求异议",
                ObjectionType.TRUST: "信任异议",
                ObjectionType.COMPETITOR: "竞品对比",
                ObjectionType.AUTHORITY: "决策权异议"
            }
            objection_name = objection_names.get(objection_type, "未知")
            parts.append(f"**异议类型**：{objection_name}")
        
        # 客户记忆
        if customer_memory:
            memory_parts = []
            
            stage = customer_memory.get('stage', 'cold')
            stage_desc = {
                'cold': '冷线索（初次接触）',
                'warm': '温线索（有一定兴趣）',
                'hot': '热线索（购买意向强）',
                'customer': '已成交客户',
                'lost': '流失客户'
            }
            memory_parts.append(f"客户阶段：{stage_desc.get(stage, '未知')}")
            
            if customer_memory.get('preferences'):
                prefs = customer_memory['preferences']
                if prefs.get('price_sensitive'):
                    memory_parts.append("⚠️ 对价格敏感")
                if prefs.get('concerns'):
                    memory_parts.append(f"关注点：{', '.join(prefs['concerns'])}")
            
            if customer_memory.get('provided_info'):
                provided_info = customer_memory['provided_info']
                # 如果是列表，直接使用；如果是字典列表，提取 info 字段
                if provided_info and isinstance(provided_info[0], dict):
                    recent_info = [item.get('info', item.get('name', str(item))) for item in provided_info[-3:]]
                else:
                    recent_info = provided_info[-3:]
                if recent_info:
                    memory_parts.append(f"已提供信息：{', '.join(recent_info)}")
            
            if memory_parts:
                parts.append("\n**客户画像**：\n" + "\n".join(f"- {p}" for p in memory_parts))
        
        return "\n".join(parts) if len(parts) > 1 else ""
    
    def _build_tone_section(self, config: Dict) -> str:
        """构建话术规范部分"""
        tone_style = config.get('tone_style', 'professional')
        reply_length = config.get('reply_length', 'medium')
        emoji_usage = config.get('emoji_usage', 'occasional')
        
        tone_desc = {
            'professional': '专业正式',
            'friendly': '亲切友好',
            'casual': '轻松随意'
        }
        
        length_desc = {
            'short': '简短精炼（1-2句话）',
            'medium': '适中详细（3-5句话）',
            'long': '详细完整（5句话以上）'
        }
        
        emoji_desc = {
            'none': '不使用表情符号',
            'occasional': '偶尔使用表情符号',
            'frequent': '频繁使用表情符号'
        }
        
        return f"""# 💬 话术规范
- **语气风格**：{tone_desc.get(tone_style, '专业')}
- **回复长度**：{length_desc.get(reply_length, '适中')}
- **表情使用**：{emoji_desc.get(emoji_usage, '偶尔')}
- **语言要求**：简洁清晰，避免冗长
- **专业度**：展现专业知识，建立信任"""

    def _build_knowledge_section(self, config: Dict) -> str:
        """构建知识库部分"""
        knowledge = config.get('knowledge_base')
        if isinstance(knowledge, str):
            knowledge = json.loads(knowledge)

        if not knowledge:
            return ""

        parts = ["# 📚 产品知识库"]

        for item in knowledge:
            # 兼容两种格式: {name, details} (后端旧版) 或 {topic, points} (前端向导)
            name = item.get('name', item.get('topic', ''))
            details = item.get('details', '')
            
            # 如果是 points 列表，转换为字符串
            points = item.get('points', [])
            if points and isinstance(points, list):
                details = "\n".join(f"- {p}" for p in points)
            
            parts.append(f"\n**{name}**")
            parts.append(details)

        return "\n".join(parts)

    def _build_forbidden_section(self, config: Dict) -> str:
        """构建禁忌规则部分"""
        forbidden = config.get('forbidden_words')
        if isinstance(forbidden, str):
            forbidden = json.loads(forbidden)

        if not forbidden:
            return ""

        parts = ["# ⚠️ 禁忌规则"]
        parts.append("以下词汇和表达方式严禁使用：")

        for item in forbidden:
            # 兼容两种格式: {word, reason} (后端旧版) 或 字符串 (前端列表)
            if isinstance(item, str):
                parts.append(f"- ❌ **{item}**")
            else:
                word = item.get('word', '')
                reason = item.get('reason', '')
                parts.append(f"- ❌ **{word}**：{reason}")

        return "\n".join(parts)

    def _build_strategy_section(
        self,
        conversation_stage: Optional[ConversationStage],
        customer_intent: Optional[CustomerIntent],
        objection_type: Optional[ObjectionType],
        stage_guidance: Optional[Dict]
    ) -> str:
        """构建策略指导部分"""
        parts = ["# 🎯 回复策略"]

        # 根据对话阶段给出策略
        if conversation_stage and stage_guidance:
            tips = stage_guidance.get('tips', [])
            if tips:
                parts.append("\n**当前阶段建议**：")
                for tip in tips:
                    parts.append(f"- {tip}")

            next_actions = stage_guidance.get('next_actions', [])
            if next_actions:
                parts.append("\n**下一步行动**：")
                for action in next_actions:
                    parts.append(f"- {action}")

        # 根据客户意图给出策略
        if customer_intent == CustomerIntent.OBJECTION and objection_type:
            parts.append("\n**异议处理策略**：")

            if objection_type == ObjectionType.PRICE:
                parts.append("- 强调产品价值和性价比")
                parts.append("- 提供分期或优惠方案")
                parts.append("- 对比竞品，突出优势")

            elif objection_type == ObjectionType.TIME:
                parts.append("- 尊重客户节奏，不强推")
                parts.append("- 提供限时优惠，营造紧迫感")
                parts.append("- 约定下次联系时间")

            elif objection_type == ObjectionType.NEED:
                parts.append("- 重新挖掘客户需求")
                parts.append("- 展示产品如何解决痛点")
                parts.append("- 提供案例证明")

            elif objection_type == ObjectionType.TRUST:
                parts.append("- 提供权威证明（资质、案例）")
                parts.append("- 展示客户评价和成功案例")
                parts.append("- 提供试用或保障政策")

            elif objection_type == ObjectionType.COMPETITOR:
                parts.append("- 客观对比，突出差异化优势")
                parts.append("- 避免贬低竞品")
                parts.append("- 强调独特价值")

            elif objection_type == ObjectionType.AUTHORITY:
                parts.append("- 提供详细资料供客户参考")
                parts.append("- 建议客户与决策者沟通")
                parts.append("- 保持联系，等待反馈")

        elif customer_intent == CustomerIntent.CLOSING:
            parts.append("\n**成交策略**：")
            parts.append("- 简化购买流程")
            parts.append("- 强调优惠和赠品")
            parts.append("- 营造紧迫感")
            parts.append("- 引导立即行动")

        elif customer_intent == CustomerIntent.INTEREST:
            parts.append("\n**兴趣培养策略**：")
            parts.append("- 深入介绍产品特点")
            parts.append("- 提供案例和证明")
            parts.append("- 引导体验或试用")

        return "\n".join(parts) if len(parts) > 1 else ""

    def _build_few_shot_section(self, config: Dict) -> str:
        """构建 Dynamic Few-Shot 部分 (Phase 3)"""
        examples = config.get('few_shot_examples', [])
        if not examples:
            return ""

        parts = ["# 💡 参考示例 (Golden Replies)"]
        parts.append("以下是经过验证的高质量回复示例，请学习其语气和表达方式：")
        
        for ex in examples:
            parts.append(f"\n{ex}")
            
        return "\n".join(parts)

    def _build_output_section(self) -> str:
        """构建输出要求部分"""
        return """# 📝 输出要求
- 直接输出回复内容，不要添加"回复："等前缀
- 保持自然对话风格，像真人一样交流
- 根据客户问题灵活调整回复内容
- 如果不确定，可以礼貌地询问更多信息
- 避免重复已提供的信息
- 每次回复都要推进对话，朝着目标前进"""

    def build_version_suffix(self, version_type: str) -> str:
        """
        构建不同版本的 Prompt 后缀

        Args:
            version_type: 'aggressive' | 'conservative' | 'professional'

        Returns:
            版本特定的指令
        """
        suffixes = {
            'aggressive': """

# 🚀 版本要求：进取型
- 积极引导客户做出决策
- 营造紧迫感和稀缺性
- 强调立即行动的好处
- 使用更有说服力的语言
- 适度施加压力，但不要过于强硬""",

            'conservative': """

# 🛡️ 版本要求：保守型
- 稳健推进，不急于求成
- 重点建立信任和了解需求
- 提供充分的信息和选择
- 尊重客户的决策节奏
- 强调长期价值和保障""",

            'professional': """

# 🎓 版本要求：专业型
- 展示专业知识和行业洞察
- 提供详细的产品信息
- 使用数据和案例支撑
- 保持专业、客观的态度
- 充分展示产品价值和优势"""
        }

        return suffixes.get(version_type, '')


