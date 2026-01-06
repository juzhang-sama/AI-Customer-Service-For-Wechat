# -*- coding: utf-8 -*-
"""
DeepSeek API Adapter
DeepSeek 大模型 API 适配器
"""

import requests
import time
import json
from typing import List, Dict, Optional
from .cost_calculator import calculate_deepseek_cost

class DeepSeekAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-chat"
        self.timeout = 30  # 30秒超时
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Dict:
        """
        调用 DeepSeek Chat API
        
        Args:
            messages: 对话消息列表 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 温度参数 (0-1)
            max_tokens: 最大生成token数
            stream: 是否流式输出
        
        Returns:
            {
                "content": "生成的回复",
                "prompt_tokens": 输入token数,
                "completion_tokens": 输出token数,
                "total_tokens": 总token数,
                "cost": 费用（元）,
                "response_time": 响应时间（秒）
            }
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # 极致安全的提取方式
            choices = result.get("choices", [])
            if not choices:
                return {
                    "success": False,
                    "error": f"API 返回结果结构异常 (无 choices): {json.dumps(result, ensure_ascii=False)}"
                }
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content and not result.get("usage"):
                 return {
                    "success": False,
                    "error": f"API 返回空内容或异常结构: {json.dumps(result, ensure_ascii=False)}"
                }

            usage = result.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # 计算费用
            cost = calculate_deepseek_cost(prompt_tokens, completion_tokens)
            
            return {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "response_time": response_time,
                "success": True,
                "error": None
            }
            
        except requests.exceptions.Timeout:
            return {
                "content": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": "请求超时，请稍后重试"
            }
        
        except Exception as e:
            return {
                "content": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        流式调用 DeepSeek API
        
        Yields:
            每次返回一个字符块
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                stream=True,
                timeout=self.timeout
            )
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data_json = json.loads(data_str)
                            if 'choices' in data_json and len(data_json['choices']) > 0:
                                delta = data_json['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            print(f"Stream error: {e}")
            yield ""
    
    def test_connection(self) -> bool:
        """测试 API 连接"""
        try:
            result = self.chat([
                {"role": "user", "content": "你好"}
            ], max_tokens=10)
            
            return result["success"]
        
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    def check_similarity(self, text1: str, text2: str) -> float:
        """
        使用 LLM 判断两句话的语义相似度 (0.0 - 1.0)
        """
        # 简单预处理：如果文本完全相同，直接返回 1.0
        if text1.strip() == text2.strip():
            return 1.0

        sys_prompt = "你是一个语义判断专家。请判断以下两句话的语义相似度，返回0.0到1.0之间的数值。0.0表示完全不相关，1.0表示语义完全相同。请只返回一个数字，不要包含任何其他文字。"
        user_prompt = f"句子1: {text1}\n句子2: {text2}"
        
        try:
            result = self.chat(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 使用低温度以获得稳定输出
                max_tokens=10
            )
            
            if result['success']:
                content = result['content'].strip()
                # 尝试提取数字
                import re
                match = re.search(r"0\.\d+|1\.0|1|0", content)
                if match:
                    return float(match.group())
            
            return 0.0
            
        except Exception as e:
            print(f"[DeepSeek] Similarity check failed: {e}")
            return 0.0

    def extract_search_keywords(self, text: str) -> List[str]:
        """
        从文本中提取核心检索关键词
        """
        sys_prompt = "你是一个搜索专家。请从用户输入的文本中提取2-5个核心检索关键词，用于在历史记录中搜索相关内容。忽略无意义的虚词。结果必须是合法的 JSON 字符串列表，例如：[\"价格\", \"优惠\"]。"
        
        try:
            result = self.chat(
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            if result['success']:
                content = result['content'].strip()
                # 清理可能的 markdown 标记
                content = content.replace("```json", "").replace("```", "").strip()
                try:
                    keywords = json.loads(content)
                    if isinstance(keywords, list):
                        return keywords
                except:
                    pass
            
            # 如果解析失败，回退到简单的分词（这里简单按空格分）
            return [w for w in text.split() if len(w) > 1][:5]
            
        except Exception as e:
            print(f"[DeepSeek] Keyword extraction failed: {e}")
            return []
