# -*- coding: utf-8 -*-
"""
Intent Recognizer
客户意图识别器 - 改进点2
"""

import re
from typing import Dict, List, Optional
from enum import Enum

class CustomerIntent(Enum):
    """客户意图类型"""
    INQUIRY = "inquiry"  # 咨询
    OBJECTION = "objection"  # 异议
    INTEREST = "interest"  # 感兴趣
    CLOSING = "closing"  # 成交意向
    CHITCHAT = "chitchat"  # 闲聊
    COMPLAINT = "complaint"  # 投诉
    UNKNOWN = "unknown"  # 未知

class ObjectionType(Enum):
    """异议类型"""
    PRICE = "price"  # 价格异议
    TIME = "time"  # 时间异议
    NEED = "need"  # 需求异议
    TRUST = "trust"  # 信任异议
    COMPETITOR = "competitor"  # 竞品对比
    AUTHORITY = "authority"  # 决策权异议

class IntentRecognizer:
    """识别客户意图和异议类型"""
    
    def __init__(self, deepseek_adapter=None):
        self.deepseek = deepseek_adapter
        # 意图关键词映射
        self.intent_keywords = {
            CustomerIntent.INQUIRY: [
                '什么', '怎么', '如何', '哪个', '哪里', '多少',
                '能不能', '可以吗', '有没有', '是不是',
                '了解', '咨询', '问一下', '请问',
                '?', '？'
            ],
            CustomerIntent.OBJECTION: [
                '太贵', '贵了', '便宜点', '降价', '打折',
                '考虑考虑', '再说吧', '不着急', '以后再说',
                '不需要', '不合适', '不感兴趣', '算了',
                '骗人', '假的', '不信', '不靠谱',
                '别家', '其他家', '竞争对手', '对比',
                '要问问', '商量商量', '决定不了'
            ],
            CustomerIntent.INTEREST: [
                '不错', '挺好', '可以', '感兴趣',
                '详细', '具体', '深入了解',
                '有什么优势', '特点', '亮点',
                '案例', '效果', '成功',
                '试试', '体验', '看看'
            ],
            CustomerIntent.CLOSING: [
                '怎么买', '购买', '下单', '付款', '支付',
                '要了', '就这个', '决定了',
                '什么时候', '多久能', '发货',
                '合同', '协议', '签约',
                '优惠', '活动', '赠品'
            ],
            CustomerIntent.COMPLAINT: [
                '投诉', '退款', '退货', '差评',
                '骗子', '垃圾', '太差',
                '不满意', '失望', '后悔'
            ],
            CustomerIntent.CHITCHAT: [
                '你好', '在吗', '嗯', '哦', '好的',
                '谢谢', '辛苦', '再见',
                '天气', '吃饭', '忙吗'
            ]
        }
        
        # 异议类型关键词
        self.objection_keywords = {
            ObjectionType.PRICE: [
                '贵', '便宜', '价格', '多少钱', '降价', '打折', '优惠',
                '太高', '承受不起', '预算', '性价比'
            ],
            ObjectionType.TIME: [
                '考虑', '再说', '不着急', '以后', '过段时间',
                '等等', '再看看', '暂时不', '目前不'
            ],
            ObjectionType.NEED: [
                '不需要', '不合适', '不感兴趣', '算了',
                '用不上', '没必要', '不想要'
            ],
            ObjectionType.TRUST: [
                '骗人', '假的', '不信', '靠谱吗', '可信吗',
                '真的吗', '保证', '承诺', '证明'
            ],
            ObjectionType.COMPETITOR: [
                '别家', '其他家', '竞争对手', '对比',
                '某某家', '朋友推荐', '看到过'
            ],
            ObjectionType.AUTHORITY: [
                '要问问', '商量商量', '决定不了', '老板',
                '家人', '朋友', '同意', '批准'
            ]
        }
    
    def recognize_intent(self, message: str, context: List[Dict] = None) -> Dict:
        """
        识别客户意图
        
        Args:
            message: 客户消息
            context: 对话上下文（可选，用于更准确的判断）
        
        Returns:
            {
                "intent": CustomerIntent,
                "confidence": float (0-1),
                "objection_type": ObjectionType (如果是异议),
                "keywords_matched": List[str]
            }
        """
        message_lower = message.lower()
        
        # 计算每个意图的匹配分数
        intent_scores = {}
        matched_keywords = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    matched.append(keyword)
            
            if score > 0:
                intent_scores[intent] = score
                matched_keywords[intent] = matched
        
        # 如果没有匹配，返回未知
        if not intent_scores:
            return {
                "intent": CustomerIntent.UNKNOWN,
                "confidence": 0.0,
                "objection_type": None,
                "keywords_matched": []
            }
        
        # 找到得分最高的意图
        top_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[top_intent]
        total_keywords = len(self.intent_keywords[top_intent])
        confidence = min(max_score / 3, 1.0)  # 匹配3个关键词即为高置信度
        
        result = {
            "intent": top_intent,
            "confidence": confidence,
            "objection_type": None,
            "keywords_matched": matched_keywords.get(top_intent, [])
        }
        
        # 如果是异议，进一步识别异议类型
        if top_intent == CustomerIntent.OBJECTION:
            objection_type = self._recognize_objection_type(message_lower)
            result["objection_type"] = objection_type
        
        return result
    
    def _recognize_objection_type(self, message: str) -> Optional[ObjectionType]:
        """识别异议类型"""
        objection_scores = {}
        
        for obj_type, keywords in self.objection_keywords.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                objection_scores[obj_type] = score
        
        if not objection_scores:
            return None
        
        return max(objection_scores, key=objection_scores.get)

