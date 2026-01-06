# -*- coding: utf-8 -*-
"""
Conversation Stage Manager
对话阶段管理器 - 改进点4
"""

from typing import Dict, List, Optional
from enum import Enum

class ConversationStage(Enum):
    """对话阶段"""
    GREETING = "greeting"  # 破冰/打招呼
    NEED_DISCOVERY = "need_discovery"  # 需求挖掘
    SOLUTION_PRESENTATION = "solution_presentation"  # 方案推荐
    OBJECTION_HANDLING = "objection_handling"  # 异议处理
    CLOSING = "closing"  # 促成交易
    FOLLOW_UP = "follow_up"  # 后续跟进

class ConversationStageManager:
    """管理对话阶段，提供下一步建议"""
    
    def __init__(self, deepseek_adapter=None):
        self.deepseek = deepseek_adapter
        # 阶段转换规则
        self.stage_transitions = {
            ConversationStage.GREETING: [
                ConversationStage.NEED_DISCOVERY
            ],
            ConversationStage.NEED_DISCOVERY: [
                ConversationStage.SOLUTION_PRESENTATION,
                ConversationStage.OBJECTION_HANDLING
            ],
            ConversationStage.SOLUTION_PRESENTATION: [
                ConversationStage.OBJECTION_HANDLING,
                ConversationStage.CLOSING
            ],
            ConversationStage.OBJECTION_HANDLING: [
                ConversationStage.SOLUTION_PRESENTATION,
                ConversationStage.CLOSING,
                ConversationStage.FOLLOW_UP
            ],
            ConversationStage.CLOSING: [
                ConversationStage.FOLLOW_UP
            ],
            ConversationStage.FOLLOW_UP: [
                ConversationStage.NEED_DISCOVERY,
                ConversationStage.CLOSING
            ]
        }
        
        # 阶段关键词
        self.stage_keywords = {
            ConversationStage.GREETING: [
                '你好', '在吗', '您好', '打扰',
                '咨询', '了解', '问一下'
            ],
            ConversationStage.NEED_DISCOVERY: [
                '需要', '想要', '希望', '目标',
                '问题', '困扰', '痛点',
                '什么', '怎么', '如何'
            ],
            ConversationStage.SOLUTION_PRESENTATION: [
                '产品', '方案', '服务', '功能',
                '特点', '优势', '效果',
                '介绍', '详细', '具体'
            ],
            ConversationStage.OBJECTION_HANDLING: [
                '贵', '考虑', '不需要', '不合适',
                '但是', '可是', '不过',
                '担心', '顾虑', '问题'
            ],
            ConversationStage.CLOSING: [
                '购买', '下单', '付款', '支付',
                '怎么买', '什么时候', '多久',
                '优惠', '活动', '赠品'
            ],
            ConversationStage.FOLLOW_UP: [
                '考虑考虑', '再说', '以后',
                '联系', '回复', '通知'
            ]
        }
        
        # 每个阶段的目标和建议
        self.stage_guidance = {
            ConversationStage.GREETING: {
                "goal": "建立初步联系，引导进入需求挖掘",
                "tips": [
                    "友好问候，表明身份",
                    "简短介绍服务内容",
                    "询问客户需求或关注点"
                ],
                "next_actions": [
                    "询问客户具体需求",
                    "了解客户当前痛点",
                    "确认客户购买意向"
                ]
            },
            ConversationStage.NEED_DISCOVERY: {
                "goal": "深入了解客户需求和痛点",
                "tips": [
                    "多提开放式问题",
                    "倾听客户真实需求",
                    "识别关键痛点"
                ],
                "next_actions": [
                    "总结客户需求",
                    "推荐匹配的解决方案",
                    "展示产品价值"
                ]
            },
            ConversationStage.SOLUTION_PRESENTATION: {
                "goal": "展示产品价值，匹配客户需求",
                "tips": [
                    "针对性介绍产品特点",
                    "强调与客户需求的匹配度",
                    "提供案例或证明"
                ],
                "next_actions": [
                    "询问客户是否有疑问",
                    "处理客户异议",
                    "引导成交"
                ]
            },
            ConversationStage.OBJECTION_HANDLING: {
                "goal": "化解客户顾虑，重建信心",
                "tips": [
                    "认同客户感受",
                    "提供解决方案",
                    "用案例或数据证明"
                ],
                "next_actions": [
                    "确认异议是否解决",
                    "继续介绍产品",
                    "尝试促成交易"
                ]
            },
            ConversationStage.CLOSING: {
                "goal": "促成交易，完成转化",
                "tips": [
                    "营造紧迫感",
                    "强调优惠或赠品",
                    "简化购买流程"
                ],
                "next_actions": [
                    "引导下单",
                    "说明购买流程",
                    "确认订单信息"
                ]
            },
            ConversationStage.FOLLOW_UP: {
                "goal": "保持联系，等待时机",
                "tips": [
                    "尊重客户决定",
                    "提供持续价值",
                    "定期跟进"
                ],
                "next_actions": [
                    "约定下次联系时间",
                    "发送相关资料",
                    "保持适度联系"
                ]
            }
        }
    
    def detect_stage(self, messages: List[Dict], current_intent: str = None) -> ConversationStage:
        """
        检测当前对话阶段
        
        Args:
            messages: 对话历史
            current_intent: 当前客户意图（可选）
        
        Returns:
            ConversationStage
        """
        if not messages:
            return ConversationStage.GREETING
        
        # 分析最近几条消息
        recent_messages = messages[-5:]
        
        # 计算每个阶段的匹配分数
        stage_scores = {}
        for stage, keywords in self.stage_keywords.items():
            score = 0
            for msg in recent_messages:
                content = msg.get('content', '').lower()
                for keyword in keywords:
                    if keyword in content:
                        score += 1
            
            if score > 0:
                stage_scores[stage] = score
        
        # 如果没有匹配，根据消息数量判断
        if not stage_scores:
            if len(messages) <= 2:
                return ConversationStage.GREETING
            elif len(messages) <= 5:
                return ConversationStage.NEED_DISCOVERY
            else:
                return ConversationStage.SOLUTION_PRESENTATION
        
        # 返回得分最高的阶段
        return max(stage_scores, key=stage_scores.get)
    
    def get_guidance(self, stage: ConversationStage) -> Dict:
        """获取当前阶段的指导建议"""
        return self.stage_guidance.get(stage, {})
    
    def get_next_actions(self, stage: ConversationStage) -> List[str]:
        """获取下一步建议行动"""
        guidance = self.get_guidance(stage)
        return guidance.get('next_actions', [])

