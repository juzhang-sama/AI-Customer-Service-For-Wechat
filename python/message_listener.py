# -*- coding: utf-8 -*-
import uiautomation as auto
import time
import re
import threading
import queue
import comtypes
import json
import os

class WeChatMessageListener(threading.Thread):
    def __init__(self, callback=None):
        super().__init__()
        self.daemon = True
        self.callback = callback
        self.stop_event = threading.Event()
        self.last_states = {} # {nickname: last_msg_text}
        self.window = None
        self.session_list = None
        self.msg_queue = queue.Queue()
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
        self.config_mtime = 0
        self.monitor_keyword = '客户'
        self.monitor_match_mode = 'contains'  # 默认使用包含匹配
        self._check_config_reload()  # 初始加载

    def _check_config_reload(self):
        """检查配置文件是否更新，若更新则重新加载"""
        try:
            if os.path.exists(self.config_path):
                current_mtime = os.path.getmtime(self.config_path)
                if current_mtime > self.config_mtime:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        new_keyword = config.get('monitor_keyword', '客户')
                        new_match_mode = config.get('monitor_match_mode', 'contains')  # 新增匹配模式
                        if new_keyword != self.monitor_keyword:
                            print(f"[监听器] 关键词已更新: '{self.monitor_keyword}' -> '{new_keyword}'")
                            self.monitor_keyword = new_keyword
                        if not hasattr(self, 'monitor_match_mode') or new_match_mode != self.monitor_match_mode:
                            print(f"[监听器] 匹配模式已更新: '{getattr(self, 'monitor_match_mode', 'startswith')}' -> '{new_match_mode}'")
                            self.monitor_match_mode = new_match_mode
                        self.config_mtime = current_mtime
        except Exception as e:
            print(f"[监听器] 加载配置失败: {e}")
            # 设置默认值
            if not hasattr(self, 'monitor_match_mode'):
                self.monitor_match_mode = 'contains'

    def find_window(self):
        self.window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
        if not self.window.Exists(0):
            self.window = auto.WindowControl(Name='微信', searchDepth=1)
        
        if self.window.Exists(0):
            # Try to cache session list control
            self.session_list = self.window.ListControl(Name='会话')
            return True
        return False

    def parse_session_name(self, name):
        """
        解析微信 NT 版 ListItem 的 Name 字符串。
        """
        if not name: return None, 0, "", False, ""
        
        # 1. 提取并清除未读数，同时规范化空格
        unread_match = re.search(r'(\d+)条未读', name)
        unread_count = int(unread_match.group(1)) if unread_match else 0
        
        # 将已知干扰标签替换为空格，然后合并连续空格并 strip
        temp_name = re.sub(r'\d+条未读', ' ', name)
        temp_name = re.sub(r'已置顶', ' ', temp_name)
        temp_name = re.sub(r'消息免打扰', ' ', temp_name)
        
        # 规范化空格：将所有连续空白字符替换为单个空格
        normalized_name = re.sub(r'\s+', ' ', temp_name).strip()
        
        # 2. 提取时间后缀
        # 支持: 16:02, 昨天, 星期一, 2024/12/30 等常见微信格式
        time_pattern = r'\s?(\d{1,2}:\d{2}|昨天|星期.|前天|\d{1,2}/\d{1,2}|\d{4}/\d{1,2}/\d{1,2})$'
        time_match = re.search(time_pattern, normalized_name)
        time_tag = time_match.group(0).strip() if time_match else ""
        
        # 从主体中移除时间部分
        clean_body = re.sub(time_pattern, '', normalized_name).strip()
        
        # 3. 提取会话名和消息主体
        parts = clean_body.split(' ', 1)
        session_name = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        # 4. 身份判定逻辑 - 基于微信NT版本的实际格式
        # 微信NT版本的消息格式: '联系人名 [未读数] 消息内容 时间'
        # 关键发现：微信NT版本不使用"我:"前缀
        # 判断方法：
        #   - 有未读数 = 对方发送的新消息
        #   - 无未读数 = 我发送的消息（发送后未读数清零）

        is_self = False
        display_sender = session_name

        # 方法1：检查是否有"我:"等前缀（兼容旧版本）
        self_indicators = ["我: ", "我:", "我：", "我 :"]
        for indicator in self_indicators:
            if content.startswith(indicator):
                is_self = True
                display_sender = "我"
                content = content[len(indicator):].strip()
                break

        # 方法2：如果没有明确前缀，使用未读数判断
        # 注意：这个判断在 scan() 方法中会被覆盖，因为需要结合状态变化
        # 这里只做基础判断，实际的 is_self 判断在 scan() 中完成

        if not is_self and ": " in content:
            sub_parts = content.split(': ', 1)
            sender_name = sub_parts[0]
            actual_content = sub_parts[1]
            if sender_name in ["我", "Me", "me"]:
                is_self = True
                display_sender = "我"
                content = actual_content
            else:
                display_sender = sender_name
                content = actual_content

        # 返回时包含 unread_count，让 scan() 方法可以用它来判断
        return session_name, unread_count, content, is_self, display_sender, time_tag

    def scan(self):
        if not self.window or not self.window.Exists(0):
            if not self.find_window():
                return

        if not self.session_list or not self.session_list.Exists(0):
            self.session_list = self.window.ListControl(Name='会话')
            if not self.session_list.Exists(0): return

        try:
            items = self.session_list.GetChildren()
            for item in items:
                raw_name = item.Name
                if not raw_name: continue
                
                # 1. 解析会话项
                parsed = self.parse_session_name(raw_name)
                if not parsed: continue
                nickname, unread, content, is_self, display_sender, time_tag = parsed

                # 添加详细的消息格式调试
                if nickname.startswith('客户') or '客户' in nickname:
                    print(f"[DEBUG] 原始消息: '{raw_name}'")
                    print(f"[DEBUG] 解析结果: 昵称='{nickname}', 内容='{content}', 未读数={unread}, 时间标签='{time_tag}'")

                    # 🔧 使用未读数判断消息发送者
                    if unread > 0:
                        print(f"[DEBUG] ✅ 未读数={unread} > 0，判断为【对方】消息")
                    else:
                        print(f"[DEBUG] ✅ 未读数={unread} == 0，判断为【我的】消息")

                    print("-" * 60)

                # 2. 全局关键词过滤 - 支持多种匹配模式
                if not nickname:
                    continue

                # 检查配置更新
                self._check_config_reload()

                # 根据匹配模式进行过滤
                match_mode = getattr(self, 'monitor_match_mode', 'contains')
                keyword_matched = False

                if match_mode == 'startswith':
                    # 以关键词开头
                    keyword_matched = nickname.startswith(self.monitor_keyword)
                elif match_mode == 'contains':
                    # 包含关键词（推荐）
                    keyword_matched = self.monitor_keyword in nickname
                elif match_mode == 'exact':
                    # 精确匹配
                    keyword_matched = nickname == self.monitor_keyword
                else:
                    # 默认使用包含匹配
                    keyword_matched = self.monitor_keyword in nickname

                # 添加调试日志
                if nickname.startswith('客户') or '客户' in nickname:
                    print(f"[DEBUG] 检查联系人: '{nickname}', 关键词: '{self.monitor_keyword}', 模式: {match_mode}, 匹配: {keyword_matched}")

                if not keyword_matched:
                    # 联系人名称不匹配关键词，跳过
                    continue

                # 3. 构造状态一致性标识
                # 这个标识必须在“红点存在”和“红点消失”时保持绝对一致
                # 我们直接使用清理掉标签后的 normalized_name (即 昵称 + 内容 + 时间)
                # 补充：在 parse_session_name 中合并了所有干扰项
                # 重新计算状态标识以防万一
                state_id = re.sub(r'\d+条未读|已置顶|消息免打扰', ' ', raw_name)
                state_id = re.sub(r'\s+', ' ', state_id).strip()

                # 4. 状态对比与上报
                if nickname not in self.last_states:
                    self.last_states[nickname] = state_id
                    print(f"[DEBUG] 初始化状态: '{nickname}' -> '{state_id}' (不推送初始消息)")
                elif self.last_states[nickname] != state_id:
                    print(f"[DEBUG] 状态变化: '{nickname}' 从 '{self.last_states[nickname]}' 变为 '{state_id}'")

                    # 🔧 关键修复：使用未读数来判断消息发送者
                    # - 有未读数(unread > 0) = 对方发送的新消息
                    # - 无未读数(unread == 0) = 我发送的消息
                    if unread > 0:
                        final_is_self = False
                        final_sender = nickname
                        print(f"[DEBUG] 未读数={unread} > 0，判断为【对方】消息")
                    else:
                        final_is_self = True
                        final_sender = "我"
                        print(f"[DEBUG] 未读数={unread} == 0，判断为【我的】消息")

                    msg_data = {
                        "session": nickname,
                        "sender": final_sender,
                        "content": content,
                        "unread": unread,
                        "is_self": final_is_self,
                        "time": time.strftime("%H:%M:%S")
                    }
                    self.last_states[nickname] = state_id

                    print(f"[DEBUG] 推送消息: {msg_data}")

                    if self.callback:
                        self.callback(msg_data)
                    self.msg_queue.put(msg_data)
        except Exception as e:
            print(f"[Listener Error] {e}")

    def stop(self):
        self.stop_event.set()

    def run(self):
        print("WeChatMessageListener started.")
        comtypes.CoInitialize()
        try:
            while not self.stop_event.is_set():
                self._check_config_reload() # 扫描前检查配置是否更新
                self.scan()
                time.sleep(0.5) # 加快扫描频率，提升 PC 端发送的捕获率
        finally:
            comtypes.CoUninitialize()
        print("WeChatMessageListener stopped.")

if __name__ == "__main__":
    def demo_callback(msg):
        print(f"\n>>> New Message: [{msg['sender']}] {msg['content']} (Time: {msg['time']})")

    listener = WeChatMessageListener(callback=demo_callback)
    listener.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        listener.join()
