# -*- coding: utf-8 -*-
import uiautomation as auto
import time

def diagnose():
    print("="*50)
    print("微信 UI 自动化诊断工具 - 正在深度扫描...")
    print("="*50)

    # 1. 尝试寻找窗口
    window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信', searchDepth=1)
    
    if not window.Exists(0):
        print("[错误] 未能找到微信主窗口！请确保微信已登录且窗口未被最小化。")
        return

    print(f"[成功] 找到微信窗口: Class={window.ClassName}, Name={window.Name}")
    
    # 2. 扫描侧边栏导航（确认是否在正确的 Tab）
    # 微信通常第一个是聊天，第二个是通讯录
    print("\n[扫描侧边栏图标...]")
    toolbar = window.ToolBarControl(Name='导航')
    if toolbar.Exists(0):
        for btn in toolbar.GetChildren():
            print(f"  - 按钮: {btn.Name}")
    else:
        print("  - 未找到名为'导航'的工具栏")

    # 3. 扫描会话列表
    print("\n[正在枚举可能的会话列表控制台...]")
    # 尝试多种可能的识别方式
    candidates = [
        window.ListControl(Name='会话'),
        window.ListControl(ClassName='ListView'),
        window.Control(Name='会话')
    ]

    found_list = None
    for cand in candidates:
        if cand.Exists(0):
            print(f"[找到列表候选] Name={cand.Name}, Class={cand.ClassName}")
            found_list = cand
            break
    
    if not found_list:
        print("[严重错误] 无法定位会话列表。微信界面可能发生了重大变化。")
        return

    # 4. 打印前 10 条会话项的原始名称
    print("\n[会话项探测 - 前 10 条]:")
    items = found_list.GetChildren()
    if not items:
        print("  - 列表为空")
    else:
        for i, item in enumerate(items[:10]):
            print(f"  {i+1}. 原始名称: \"{item.Name}\"")
            # 也可以看一下子控件
            # children = item.GetChildren()
            # for j, child in enumerate(children):
            #     print(f"     └─ 子项 {j}: {child.Name} (Class={child.ClassName})")

    print("\n诊断完成。请将此结果反馈给我。")

if __name__ == "__main__":
    diagnose()
