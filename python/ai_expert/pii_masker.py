# -*- coding: utf-8 -*-
"""
PII Masker
敏感信息脱敏工具 - Phase 5 生产级优化
"""

import re
import logging

logger = logging.getLogger(__name__)

class PIIMasker:
    """自动识别并脱敏敏感信息（电话、金额、证件号）"""
    
    def __init__(self):
        # 敏感信息识别正则
        self.patterns = {
            # 1. 手机号 (宽松匹配，识别 11 位数字)
            "phone": r'(?:\+86)?1[3-9]\d{9}',
            # 2. 金额 (识别数字跟单位，如 100元, $500, 399.00)
            "money": r'(?:[¥$]|RMB|元)?\s?\d+(?:\.\d{1,2})?\s?(?:元|块|角|分)?',
            # 3. 身份证号 (18位)
            "id_card": r'\d{17}[\dXx]',
            # 4. 银行卡号 (16-19位)
            "bank_card": r'\d{16,19}',
            # 5. 邮箱
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }

    def mask(self, text: str) -> str:
        """执行全文本脱敏"""
        if not text:
            return text
            
        masked_text = text
        
        # 1. 处理手机号 (中段加星)
        def phone_mask(match):
            phone = match.group(0)
            return phone[:3] + "****" + phone[7:]
        
        masked_text = re.sub(self.patterns["phone"], phone_mask, masked_text)
        
        # 2. 处理身份证/银行卡 (保留前后，中间加星)
        def long_num_mask(match):
            val = match.group(0)
            if len(val) >= 10:
                return val[:4] + "****" + val[-4:]
            return "****"
            
        masked_text = re.sub(self.patterns["id_card"], long_num_mask, masked_text)
        masked_text = re.sub(self.patterns["bank_card"], long_num_mask, masked_text)
        
        # 3. 处理邮箱
        def email_mask(match):
            email = match.group(0)
            parts = email.split('@')
            name = parts[0]
            if len(name) > 2:
                return name[:1] + "***" + name[-1:] + "@" + parts[1]
            return "***@" + parts[1]
            
        masked_text = re.sub(self.patterns["email"], email_mask, masked_text)
        
        # 4. 处理金额 (如果金额过大，可以模糊化，目前选择保留但标记)
        # 这里暂时不强制脱敏金额，因为销售对话中金额是核心业务逻辑，脱敏可能导致 AI 建议错误
        # 如果需要彻底脱敏，可以开启：
        # masked_text = re.sub(self.patterns["money"], "[金额]", masked_text)

        return masked_text

    def mask_chat_history(self, history: list) -> list:
        """对整个对话历史进行脱敏"""
        masked_history = []
        for msg in history:
            new_msg = msg.copy()
            if 'content' in new_msg:
                new_msg['content'] = self.mask(new_msg['content'])
            masked_history.append(new_msg)
        return masked_history
