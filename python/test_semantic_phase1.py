
# -*- coding: utf-8 -*-
import sys
import os
import time
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_expert.deepseek_adapter import DeepSeekAdapter
from ai_expert.smart_context_selector import SmartContextSelector
from ai_expert.database import AIExpertDatabase

def get_api_key():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('deepseek_api_key', '')
    return ''

def test_semantic_capabilities():
    print("="*50)
    print("Starting Semantic Capabilities Verification")
    print("="*50)

    api_key = get_api_key()
    if not api_key:
        print("[ERROR] No API Key found in config/ai_config.json")
        return

    adapter = DeepSeekAdapter(api_key)
    print("[1] DeepSeek Adapter initialized.")

    # 1. Test Similarity
    print("\n[2] Testing Similarity Check...")
    t1 = "这个多少钱？"
    t2 = "怎么卖的？"
    sim = adapter.check_similarity(t1, t2)
    print(f"'{t1}' vs '{t2}' -> Similarity: {sim}")
    if sim > 0.8:
        print("✅ Similarity check PASSED")
    else:
        print("❌ Similarity check FAILED")

    t3 = "今天天气不错"
    sim_diff = adapter.check_similarity(t1, t3)
    print(f"'{t1}' vs '{t3}' -> Similarity: {sim_diff}")
    if sim_diff < 0.3:
        print("✅ Dissimilarity check PASSED")
    else:
        print("❌ Dissimilarity check FAILED")

    # 2. Test Keyword Extraction
    print("\n[3] Testing Keyword Extraction...")
    msg = "我想了解一下你们在上海地区的实际装修案例，最好是现代风格的。"
    keywords = adapter.extract_search_keywords(msg)
    print(f"Message: {msg}")
    print(f"Extracted: {keywords}")
    if "上海" in keywords and "案例" in keywords:
         print("✅ Keyword extraction PASSED")
    else:
         print("❌ Keyword extraction FAILED (Might be valid variance, check output)")

    # 3. Test Smart Context Selector
    print("\n[4] Testing Smart Context Selector...")
    selector = SmartContextSelector()
    messages = [
        {"role": "user", "content": "你好"}, # Noise
        {"role": "user", "content": "上海那边的客户反馈怎么样？"}, # Relevant if keyword is 上海
        {"role": "assistant", "content": "挺好的。"},
        {"role": "user", "content": "北京的呢？"},
        {"role": "user", "content": "回到刚才的话题。"},
    ]
    # We expect '上海' to pull the second message up if we search for it.
    
    # Mocking extraction result to ensure test stability or use real adapter
    # Let's use real adapter
    selected, meta = selector.select_context(
        messages, 
        customer_message=msg, # Using the message from step 2
        deepseek_adapter=adapter
    )
    print("Selected Messages:")
    for m in selected:
        print(f" - {m['content']}")
    
    # Check if "上海那边的..." is included
    has_shanghai = any("上海" in m['content'] for m in selected)
    if has_shanghai:
        print("✅ Semantic Context Selection PASSED")
    else:
        print("❌ Semantic Context Selection FAILED")

    # 4. Test Database Semantic Preset Match
    print("\n[5] Testing Database Semantic Preset Match...")
    db = AIExpertDatabase("test_semantic.db") # Use a test db
    # Setup test data
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS preset_qa")
    cursor.execute("DROP TABLE IF EXISTS ai_prompts")
    db.init_database()
    
    # Create a prompt
    pid = db.create_prompt({"name": "Test Prompt"})
    db.activate_prompt(pid)
    
    # Create a preset QA
    db.add_preset_qa(pid, "价格是多少", "我们要100块", match_type='semantic')
    
    print("Added preset: '价格是多少' -> '我们要100块'")
    
    # Matched query
    query = "请问怎么收费？"
    answer = db.match_preset_answer(pid, query, deepseek_adapter=adapter)
    print(f"Query: '{query}' -> Answer: '{answer}'")
    
    if answer == "我们要100块":
        print("✅ Semantic Preset Match PASSED")
    else:
        print("❌ Semantic Preset Match FAILED")

    # Cleanup
    try:
        if os.path.exists("test_semantic.db"):
            # Try to close any open connections if possible (not exposed easily)
            # Just wait a bit
            time.sleep(1)
            os.remove("test_semantic.db")
    except Exception as e:
        print(f"[WARN] Could not delete test db: {e}")
        
    print("\nVerification Complete.")
    sys.stdout.flush()

if __name__ == "__main__":
    test_semantic_capabilities()
