

import uiautomation as auto
import time
import pyperclip

class WeChatAutomation:
    def __init__(self):
        self.window = None
        
    def _get_window(self):
        # Try simplified search first
        window = auto.WindowControl(Name='微信', searchDepth=1)
        if not window.Exists(0):
            # Fallback to ClassName
            window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=1)
        
        if window.Exists(0):
            self.window = window
            return True
        return False

    def activate(self):
        if self._get_window():
            self.window.SetActive()
            return True
        return False

    def send_message(self, who, message):
        if not self.activate():
            return {"status": "error", "message": "WeChat window not found"}

        # 1. Click Search Box and clear any previous content
        search_box = self.window.EditControl(Name='搜索')
        if not search_box.Exists(1):
            return {"status": "error", "message": "Search box not found"}
        
        search_box.Click()
        time.sleep(0.2)
        
        # Clear search box completely
        search_box.SendKeys('{Ctrl}a')
        time.sleep(0.1)
        search_box.SendKeys('{Delete}')
        time.sleep(0.2)
        
        # 2. Enter 'who' using Clipboard
        pyperclip.copy(who)
        time.sleep(0.2)
        search_box.SendKeys('{Ctrl}v')
        time.sleep(2.0) # Wait longer for search results to populate
        
        # 3. Select the first result
        search_box.SendKeys('{Enter}')
        time.sleep(2.0) # Wait for chat window to open
        
        # 4. Click the message input area to ensure focus
        # We'll click at the bottom-center of the WeChat window
        # Get window rect and click in the input area
        rect = self.window.BoundingRectangle
        input_x = rect.left + (rect.right - rect.left) // 2  # Center horizontally
        input_y = rect.bottom - 100  # 100 pixels from bottom (where input box usually is)
        
        auto.Click(input_x, input_y)
        time.sleep(0.5)
        
        # 5. Type Message using keyboard
        pyperclip.copy(message)
        time.sleep(0.3)
        auto.SendKeys('{Ctrl}v')
        time.sleep(0.3)
        auto.SendKeys('{Enter}')
        time.sleep(0.5)
        
        return {"status": "success", "message": f"Sent to {who}"}

if __name__ == "__main__":
    bot = WeChatAutomation()
    print("Initializing...")
    if bot.activate():
        print("WeChat found. Testing send...")
        # bot.send_message("File Transfer", "Hello from Python Auto")
    else:
        print("WeChat not found.")
