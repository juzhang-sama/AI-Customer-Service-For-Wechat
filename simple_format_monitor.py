# -*- coding: utf-8 -*-
"""
实时显示微信原始消息格式的工具
帮助我们准确理解消息格式差异
"""
import uiautomation as auto
import time

def main():
    print("🔍 微信消息格式实时监控")
    print("=" * 60)
    print("💡 操作步骤:")
    print("1. 确保微信已打开")
    print("2. 找到包含'客户'的联系人")
    print("3. 让对方发送一条消息，观察输出")
    print("4. 然后您回复一条消息，观察输出")
    print("5. 对比两种消息的原始格式差异")
    print("⏹️  按 Ctrl+C 停止监控")
    print("=" * 60)
    
    # 找到微信窗口
    window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信', searchDepth=1)
    
    if not window.Exists(0):
        print("❌ 无法找到微信窗口，请确保微信已打开")
        return
    
    session_list = window.ListControl(Name='会话')
    if not session_list.Exists(0):
        print("❌ 无法找到会话列表")
        return
    
    print("✅ 微信窗口已找到，开始监控...")
    print()
    
    last_raw_messages = {}
    
    try:
        while True:
            items = session_list.GetChildren()
            
            for item in items:
                raw_name = item.Name
                if not raw_name or '客户' not in raw_name:
                    continue
                
                # 检查是否有变化
                session_key = raw_name.split()[0] if raw_name.split() else 'unknown'
                
                if session_key not in last_raw_messages or last_raw_messages[session_key] != raw_name:
                    print(f"🔔 消息变化检测:")
                    print(f"原始格式: '{raw_name}'")
                    print(f"时间: {time.strftime('%H:%M:%S')}")
                    
                    # 简单分析
                    if '我:' in raw_name or '我：' in raw_name:
                        print("🟢 可能是我发送的消息（包含'我:'）")
                    else:
                        print("🔵 可能是对方发送的消息（不包含'我:'）")
                    
                    print("-" * 60)
                    last_raw_messages[session_key] = raw_name
            
            time.sleep(0.3)
            
    except KeyboardInterrupt:
        print("\n🛑 监控结束")
        print("\n📋 请将上面显示的消息格式发给我，我会根据实际格式修复识别逻辑")

if __name__ == "__main__":
    main()
