
import requests
import json
import os

def get_api_key():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('deepseek_api_key', '')
    return ''

def test_embedding():
    api_key = get_api_key()
    if not api_key:
        print("No API Key found")
        return

    # Try common DeepSeek embedding endpoints
    urls = [
        "https://api.deepseek.com/embeddings",
        "https://api.deepseek.com/v1/embeddings"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-embedding", # Try guessing the model name or use a common one
        "input": "Test embedding"
    }

    print(f"Testing with API Key: {api_key[:5]}...")

    for url in urls:
        print(f"Testing URL: {url}")
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            if response.status_code == 200:
                print("SUCCESS!")
                return
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_embedding()
