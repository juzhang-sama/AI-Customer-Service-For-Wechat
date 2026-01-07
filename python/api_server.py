

from flask import Flask, request, jsonify
from flask_cors import CORS
from wechat_auto import WeChatAutomation
from message_listener import WeChatMessageListener
from ai_expert_api import ai_expert_bp
import threading
import json
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 注册 AI Expert Blueprint
from ai_expert_api import ai_expert_bp, start_background_worker
app.register_blueprint(ai_expert_bp)

# 启动 AI 专家后台预生成服务
start_background_worker()

bot = WeChatAutomation()

# Global message queue for listener
message_queue = []
message_lock = threading.Lock()

from ai_expert_api import ai_expert_bp, start_background_worker, queue_manager

def on_new_message(msg):
    # 🔧 增强日志：后端控制台实时报信，方便排查
    print(f"\n[SERVER] >>> 新消息捕获: [{msg['sender']}] {msg['content'][:20]}... (is_self={msg['is_self']})")
    
    # 1. 更新内存队列
    with message_lock:
        message_queue.append(msg)
        if len(message_queue) > 50:
            message_queue.pop(0)
    
    # 2. 持久化入队
    try:
        session_id = msg.get('session', '')
        customer_name = msg.get('sender', '')
        content = msg.get('content', '')
        is_self = msg.get('is_self', False)
        if not is_self and session_id and content:
            queue_manager.enqueue_message(session_id, customer_name, content)
    except Exception as e:
        print(f"[Queue Error] {e}")

@app.route('/api/debug/queue', methods=['GET'])
def debug_queue():
    """查看当前内存消息队列状态"""
    return jsonify({
        "len": len(message_queue),
        "messages": message_queue[-10:] if message_queue else []
    })

# 守护进程：确保监听器线程永远在线
listener = None
def start_listener_with_watchdog():
    global listener
    def run_watchdog():
        global listener
        while True:
            if listener is None or not listener.is_alive():
                print("[Watchdog] 监测到监听器未启动或已停止，正在启动/重新启动...")
                listener = WeChatMessageListener(callback=on_new_message)
                listener.start()
            time.sleep(10)
    
    watchdog_thread = threading.Thread(target=run_watchdog, daemon=True)
    watchdog_thread.start()

start_listener_with_watchdog()

@app.route('/api/status', methods=['GET'])
def get_status():
    if bot.activate():
        return jsonify({"connected": True, "message": "WeChat is running and detected"})
    return jsonify({"connected": False, "message": "WeChat not found"})

@app.route('/api/send', methods=['POST'])
def send_msg():
    import comtypes
    comtypes.CoInitialize()
    data = request.json
    print(f"\n[DEBUG] Received JSON: {data}")
    who = data.get('who')
    message = data.get('message')
    print(f"[DEBUG] who = {repr(who)}")
    print(f"[DEBUG] message = {repr(message)}")
    
    if not who or not message:
        return jsonify({"status": "error", "message": "Missing 'who' or 'message'"}), 400
        
    try:
        result = bot.send_message(who, message)
        return jsonify(result)
    except Exception as e:
        print(f"Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/messages/stream')
def stream_messages():
    def event_stream():
        # Track which messages have been sent to this specific client
        last_sent_index = len(message_queue)
        last_heartbeat = time.time()
        while True:
            # 1. 检查新消息
            new_msgs = []
            with message_lock:
                if len(message_queue) > last_sent_index:
                    new_msgs = message_queue[last_sent_index:]
                    last_sent_index = len(message_queue)
            
            for msg in new_msgs:
                yield f"data: {json.dumps(msg)}\n\n"
            
            # 2. 定期发送心跳包 (每 15 秒)
            if time.time() - last_heartbeat > 15:
                # 使用标准的 data 格式发送心跳，确保前端 onmessage 能被触发
                yield f"data: {json.dumps({'type': 'heartbeat', 'time': time.strftime('%H:%M:%S')})}\n\n"
                last_heartbeat = time.time()
            
            time.sleep(1)
            
    from flask import Response
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("Starting API Server on port 5000...")
    # 显式开启多线程模式，增强 SSE 并发处理能力
    app.run(port=5000, threaded=True)
