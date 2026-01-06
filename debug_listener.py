# -*- coding: utf-8 -*-
"""
简化版微信监听器调试工具
用于排查监听器是否正常工作
"""
import sys
import os
import time
import json

# 添加python目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(current_dir, 'python')
sys.path.insert(0, python_dir)

from message_listener import WeChatMessageListener

def debug_callback(msg):
    print(f"\n🔔 监听到新消息:")
    print(f"   会话: {msg['session']}")
    print(f"   发送者: {msg['sender']}")
    print(f"   内容: {msg['content']}")
    print(f"   时间: {msg['time']}")
    print(f"   未读数: {msg['unread']}")
    print(f"   是否自己: {msg['is_self']}")
    print("-" * 50)

def main():
    print("🚀 启动微信监听器调试模式...")
    print("📋 当前配置:")

    # 读取配置
    config_path = os.path.join(current_dir, 'config', 'ai_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            keyword = config.get('monitor_keyword', '客户')
            match_mode = config.get('monitor_match_mode', 'contains')
            print(f"   监听关键词: '{keyword}'")
            print(f"   匹配模式: {match_mode}")
    except Exception as e:
        print(f"   ❌ 配置读取失败: {e}")

    print("\n🔍 开始监听微信消息...")
    print("💡 请确保:")
    print("   1. 微信已打开")
    print("   2. 有以'客户'开头或包含'客户'的联系人")
    print("   3. 该联系人发送了新消息")
    print("⏹️  按 Ctrl+C 停止监听\n")

    # 创建监听器
    listener = WeChatMessageListener(callback=debug_callback)
    listener.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 停止监听器...")
        listener.stop()
        listener.join()
        print("✅ 监听器已停止")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
