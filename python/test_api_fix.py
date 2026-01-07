import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/ai"

def test_full_update():
    # 1. 获取第一个 Prompt ID
    res = requests.get(f"{BASE_URL}/prompts")
    prompts = res.json().get('prompts', [])
    if not prompts:
        print("No prompts found to test.")
        return
    
    prompt_id = prompts[0]['id']
    print(f"Testing full-update for prompt ID: {prompt_id}")

    # 2. 构造全量更新包
    test_config = {
        "name": prompts[0]['name'],
        "role_definition": "这是一个测试角色",
        "business_logic": "这是一个测试业务逻辑",
        "tone_style": "friendly",
        "reply_length": "short",
        "emoji_usage": "occasional",
        "knowledge_base": [],
        "forbidden_words": ["测试禁忌词"],
        "keywords": [
            {"keyword": "测试关键词1", "match_type": "contains", "priority": 10}
        ],
        "preset_qa": [
            {"question_pattern": "测试问题1", "answer": "测试回答1", "match_type": "exact", "priority": 1}
        ]
    }

    # 3. 发送更新请求
    update_res = requests.post(
        f"{BASE_URL}/prompts/{prompt_id}/full-update",
        json=test_config
    )
    
    print("Response Status:", update_res.status_code)
    print("Response Body:", update_res.json())

    if update_res.json().get('success'):
        print("SUCCESS: Full update API is working correctly.")
    else:
        print("FAILED: API returned error.")

if __name__ == "__main__":
    test_full_update()
