# -*- coding: utf-8 -*-
"""
临时测试版本的监听器 - 强制设置部分消息为"我"发送的
用于验证前端显示逻辑是否正常
"""
import sys
import os
import time
import threading
import queue
import comtypes
import json
import re
import uiautomation as auto

# 添加python目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(current_dir, 'python')
sys.path.insert(0, python_dir)

class TestWeChatMessageListener(threading.Thread):
    def __init__(self, callback=None):
        super().__init__()
        self.daemon = True
        self.callback = callback
        self.stop_event = threading.Event()
        self.last_states = {}
        self.window = None
        self.session_list = None
        self.msg_queue = queue.Queue()
        self.monitor_keyword = '客户'
        self.monitor_match_mode = 'contains'
        self.message_counter = 0  # 用于测试

    def find_window(self):
        self.window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
        if not self.window.Exists(0):
            self.window = auto.WindowControl(Name='微信', searchDepth=1)
        
        if self.window.Exists(0):
            self.session_list = self.window.ListControl(Name='会话')
            return True
        return False

    def parse_session_name(self, name):
        """简化的解析逻辑"""
        if not name: 
            return None, 0, "", False, ""
        
        # 提取未读数
        unread_match = re.search(r'(\d+)条未读', name)
        unread_count = int(unread_match.group(1)) if unread_match else 0
        
        # 清理标签
        temp_name = re.sub(r'\d+条未读|已置顶|消息免打扰', ' ', name)
        temp_name = re.sub(r'\s+', ' ', temp_name).strip()
        
        # 提取时间
        time_pattern = r'\s?(\d{1,2}:\d{2}|昨天|星期.|前天|\d{1,2}/\d{1,2}|\d{4}/\d{1,2}/\d{1,2})$'
        time_match = re.search(time_pattern, temp_name)
        time_tag = time_match.group(0).strip() if time_match else ""
        clean_body = re.sub(time_pattern, '', temp_name).strip()
        
        # 提取会话名和内容
        parts = clean_body.split(' ', 1)
        session_name = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        # 🔧 测试用的强制身份判定
        self.message_counter += 1
        
        # 每隔一条消息设置为"我"发送的（用于测试）
        if self.message_counter % 2 == 0:
            is_self = True
            display_sender = "我"
            print(f"[测试] 强制设置为我的消息: '{content}'")
        else:
            is_self = False
            display_sender = session_name
            print(f"[测试] 设置为对方消息: '{content}'")
        
        return session_name, unread_count, content, is_self, display_sender, time_tag

    def scan(self):
        if not self.window or not self.window.Exists(0):
            if not self.find_window():
                return

        if not self.session_list or not self.session_list.Exists(0):
            self.session_list = self.window.ListControl(Name='会话')
            if not self.session_list.Exists(0): 
                return

        try:
            items = self.session_list.GetChildren()
            for item in items:
                raw_name = item.Name
                if not raw_name: 
                    continue
                
                parsed = self.parse_session_name(raw_name)
                if not parsed: 
                    continue
                nickname, unread, content, is_self, display_sender, time_tag = parsed

                # 关键词过滤
                if not nickname or self.monitor_keyword not in nickname:
                    continue

                # 状态检测
                state_id = re.sub(r'\d+条未读|已置顶|消息免打扰', ' ', raw_name)
                state_id = re.sub(r'\s+', ' ', state_id).strip()

                if nickname not in self.last_states:
                    self.last_states[nickname] = state_id
                else:
                    if self.last_states[nickname] != state_id:
                        msg_data = {
                            "session": nickname,
                            "sender": display_sender,
                            "content": content,
                            "unread": unread,
                            "is_self": is_self,
                            "time": time.strftime("%H:%M:%S")
                        }
                        self.last_states[nickname] = state_id
                        
                        print(f"[测试消息] {msg_data}")
                        
                        if self.callback:
                            self.callback(msg_data)
                        self.msg_queue.put(msg_data)
        except Exception as e:
            print(f"[Listener Error] {e}")

    def stop(self):
        self.stop_event.set()

    def run(self):
        print("🧪 测试版监听器启动...")
        comtypes.CoInitialize()
        try:
            while not self.stop_event.is_set():
                self.scan()
                time.sleep(0.5)
        finally:
            comtypes.CoUninitialize()
        print("🧪 测试版监听器停止")

def test_callback(msg):
    print(f"\n📨 测试消息:")
    print(f"   会话: {msg['session']}")
    print(f"   发送者: {msg['sender']}")
    print(f"   内容: {msg['content']}")
    print(f"   是否自己: {msg['is_self']} {'✅' if msg['is_self'] else '❌'}")
    print("-" * 50)

if __name__ == "__main__":
    print("🧪 启动测试版监听器...")
    print("💡 这个版本会交替设置消息为'我'和'对方'发送")
    print("🎯 用于验证前端显示逻辑是否正常")
    print("⏹️  按 Ctrl+C 停止\n")
    
    listener = TestWeChatMessageListener(callback=test_callback)
    listener.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 停止测试...")
        listener.stop()
        listener.join()
        print("✅ 测试完成")
