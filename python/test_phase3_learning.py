
import json
import sqlite3
import requests
import time
from datetime import datetime

# Configuration
BASE_URL = 'http://localhost:5000/api/ai'
DATABASE_PATH = 'ai_expert.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_feedback_loop():
    print("=" * 50)
    print("🧪 Testing Phase 3: Self-Evolution (Feedback Loop)")
    print("=" * 50)

    # 1. Setup: Create a test prompt
    print("\n[Step 1] Creating Test Prompt...")
    prompt_payload = {
        "name": "Learning Test Agent",
        "role_definition": "你是一个学习测试助手",
        "business_logic": "测试反馈闭环",
        "tone_style": "professional"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/prompts", json=prompt_payload)
        resp.raise_for_status()
        prompt_data = resp.json()
        prompt_id = prompt_data['prompt_id']
        print(f"✓ Created Prompt ID: {prompt_id}")
    except Exception as e:
        print(f"❌ Failed to create prompt: {e}")
        return

    # Activate it
    requests.post(f"{BASE_URL}/prompts/{prompt_id}/activate")

    # 2. Simulate User Feedback (The "Learning" Step)
    print("\n[Step 2] Simulating User Feedback (Learning)...")
    
    test_session = f"test_user_{int(time.time())}"
    test_query = "这产品多少钱?"
    original_reply = "价格是100元。"
    final_reply = "亲，现在活动价99元，还送小礼品哦！" # Creating a 'Golden Reply'
    
    feedback_payload = {
        "session_id": test_session,
        "prompt_id": prompt_id,
        "user_query": test_query,
        "original_reply": original_reply,
        "final_reply": final_reply,
        "action": "MODIFIED"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
        resp.raise_for_status()
        print("✓ Feedback accepted by API")
    except Exception as e:
        print(f"❌ Feedback submission failed: {e}")
        return

    # 3. Verify Database (Did it learn?)
    print("\n[Step 3] Verifying Database State...")
    conn = get_db_connection()
    
    # Check Feedback Table
    feedback_row = conn.execute("SELECT * FROM reply_feedback WHERE session_id = ? ORDER BY id DESC LIMIT 1", (test_session,)).fetchone()
    if feedback_row:
        print(f"✓ Found Feedback Record: Action={feedback_row['action']}")
    else:
        print("❌ Feedback record NOT found!")
        
    # Check Golden Replies Table
    golden_row = conn.execute("SELECT * FROM golden_replies WHERE prompt_id = ? AND question = ?", (prompt_id, test_query)).fetchone()
    if golden_row:
        print(f"✓ Found Golden Reply: '{golden_row['reply']}'")
        print(f"  Usage Count: {golden_row['usage_count']}")
    else:
        print("❌ Golden Reply NOT found!")
    
    conn.close()

    # 4. Simulate Generation (Did it use the knowledge?)
    # Since we can't easily see the internal prompt trace via API without debug mode,
    # we will rely on the server logs printing "[Learning] Injected..."
    # But we can try to see if the response mimics it (hard to guarantee with LLM).
    # We will just trigger the generation to ensure no crash.
    
    print("\n[Step 4] Triggering Generation (Check Server Logs for '[Learning]' msg)...")
    generate_payload = {
        "session_id": test_session,
        "prompt_id": prompt_id,
        "customer_message": "这东西怎么卖?", # Similar question
        "conversation_history": []
    }
    
    try:
        # Note: This requires DeepSeek Key. If not configured, it might fail or mock.
        # Assuming dev environment might have key or fail gracefully.
        print("  Sending generation request...")
        resp = requests.post(f"{BASE_URL}/generate", json=generate_payload)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('success'):
                print("✓ Generation successful")
                print(f"  Aggressive: {result['suggestions']['aggressive'][:50]}...")
            else:
                 print(f"⚠️ Generation returned error (expected if no API key): {result.get('error')}")
        else:
            print(f"⚠️ API Error: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"⚠️ Request failed: {e}")

    # Cleanup
    print("\n[Cleanup] Deleting Test Prompt...")
    requests.delete(f"{BASE_URL}/prompts/{prompt_id}")
    print("✓ Cleanup done.")

if __name__ == "__main__":
    test_feedback_loop()
