# API 文档

## 📡 Flask API 服务器

**基础 URL**: `http://127.0.0.1:5000`  
**CORS**: 已启用  
**内容类型**: `application/json`

---

## 🔌 API 端点

### 1. 检查状态

检查微信客户端连接状态。

**端点**: `GET /api/status`

**请求示例**:
```bash
curl http://127.0.0.1:5000/api/status
```

**响应示例**:
```json
{
  "status": "connected",
  "wechat_running": true,
  "timestamp": "2025-12-31T10:30:00"
}
```

**状态码**:
- `200 OK` - 微信已连接
- `503 Service Unavailable` - 微信未运行

---

### 2. 发送消息

向指定联系人发送消息。

**端点**: `POST /api/send`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "who": "联系人名称",
  "message": "要发送的消息内容"
}
```

**字段说明**:
- `who` (string, 必填): 联系人昵称或备注名，必须完全匹配
- `message` (string, 必填): 消息内容，支持多行文本

**请求示例**:
```bash
curl -X POST http://127.0.0.1:5000/api/send \
  -H "Content-Type: application/json" \
  -d '{
    "who": "张三",
    "message": "你好，这是一条测试消息"
  }'
```

**成功响应**:
```json
{
  "status": "success",
  "message": "Message sent successfully",
  "recipient": "张三",
  "timestamp": "2025-12-31T10:35:00"
}
```

**失败响应**:
```json
{
  "status": "error",
  "message": "WeChat window not found",
  "error_code": "WECHAT_NOT_FOUND"
}
```

**状态码**:
- `200 OK` - 消息发送成功
- `400 Bad Request` - 请求参数错误
- `500 Internal Server Error` - 发送失败

**错误代码**:
- `WECHAT_NOT_FOUND` - 微信窗口未找到
- `CONTACT_NOT_FOUND` - 联系人不存在
- `SEND_FAILED` - 发送失败

---

### 3. 消息流 (SSE)

实时接收微信消息推送。

**端点**: `GET /api/messages/stream`

**协议**: Server-Sent Events (SSE)

**请求示例**:
```javascript
const eventSource = new EventSource('http://127.0.0.1:5000/api/messages/stream');

eventSource.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('New message:', message);
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
};
```

**事件格式**:
```
data: {"session":"张三","sender":"张三","content":"你好","time":"16:30","unread":1,"timestamp":"2025-12-31T16:30:00"}

data: {"session":"李四","sender":"李四","content":"在吗","time":"16:31","unread":2,"timestamp":"2025-12-31T16:31:00"}
```

**消息字段**:
- `session` (string): 会话名称
- `sender` (string): 发送者名称
- `content` (string): 消息内容
- `time` (string): 消息时间（格式: HH:MM 或 "昨天" 或 "星期X"）
- `unread` (number): 未读消息数量
- `timestamp` (string): ISO 8601 时间戳

**心跳包**:
每 15 秒发送一次心跳包：
```
: heartbeat
```

**连接管理**:
- 自动重连: 客户端应实现断线重连
- 超时时间: 无限制
- 并发连接: 支持多个客户端

---

## 🔧 Electron IPC API

### 1. 扫描联系人

触发联系人扫描任务。

**通道**: `scan-contacts`

**发送**:
```typescript
window.electron.ipcRenderer.send('scan-contacts', {
  maxContacts: 100
});
```

**监听结果**:
```typescript
window.electron.ipcRenderer.on('contacts-updated', (event, contacts) => {
  console.log('Contacts:', contacts);
});
```

**返回数据**:
```typescript
interface Contact {
  nickname: string;
  remark?: string;
  wx_id?: string;
  mobile?: string;
  region?: string;
  signature?: string;
}

type Contacts = Contact[];
```

---

### 2. 读取联系人列表

从本地文件读取已扫描的联系人。

**通道**: `get-contacts`

**发送**:
```typescript
const contacts = await window.electron.ipcRenderer.invoke('get-contacts');
```

**返回数据**:
```typescript
interface Contact {
  id: number;
  nickname: string;
  remark?: string;
  wx_id?: string;
  mobile?: string;
  region?: string;
  signature?: string;
  created_at: string;
}

type Contacts = Contact[];
```

---

## 📊 数据模型

### Contact (联系人)

```typescript
interface Contact {
  id?: number;              // 数据库 ID (自增)
  nickname: string;         // 昵称 (必填)
  remark?: string;          // 备注名
  wx_id?: string;           // 微信号
  mobile?: string;          // 手机号
  region?: string;          // 地区
  signature?: string;       // 个性签名
  created_at?: string;      // 创建时间 (ISO 8601)
}
```

### Message (消息)

```typescript
interface Message {
  session: string;          // 会话名称
  sender: string;           // 发送者
  content: string;          // 消息内容
  time: string;             // 时间 (HH:MM 或相对时间)
  unread: number;           // 未读数量
  timestamp: string;        // ISO 8601 时间戳
}
```

---

## 🔐 认证与安全

### 当前状态
- ❌ 无认证机制
- ✅ 仅监听 localhost
- ✅ CORS 已配置

### 建议改进
```python
# 添加 API Key 认证
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != 'your-secret-key':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/send', methods=['POST'])
@require_api_key
def send_message():
    # ...
```

---

## 📈 速率限制

### 建议配置

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/send', methods=['POST'])
@limiter.limit("10 per minute")
def send_message():
    # ...
```

---

## 🧪 测试示例

### Python 测试

```python
import requests

# 测试状态
response = requests.get('http://127.0.0.1:5000/api/status')
print(response.json())

# 测试发送消息
response = requests.post('http://127.0.0.1:5000/api/send', json={
    'who': '文件传输助手',
    'message': '测试消息'
})
print(response.json())
```

### JavaScript 测试

```javascript
// 测试发送消息
async function sendMessage(who, message) {
  const response = await fetch('http://127.0.0.1:5000/api/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ who, message }),
  });
  
  const result = await response.json();
  console.log(result);
}

sendMessage('文件传输助手', '测试消息');
```

---

## 📝 更新日志

### v1.0.0 (2025-12-31)
- ✅ 实现基础 API 端点
- ✅ 支持消息发送
- ✅ 支持 SSE 消息流
- ✅ 支持联系人扫描

### 计划中
- ⏳ 添加认证机制
- ⏳ 实现速率限制
- ⏳ 支持批量操作
- ⏳ 添加 WebSocket 支持

---

**文档版本**: 1.0.0  
**最后更新**: 2025-12-31

