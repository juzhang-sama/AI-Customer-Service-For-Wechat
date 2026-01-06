
# -*- coding: utf-8 -*-
import sys
import os
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_expert.deepseek_adapter import DeepSeekAdapter
from ai_expert.smart_context_selector import SmartContextSelector
from ai_expert.database import AIExpertDatabase

def flush_print(msg):
    print(msg)
    sys.stdout.flush()

def get_api_key():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('deepseek_api_key', '')
    return ''

def test_semantic_capabilities():
    flush_print("="*50)
    flush_print("Starting Semantic Capabilities Verification")
    flush_print("="*50)

    api_key = get_api_key()
    if not api_key:
        flush_print("[ERROR] No API Key found")
        return

    adapter = DeepSeekAdapter(api_key)
    flush_print("[1] DeepSeek Adapter initialized.")

    # 1. Similarity
    flush_print("\n[2] Testing Similarity Check...")
    t1 = "这个多少钱？"
    t2 = "怎么卖的？"
    sim = adapter.check_similarity(t1, t2)
    flush_print(f"'{t1}' vs '{t2}' -> Similarity: {sim}")
    
    t3 = "今天天气不错"
    sim_diff = adapter.check_similarity(t1, t3)
    flush_print(f"'{t1}' vs '{t3}' -> Similarity: {sim_diff}")

    # 2. Keyword Extraction
    flush_print("\n[3] Testing Keyword Extraction...")
    msg = "我想了解一下你们在上海地区的实际装修案例，最好是现代风格的。"
    keywords = adapter.extract_search_keywords(msg)
    flush_print(f"Message: {msg}")
    flush_print(f"Extracted: {keywords}")

    # 3. Smart Context
    flush_print("\n[4] Testing Smart Context Selector...")
    selector = SmartContextSelector()
    messages = [
        {"role": "user", "content": "你好"}, 
        {"role": "user", "content": "上海那边的客户反馈怎么样？"}, 
        {"role": "assistant", "content": "挺好的。"},
        {"role": "user", "content": "回到刚才的话题。"},
    ]
    
    selected, meta = selector.select_context(
        messages, 
        customer_message=msg,
        deepseek_adapter=adapter
    )
    flush_print("Selected Messages:")
    for m in selected:
        flush_print(f" - {m['content']}")

    # 4. Database Preset
    flush_print("\n[5] Testing Database Semantic Preset Match...")
    db_path = "test_semantic_v2.db"
    if os.path.exists(db_path):
        try: os.remove(db_path)
        except: pass
        
    db = AIExpertDatabase(db_path)
    # Setup
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS preset_qa")
    cursor.execute("DROP TABLE IF EXISTS ai_prompts")
    db.init_database()
    
    pid = db.create_prompt({"name": "Test Prompt"})
    db.activate_prompt(pid)
    
    db.add_preset_qa(pid, "价格是多少", "SEMANTIC_MATCH_SUCCESS", match_type='semantic')
    flush_print("Added preset: '价格是多少' -> 'SEMANTIC_MATCH_SUCCESS'")
    
    query = "请问怎么收费？"
    answer = db.match_preset_answer(pid, query, deepseek_adapter=adapter)
    flush_print(f"Query: '{query}' -> Answer: '{answer}'")
    
    conn.close()
    
    flush_print("\nVerification Complete.")
    
if __name__ == "__main__":
    test_semantic_capabilities()
