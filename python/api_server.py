

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
app.register_blueprint(ai_expert_bp)

bot = WeChatAutomation()

# Global message queue for listener
message_queue = []
message_lock = threading.Lock()

def on_new_message(msg):
    with message_lock:
        message_queue.append(msg)
        # Keep only last 50 messages
        if len(message_queue) > 50:
            message_queue.pop(0)

listener = WeChatMessageListener(callback=on_new_message)
listener.start()

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
                yield ": heartbeat\n\n"
                last_heartbeat = time.time()
            
            time.sleep(1)
            
    from flask import Response
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    print("Starting API Server on port 5000...")
    app.run(port=5000)
