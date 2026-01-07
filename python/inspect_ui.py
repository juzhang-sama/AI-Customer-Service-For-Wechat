import uiautomation as auto
import time

def inspect_wechat():
    # Try multiple ways to find window
    window = auto.WindowControl(ClassName='WeChatMainWndForPC')
    if not window.Exists(0):
        window = auto.WindowControl(Name='Weixin')
    if not window.Exists(0):
        window = auto.WindowControl(Name='微信')
    
    if not window.Exists(0):
        # Root search
        for w in auto.GetRootControl().GetChildren():
            if 'Weixin' in w.Name or '微信' in w.Name:
                window = w
                break
                
    if not window.Exists(0):
        print("WeChat window not found by any criteria.")
        return

    print(f"Found Window: {window.Name} ({window.ClassName})")
    print("Dumping top-level TextControls...")
    
    # Walk through children to find TextControls
    for i, control in enumerate(window.GetChildren()):
        print(f"[{i}] {control.ControlTypeName}: '{control.Name}' at {control.BoundingRectangle}")
        # Search one level deeper for specific panes
        for j, sub in enumerate(control.GetChildren()):
             if sub.ControlTypeName in ['TextControl', 'ButtonControl']:
                 print(f"  -- [{i}.{j}] {sub.ControlTypeName}: '{sub.Name}' at {sub.BoundingRectangle}")

    print("\nSearching for targeted chat title...")
    # Find all TextControls regardless of depth (limit to reasonable count)
    all_texts = window.GetRuntimeId() # trigger search
    candidates = []
    
    def walk(control, depth):
        if depth > 5: return
        name = control.Name
        if control.ControlTypeName == 'TextControl' and name:
            candidates.append((name, control.BoundingRectangle, depth))
        for child in control.GetChildren():
            walk(child, depth + 1)

    walk(window, 0)
    
    print("\nPossible Titile Candidates (TextControls found):")
    for name, rect, depth in candidates:
        print(f"Depth {depth}: '{name}' at {rect}")

if __name__ == "__main__":
    inspect_wechat()
