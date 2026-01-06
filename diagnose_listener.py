# -*- coding: utf-8 -*-
"""
微信监听器完整诊断工具
"""
import sys
import os
import time
import json
import uiautomation as auto

# 添加python目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(current_dir, 'python')
sys.path.insert(0, python_dir)

def check_wechat_window():
    """检查微信窗口是否可访问"""
    print("🔍 检查微信窗口...")
    
    # 尝试找到微信窗口
    window = auto.WindowControl(ClassName='mmui::MainWindow', searchDepth=1)
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信', searchDepth=1)
    
    if window.Exists(0):
        print("✅ 微信窗口已找到")
        
        # 检查会话列表
        session_list = window.ListControl(Name='会话')
        if session_list.Exists(0):
            print("✅ 会话列表已找到")
            
            # 获取会话项目
            items = session_list.GetChildren()
            print(f"📋 当前会话数量: {len(items)}")
            
            # 显示前5个会话
            print("📝 前5个会话:")
            for i, item in enumerate(items[:5]):
                print(f"   {i+1}. {item.Name}")
            
            return True, items
        else:
            print("❌ 会话列表未找到")
            return False, []
    else:
        print("❌ 微信窗口未找到")
        return False, []

def check_config():
    """检查配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_path = os.path.join(current_dir, 'config', 'ai_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            keyword = config.get('monitor_keyword', '客户')
            match_mode = config.get('monitor_match_mode', 'contains')
            
            print(f"✅ 配置文件读取成功")
            print(f"   监听关键词: '{keyword}'")
            print(f"   匹配模式: {match_mode}")
            
            return keyword, match_mode
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return '客户', 'contains'

def test_keyword_matching(items, keyword, match_mode):
    """测试关键词匹配"""
    print(f"\n🔍 测试关键词匹配 (关键词: '{keyword}', 模式: {match_mode})...")
    
    matched_sessions = []
    
    for item in items:
        raw_name = item.Name
        if not raw_name:
            continue
            
        # 简单解析会话名（取第一个空格前的部分作为昵称）
        parts = raw_name.split(' ')
        nickname = parts[0] if parts else ''
        
        # 清理昵称（移除数字、"条未读"等）
        import re
        clean_nickname = re.sub(r'\d+条未读|已置顶|消息免打扰', '', nickname).strip()
        
        # 测试匹配
        matched = False
        if match_mode == 'startswith':
            matched = clean_nickname.startswith(keyword)
        elif match_mode == 'contains':
            matched = keyword in clean_nickname
        elif match_mode == 'exact':
            matched = clean_nickname == keyword
        else:
            matched = keyword in clean_nickname
        
        if matched:
            matched_sessions.append({
                'raw_name': raw_name,
                'clean_nickname': clean_nickname,
                'matched': True
            })
            print(f"✅ 匹配: '{clean_nickname}' (原始: {raw_name})")
        else:
            print(f"❌ 不匹配: '{clean_nickname}' (原始: {raw_name})")
    
    print(f"\n📊 匹配结果: {len(matched_sessions)} 个会话匹配关键词")
    return matched_sessions

def main():
    print("🚀 微信监听器完整诊断")
    print("=" * 50)
    
    # 1. 检查配置
    keyword, match_mode = check_config()
    
    # 2. 检查微信窗口
    wechat_ok, items = check_wechat_window()
    
    if not wechat_ok:
        print("\n❌ 微信窗口检查失败，请确保:")
        print("   1. 微信已打开")
        print("   2. 微信窗口可见")
        return
    
    # 3. 测试关键词匹配
    matched_sessions = test_keyword_matching(items, keyword, match_mode)
    
    # 4. 总结
    print("\n" + "=" * 50)
    print("📋 诊断总结:")
    print(f"   配置状态: ✅")
    print(f"   微信窗口: ✅")
    print(f"   会话列表: ✅")
    print(f"   匹配会话: {len(matched_sessions)} 个")
    
    if len(matched_sessions) == 0:
        print("\n⚠️  没有找到匹配的会话，可能原因:")
        print("   1. 没有以'客户'开头或包含'客户'的联系人")
        print("   2. 关键词设置不正确")
        print("   3. 匹配模式不合适")
        print("\n💡 建议:")
        print("   1. 检查联系人名称是否真的包含'客户'")
        print("   2. 尝试修改匹配模式为'contains'")
        print("   3. 尝试修改关键词为更常见的词")
    else:
        print(f"\n✅ 找到 {len(matched_sessions)} 个匹配的会话")
        print("💡 如果监听器仍然不工作，可能是:")
        print("   1. 监听器线程没有启动")
        print("   2. 消息状态变化检测有问题")
        print("   3. SSE连接有问题")

if __name__ == "__main__":
    main()
