# -*- coding: utf-8 -*-
"""
专门用于调试微信消息格式的脚本
帮助理解"我"和"对方"消息的实际格式差异
"""
import sys
import os
import time
import uiautomation as auto
import re

# 添加python目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(current_dir, 'python')
sys.path.insert(0, python_dir)

def find_wechat_window():
    """找到微信窗口"""
    window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信', searchDepth=1)
    
    if window.Exists(0):
        session_list = window.ListControl(Name='会话')
        if session_list.Exists(0):
            return window, session_list
    return None, None

def analyze_message_format():
    """分析微信消息格式"""
    print("🔍 开始分析微信消息格式...")
    print("💡 请在微信中:")
    print("   1. 找到一个以'客户'开头的联系人")
    print("   2. 让对方发送一条消息")
    print("   3. 然后您回复一条消息")
    print("   4. 观察下面的输出格式差异")
    print("⏹️  按 Ctrl+C 停止分析\n")
    
    window, session_list = find_wechat_window()
    if not window or not session_list:
        print("❌ 无法找到微信窗口或会话列表")
        return
    
    last_messages = {}
    
    try:
        while True:
            items = session_list.GetChildren()
            
            for item in items:
                raw_name = item.Name
                if not raw_name:
                    continue
                
                # 只关注包含"客户"的会话
                if '客户' not in raw_name:
                    continue
                
                # 检查是否有变化
                if raw_name != last_messages.get('客户', ''):
                    print(f"\n🔔 检测到消息变化:")
                    print(f"原始格式: '{raw_name}'")
                    
                    # 分析消息结构
                    print("📋 消息结构分析:")
                    
                    # 1. 检查未读数
                    unread_match = re.search(r'(\d+)条未读', raw_name)
                    if unread_match:
                        print(f"   未读数: {unread_match.group(1)}")
                    else:
                        print(f"   未读数: 0")
                    
                    # 2. 清理标签
                    temp_name = re.sub(r'\d+条未读|已置顶|消息免打扰', ' ', raw_name)
                    temp_name = re.sub(r'\s+', ' ', temp_name).strip()
                    print(f"   清理后: '{temp_name}'")
                    
                    # 3. 提取时间
                    time_pattern = r'\s?(\d{1,2}:\d{2}|昨天|星期.|前天|\d{1,2}/\d{1,2}|\d{4}/\d{1,2}/\d{1,2})$'
                    time_match = re.search(time_pattern, temp_name)
                    if time_match:
                        time_tag = time_match.group(0).strip()
                        print(f"   时间标签: '{time_tag}'")
                        clean_body = re.sub(time_pattern, '', temp_name).strip()
                        print(f"   去除时间后: '{clean_body}'")
                    else:
                        print(f"   时间标签: 无")
                        clean_body = temp_name
                    
                    # 4. 分析消息内容
                    parts = clean_body.split(' ', 1)
                    session_name = parts[0] if parts else ''
                    content = parts[1] if len(parts) > 1 else ''
                    
                    print(f"   会话名: '{session_name}'")
                    print(f"   消息内容: '{content}'")
                    
                    # 5. 判断发送者
                    if content.startswith("我: ") or content.startswith("我:"):
                        print(f"   🟢 判断: 这是我发送的消息")
                        print(f"   实际内容: '{content.split(':', 1)[-1].strip()}'")
                    elif content.startswith("你: ") or content.startswith("你:"):
                        print(f"   🔵 判断: 这是对方发送的消息")
                        print(f"   实际内容: '{content.split(':', 1)[-1].strip()}'")
                    elif ": " in content:
                        sender = content.split(': ', 1)[0]
                        actual_content = content.split(': ', 1)[1]
                        if sender == "我":
                            print(f"   🟢 判断: 这是我发送的消息 (发送者: {sender})")
                        else:
                            print(f"   🔵 判断: 这是对方发送的消息 (发送者: {sender})")
                        print(f"   实际内容: '{actual_content}'")
                    else:
                        print(f"   🟡 判断: 无明确发送者标识，可能是对方发送")
                    
                    print("-" * 80)
                    last_messages['客户'] = raw_name
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 分析结束")

if __name__ == "__main__":
    analyze_message_format()
