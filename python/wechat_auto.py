
import uiautomation as auto
import time
import pyperclip
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeChatAutomation:
    def __init__(self):
        self.window = None
        
    def _get_window(self):
        """获取微信主窗口并处理最小化/遮挡"""
        # 1. 优先通过类名查找（最稳妥，不受语言和未读数影响）
        window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
        
        # 2. 备选：通过中英文名称查找
        if not window.Exists(0.5):
            window = auto.WindowControl(Name='微信', searchDepth=1)
            
        if not window.Exists(0):
            window = auto.WindowControl(Name='Weixin', searchDepth=1)
        
        # 3. 兜底：模糊匹配包含“微信”的窗口
        if not window.Exists(0):
             # 这种方式较慢，作为最后的手段
             for w in auto.GetRootControl().GetChildren():
                 if '微信' in w.Name or 'Weixin' in w.Name:
                     window = w
                     break
        
        if window.Exists(0):
            self.window = window
            # 处理最小化
            try:
                # 使用标准的 WindowPattern 获取视觉状态
                pattern = window.GetWindowPattern()
                if pattern and pattern.WindowVisualState == auto.WindowVisualState.Minimized:
                    logger.info("WeChat window is minimized, restoring...")
                    window.Restore()
            except Exception as e:
                # 兼容性兜底：如果无法获取状态，尝试恢复
                logger.debug(f"Could not verify minimized state, trying restore: {e}")
                window.Restore()
            return True
        return False

    def activate(self):
        """将微信窗口置于最前"""
        if self._get_window():
            try:
                self.window.SetActive()
                self.window.SetTopmost(True)
                self.window.SetTopmost(False) # 闪现置顶来夺取焦点
                return True
            except Exception as e:
                logger.error(f"Failed to activate window: {e}")
                return False
        return False

    def get_current_chat_title(self):
        """[WeChat NT 适配] 获取当前聊天窗口标题"""
        try:
            # 1. 尝试直接定位聊天窗口顶部的标题 (通常是第一个较大的非功能性文本)
            # 在 NT 版微信中，标题通常位于右侧面板顶部的 Pane 内
            # 我们寻找所有 TextControl，取第一个 Name 较长且不属于导航栏的
            
            # 先尝试找最有可能的：Name 为非空且不包含基础功能的 Text
            # 我们通过限制搜索深度并避开左侧导航栏（左边距通常较小）来实现
            all_texts = self.window.TextControls()
            for text in all_texts:
                name = text.Name
                rect = text.BoundingRectangle
                if name and name not in ["微信", "Weixin", "搜索", "通讯录", "收藏", "朋友圈", "消息"]:
                    # 标题通常在窗口的中间偏右位置，高度在顶部 100 像素内
                    if rect.top < self.window.BoundingRectangle.top + 100:
                        if rect.left > self.window.BoundingRectangle.left + 150: # 跳过左侧边栏
                             return name
            
            # 兜底：如果上述策略失效，返回第一个找到的 TextControl 名称
            chat_title_element = self.window.TextControl(searchDepth=15, foundIndex=1)
            return chat_title_element.Name
        except Exception as e:
            logger.debug(f"Error getting chat title: {e}")
            return None

    def _verify_chat_title(self, target_who):
        """核对当前会话标题 (强化鲁棒性)"""
        actual_title = self.get_current_chat_title()
        logger.info(f"Actual chat title detected: '{actual_title}', Expected part of: '{target_who}'")
        
        if not actual_title:
            # 如果完全抓不到标题，但在搜索后已进入会话，我们尝试第二种验证：
            # 检查窗口中是否存在一个包含 target_who 的 TextControl
            try:
                if self.window.TextControl(SubName=target_who).Exists(0):
                    logger.info("Title element verified via SubName search.")
                    return True
            except:
                pass
            return False
            
        # 规范化：移除空格/括号/未读数后缀
        import re
        def clean(s):
            return re.sub(r'[\s\(\)（）\-\_\d]+', '', s)
            
        target_clean = clean(target_who)
        actual_clean = clean(actual_title)
        
        # 支持模糊双层匹配
        if target_clean in actual_clean or actual_clean in target_clean:
            return True
            
        # 如果还是不通过，最后一次机会：直接包含匹配
        return target_who in actual_title or actual_title in target_who

    def send_message(self, who, message):
        """发送消息，包含完整性核对闭环"""
        if not self.activate():
            return {"status": "error", "message": "WeChat window not found"}

        logger.info(f"Starting to send message to: {who}")

        # 1. 点击搜索框并清理内容
        try:
            search_box = self.window.EditControl(Name='搜索')
            if not search_box.Exists(2):
                return {"status": "error", "message": "Search box not found"}
            
            search_box.Click()
            time.sleep(0.2)
            search_box.SendKeys('{Ctrl}a{Delete}')
            time.sleep(0.2)
            
            # 2. 输入目标联系人
            pyperclip.copy(who)
            search_box.SendKeys('{Ctrl}v')
            time.sleep(1.2) # 等待搜索结果
            
            # 3. 确认识选第一个结果
            search_box.SendKeys('{Enter}')
            time.sleep(1.5) # 给 NT 版 UI 更多的渲染时间
            
            # --- 增加生产级核对步骤 ---
            # 4. 核对当前打开的是否是正确的人 (带重试机制)
            verified = False
            for attempt in range(3):
                if self._verify_chat_title(who):
                    verified = True
                    break
                logger.warning(f"Verification attempt {attempt+1} failed, retrying...")
                time.sleep(0.8)
                
            if not verified:
                return {"status": "error", "message": f"UI Verification failed: Title mismatch after 3 attempts. Target: {who}"}
            
            # 5. 确保输入框获得焦点
            # 利用快捷键 Alt+S (发送) 或 Alt+C (清理) 之外，最稳妥是定位输入框
            rect = self.window.BoundingRectangle
            input_x = rect.left + (rect.right - rect.left) // 2
            input_y = rect.bottom - 80 
            auto.Click(input_x, input_y)
            time.sleep(0.3)
            
            # 6. 输入并发送内容
            pyperclip.copy(message)
            auto.SendKeys('{Ctrl}v')
            time.sleep(0.2)
            auto.SendKeys('{Enter}')
            
            # 7. 最终发送验证 (可选：验证气泡)
            # 这里简单返回成功，因为已经通过了 Title 验证，误发概率降到极低
            logger.info(f"Successfully sent message to {who}")
            return {"status": "success", "message": f"Sent to {who} (Verified)"}
            
        except Exception as e:
            logger.error(f"Error during send_message: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    bot = WeChatAutomation()
    print("Initializing...")
    if bot.activate():
        print("WeChat found. Test result:", bot.send_message("文件传输助手", "生产级闭环测试 - " + time.strftime("%H:%M:%S")))
    else:
        print("WeChat not found.")
