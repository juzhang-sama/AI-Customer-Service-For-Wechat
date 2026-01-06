# -*- coding: utf-8 -*-
"""
Prompt Builder
System Prompt 生成器
"""

import json
from typing import List, Dict

class PromptBuilder:
    def __init__(self):
        pass
    
    def build_system_prompt(self, config: Dict) -> str:
        """
        根据用户配置生成 System Prompt
        
        Args:
            config: 配置字典，包含:
                - role_definition: 角色定义
                - business_logic: 业务逻辑
                - tone_style: 话术风格
                - reply_length: 回复长度
                - emoji_usage: emoji使用
                - knowledge_base: 知识库
                - forbidden_words: 禁忌词
        
        Returns:
            完整的 System Prompt
        """
        sections = []
        
        # 1. 角色定义
        if config.get('role_definition'):
            sections.append(f"# 角色定义\n{config['role_definition']}")
        
        # 2. 业务目标
        if config.get('business_logic'):
            sections.append(f"# 业务目标\n{config['business_logic']}")
        
        # 3. 话术规范
        tone_rules = self._build_tone_rules(
            config.get('tone_style', 'professional'),
            config.get('reply_length', 'medium'),
            config.get('emoji_usage', 'occasional')
        )
        sections.append(f"# 话术规范\n{tone_rules}")
        
        # 4. 知识库
        knowledge = config.get('knowledge_base')
        if knowledge:
            if isinstance(knowledge, str):
                knowledge = json.loads(knowledge)
            if knowledge:
                kb_text = self._build_knowledge_base(knowledge)
                sections.append(f"# 产品知识库\n{kb_text}")
        
        # 5. 禁忌规则
        forbidden = config.get('forbidden_words')
        if forbidden:
            if isinstance(forbidden, str):
                forbidden = json.loads(forbidden)
            if forbidden:
                forbidden_text = self._build_forbidden_rules(forbidden)
                sections.append(f"# 禁忌规则\n{forbidden_text}")
        
        # 6. 输出格式要求
        output_format = """# 输出格式要求
- 直接输出回复内容，不要添加"回复："等前缀
- 保持自然对话风格
- 根据客户问题灵活调整回复内容
- 如果不确定，可以礼貌地询问更多信息"""
        sections.append(output_format)
        
        # 组合所有部分
        system_prompt = "\n\n".join(sections)
        
        return system_prompt
    
    def _build_tone_rules(self, tone_style: str, reply_length: str, emoji_usage: str) -> str:
        """构建话术规范"""
        rules = []
        
        # 语气风格
        if tone_style == 'professional':
            rules.append("- 使用专业、正式的语气")
        elif tone_style == 'casual':
            rules.append("- 使用轻松、口语化的表达")
        elif tone_style == 'friendly':
            rules.append("- 使用亲切、热情的语气")
        
        # 回复长度
        if reply_length == 'short':
            rules.append("- 回复简洁明了，控制在50字以内")
        elif reply_length == 'medium':
            rules.append("- 回复适中，控制在50-150字")
        elif reply_length == 'long':
            rules.append("- 回复详细充分，可以超过150字")
        
        # Emoji使用
        if emoji_usage == 'none':
            rules.append("- 不使用emoji表情")
        elif emoji_usage == 'occasional':
            rules.append("- 适当使用emoji表情增加亲和力")
        elif emoji_usage == 'frequent':
            rules.append("- 经常使用emoji表情，让对话更生动")
        
        return "\n".join(rules)
    
    def _build_knowledge_base(self, knowledge: List[Dict]) -> str:
        """构建知识库部分"""
        if not knowledge:
            return ""
        
        kb_lines = []
        for item in knowledge:
            if isinstance(item, dict):
                topic = item.get('topic', '')
                points = item.get('points', [])
                if topic and points:
                    kb_lines.append(f"**{topic}**")
                    for point in points:
                        kb_lines.append(f"  - {point}")
            elif isinstance(item, str):
                kb_lines.append(f"- {item}")
        
        return "\n".join(kb_lines)
    
    def _build_forbidden_rules(self, forbidden_words: List[str]) -> str:
        """构建禁忌规则"""
        if not forbidden_words:
            return ""
        
        rules = ["严禁在回复中提及以下内容："]
        for word in forbidden_words:
            rules.append(f"- {word}")
        
        return "\n".join(rules)
    
    def inject_few_shot_examples(self, system_prompt: str, examples: List[Dict]) -> str:
        """
        注入 Few-Shot 示例
        
        Args:
            system_prompt: 原始 System Prompt
            examples: 示例列表 [{"question": "...", "answer": "..."}]
        
        Returns:
            增强后的 System Prompt
        """
        if not examples:
            return system_prompt
        
        few_shot_section = "\n\n# 优质话术示例\n"
        for i, example in enumerate(examples[:5], 1):  # 最多5个示例
            few_shot_section += f"\n示例{i}:\n"
            few_shot_section += f"客户: {example['question']}\n"
            few_shot_section += f"回复: {example['answer']}\n"
        
        return system_prompt + few_shot_section
    
    def build_version_suffix(self, version_type: str) -> str:
        """
        构建不同版本的 Prompt 后缀
        
        Args:
            version_type: 'aggressive' | 'conservative' | 'professional'
        
        Returns:
            版本特定的指令
        """
        suffixes = {
            'aggressive': "\n\n请给出积极促单的回复，引导客户尽快做出决策。",
            'conservative': "\n\n请给出稳健推进的回复，重点建立信任和了解需求。",
            'professional': "\n\n请给出专业详细的回复，充分展示专业度和产品价值。"
        }
        
        return suffixes.get(version_type, '')

