# -*- coding: utf-8 -*-
"""
深度分析微信消息格式 - 检查所有可能的属性
"""
import uiautomation as auto
import time

def main():
    print("🔍 深度分析微信消息格式")
    print("=" * 60)
    
    window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信', searchDepth=1)
    
    if not window.Exists(0):
        print("❌ 无法找到微信窗口")
        return
    
    session_list = window.ListControl(Name='会话')
    if not session_list.Exists(0):
        print("❌ 无法找到会话列表")
        return
    
    print("✅ 微信窗口已找到")
    print("💡 请在微信中发送/接收消息，观察属性变化")
    print("⏹️  按 Ctrl+C 停止")
    print("=" * 60)
    
    last_states = {}
    
    try:
        while True:
            items = session_list.GetChildren()
            
            for item in items:
                raw_name = item.Name
                if not raw_name or '客户' not in raw_name:
                    continue
                
                # 检查是否有变化
                if raw_name != last_states.get(item.Name[:10], ''):
                    print(f"\n🔔 检测到变化:")
                    print(f"   Name: '{raw_name}'")
                    
                    # 尝试获取更多属性
                    try:
                        print(f"   ControlType: {item.ControlTypeName}")
                        print(f"   ClassName: {item.ClassName}")
                        print(f"   AutomationId: {item.AutomationId}")
                        
                        # 检查子元素
                        children = item.GetChildren()
                        if children:
                            print(f"   子元素数量: {len(children)}")
                            for i, child in enumerate(children[:5]):
                                print(f"      [{i}] Type={child.ControlTypeName}, Name='{child.Name}'")
                    except Exception as e:
                        print(f"   获取属性失败: {e}")
                    
                    print("-" * 60)
                    last_states[item.Name[:10]] = raw_name
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n🛑 分析结束")

if __name__ == "__main__":
    main()
