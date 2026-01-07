# -*- coding: utf-8 -*-
"""
Analytics Manager
数据统计引擎 - Phase 8
负责从数据库聚合消息、AI 采纳率、Token 消耗等数据
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from collections import Counter
import re

logger = logging.getLogger(__name__)

class AnalyticsManager:
    def __init__(self, db):
        self.db = db

    def get_overview_stats(self) -> Dict[str, Any]:
        """获取全盘概览数据"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 消息统计
            cursor.execute("SELECT COUNT(*) FROM message_queue")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM message_queue WHERE status = 'SENT'")
            sent_messages = cursor.fetchone()[0]
            
            # 2. Token & 成本统计
            cursor.execute("SELECT SUM(tokens_used), SUM(cost) FROM ai_suggestions")
            row = cursor.fetchone()
            total_tokens = row[0] or 0
            total_cost = row[1] or 0.0
            
            # 3. 专家配置数
            cursor.execute("SELECT COUNT(*) FROM ai_prompts")
            total_prompts = cursor.fetchone()[0]
            
            return {
                "total_messages": total_messages,
                "sent_messages": sent_messages,
                "reply_rate": round(sent_messages / total_messages * 100, 2) if total_messages > 0 else 0,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 2),
                "total_prompts": total_prompts
            }
        except Exception as e:
            logger.error(f"[Analytics] Overview stats failed: {e}")
            return {}
        finally:
            conn.close()

    def get_daily_trends(self, limit_days: int = 7) -> List[Dict]:
        """获取每日趋势数据"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取最近几天的时间点
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(limit_days - 1, -1, -1)]
            
            trends = []
            for date in dates:
                # 统计当消息任务数 (使用 strftime 格式化比对)
                cursor.execute("""
                    SELECT COUNT(*) FROM message_queue 
                    WHERE strftime('%Y-%m-%d', created_at) = ?
                """, (date,))
                count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM message_queue 
                    WHERE strftime('%Y-%m-%d', updated_at) = ? AND status = 'SENT'
                """, (date,))
                sent_count = cursor.fetchone()[0]
                
                trends.append({
                    "date": date,
                    "total": count,
                    "sent": sent_count
                })
                
            return trends
        except Exception as e:
            logger.error(f"[Analytics] Daily trends failed: {e}")
            return []
        finally:
            conn.close()

    def get_hot_keywords(self, top_n: int = 15) -> List[Dict]:
        """简单词频分析（模拟热点词云）"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT raw_message FROM message_queue ORDER BY created_at DESC LIMIT 200")
            messages = [row[0] for row in cursor.fetchall() if row[0]]
            
            # 合并所有文本并清洗（简单正则）
            all_text = " ".join(messages)
            # 过滤掉常见停用词（初级版）
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            
            # 提取 2-4 字的中文字符
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', all_text)
            filtered_words = [w for w in words if w not in stop_words]
            
            counter = Counter(filtered_words)
            return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]
        except Exception as e:
            logger.error(f"[Analytics] Hot keywords failed: {e}")
            return []
        finally:
            conn.close()

    def get_ai_efficiency(self) -> Dict[str, Any]:
        """AI 采纳率与效率统计"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM ai_suggestions WHERE selected_type IS NOT NULL")
            total_adopted = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_suggestions")
            total_requests = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_suggestions WHERE edited_content IS NOT NULL AND edited_content != ''")
            edited_count = cursor.fetchone()[0]
            
            return {
                "adoption_rate": round(total_adopted / (total_requests + 0.001) * 100, 2),
                "edit_rate": round(edited_count / (total_adopted + 0.001) * 100, 2)
            }
        except Exception as e:
            logger.error(f"[Analytics] AI efficiency failed: {e}")
            return {}
        finally:
            conn.close()

    def get_ai_insights(self, generator_fn) -> str:
        """调用 AI 生成经营洞察快报"""
        try:
            # 1. 搜集素材：最近 50 条消息概要
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT customer_name, raw_message FROM message_queue ORDER BY created_at DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "暂无充足数据生成经营快报。"
                
            material = "\n".join([f"- {row[0]}: {row[1]}" for row in rows])
            
            # 2. 构造 Prompt
            prompt = f"""
            你是一位资深的商业分析专家。请根据以下最近的客户咨询消息记录，生成一份简短的【经营洞察快报】。
            要求：
            1. 概括核心客户诉求（2-3点）。
            2. 发现潜在的业务机会或风险。
            3. 提供一条具体的话术或策略落地建议。
            4. 语言专业、精炼。
            
            客户消息：
            {material}
            """
            
            # 3. 调用 AI (假设 generator_fn 是一个能处理 chat 的函数)
            insight = generator_fn(prompt)
            return insight
        except Exception as e:
            logger.error(f"[Analytics] AI insights generation failed: {e}")
            return "经营快报生成暂不可用。"
