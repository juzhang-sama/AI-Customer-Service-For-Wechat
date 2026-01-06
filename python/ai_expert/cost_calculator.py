# -*- coding: utf-8 -*-
"""
Cost Calculator
API 费用计算器
"""

# DeepSeek 定价 (2025年)
# 参考: https://platform.deepseek.com/api-docs/pricing/
DEEPSEEK_PRICING = {
    "deepseek-chat": {
        "input": 0.001,   # ¥0.001 / 1K tokens
        "output": 0.002,  # ¥0.002 / 1K tokens
    }
}

def calculate_deepseek_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    计算 DeepSeek API 调用费用
    
    Args:
        prompt_tokens: 输入 token 数
        completion_tokens: 输出 token 数
    
    Returns:
        费用（元），保留4位小数
    """
    pricing = DEEPSEEK_PRICING["deepseek-chat"]
    
    input_cost = (prompt_tokens / 1000) * pricing["input"]
    output_cost = (completion_tokens / 1000) * pricing["output"]
    
    total_cost = input_cost + output_cost
    
    return round(total_cost, 4)

def format_cost(cost: float) -> str:
    """
    格式化费用显示
    
    Args:
        cost: 费用（元）
    
    Returns:
        格式化的字符串，如 "¥0.0012"
    """
    return f"¥{cost:.4f}"

def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    中文: 约 1.5 字符 = 1 token
    英文: 约 4 字符 = 1 token
    
    Args:
        text: 文本内容
    
    Returns:
        估算的 token 数
    """
    # 简单估算：中文字符多，按1.5字符=1token
    # 英文字符多，按4字符=1token
    # 这里简化处理，统一按2字符=1token
    return len(text) // 2

def calculate_budget_usage(used_cost: float, budget: float) -> dict:
    """
    计算预算使用情况
    
    Args:
        used_cost: 已使用费用
        budget: 总预算
    
    Returns:
        {
            "used": 已使用费用,
            "remaining": 剩余费用,
            "percentage": 使用百分比,
            "status": "safe" | "warning" | "danger"
        }
    """
    remaining = budget - used_cost
    percentage = (used_cost / budget * 100) if budget > 0 else 0
    
    # 判断状态
    if percentage < 80:
        status = "safe"
    elif percentage < 100:
        status = "warning"
    else:
        status = "danger"
    
    return {
        "used": round(used_cost, 4),
        "remaining": round(remaining, 4),
        "percentage": round(percentage, 2),
        "status": status
    }

