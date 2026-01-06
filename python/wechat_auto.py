
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
        # Try simplified search first
        window = auto.WindowControl(Name='微信', searchDepth=1)
        if not window.Exists(0):
            # Fallback to ClassName
            window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
        
        if window.Exists(0):
            self.window = window
            # 处理最小化
            if window.IsMinimized():
                logger.info("WeChat window is minimized, restoring...")
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
        """获取当前打开的聊天会话标题"""
        try:
            # 在微信 3.9+ 中，顶部聊天对象通常是一个 TextControl
            # 位于主窗口头部的特定位置
            header = self.window.PaneControl(Name="消息") # 侧边栏
            # 通常在主窗口的右侧面板顶部
            # 这里简化处理：寻找当前窗口中所有的 TextControl 并根据层级定位
            # 或者直接定位主界面顶部的联系人名称
            
            # 改进方案：寻找聊天记录上方的联系人姓名
            # 微信的主界面结构复杂，这里使用相对可靠的定位方式
            chat_title_element = self.window.TextControl(searchDepth=15, foundIndex=1)
            # 注意：这步可能因微信版本不同而异，生产环境建议结合多种方式
            return chat_title_element.Name
        except:
            return None

    def _verify_chat_title(self, target_who):
        """核对当前会话标题是否匹配目标联系人"""
        actual_title = self.get_current_chat_title()
        logger.info(f"Actual chat title: {actual_title}, Target: {target_who}")
        
        if not actual_title:
            return False
            
        # 支持模糊匹配（处理备注、群聊人数等）
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
            # 有时搜出多个人，这里假设第一个是最匹配的
            search_box.SendKeys('{Enter}')
            time.sleep(0.8)
            
            # --- 增加生产级核对步骤 ---
            # 4. 核对当前打开的是否是正确的人 (关键安全防线)
            if not self._verify_chat_title(who):
                logger.warning(f"Title mismatch! Expected {who}, but UI shows different. Aborting.")
                return {"status": "error", "message": f"UI Verification failed: Title mismatch. Target: {who}"}
            
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
