# 🟡 中等问题修复指南

本文档总结了代码审查中发现的中等优先级问题及其解决方案。

## 问题 1: CORS 配置过于宽松 ✅ 已修复（Phase 1）

已在严重问题修复中完成，见 `docs/SECURITY_FIXES.md`

---

## 问题 2: 缺少请求频率限制 ✅ 已修复

### 解决方案
创建了 `python/ai_expert/rate_limiter.py` 速率限制模块

### 特性
- 滑动窗口算法
- 支持自定义限制级别
- 返回标准 HTTP 头 (X-RateLimit-*)

### 使用方法
```python
from ai_expert.rate_limiter import rate_limit

@app.route('/api/expensive')
@rate_limit(max_requests=10, window_seconds=60)  # 每分钟10次
def expensive_operation():
    ...
```

### 已应用的端点
- `/api/ai/generate` - 每分钟 20 次

---

## 问题 3: 前端数据无缓存 ✅ 已修复

### 解决方案
创建了以下 Hooks:
- `src/hooks/useDataCache.ts` - 通用数据缓存
- `src/hooks/useAIExperts.ts` - AI 专家数据缓存

### 使用方法
```typescript
import { useAIExperts } from '@/hooks';

function MyComponent() {
    const { experts, isLoading, refresh } = useAIExperts();
    // experts 会被缓存 2 分钟
}
```

---

## 问题 4: 组件过大难维护 ⏳ 部分完成

### 已完成
- 提取了 `useSSEConnection` Hook
- 提取了 `useDataCache` Hook
- 提取了 `useAIExperts` Hook

### 待完成
- MessageCenter 组件拆分
- InlineReplyGenerator 组件拆分

---

## 问题 5: 错误处理过于宽泛 ✅ 已修复

### 后端解决方案
创建了 `python/ai_expert/error_handler.py`:
- 自定义异常类层次结构
- 统一错误处理装饰器
- 用户友好的错误消息

### 前端解决方案
创建了 `src/utils/errorHandler.ts`:
- API 错误解析
- 错误消息映射
- Toast 通知工具

### 使用方法
```python
# 后端
from ai_expert.error_handler import handle_errors, ValidationError

@app.route('/api/example')
@handle_errors
def example():
    if not valid:
        raise ValidationError('参数无效')
```

```typescript
// 前端
import { handleAPICall, getErrorMessage } from '@/utils/errorHandler';

const result = await handleAPICall(
    () => fetch('/api/example'),
    { showErrorToast: true }
);
```

---

## 问题 6: SSE 重连无退避策略 ✅ 已修复

### 解决方案
创建了 `src/hooks/useSSEConnection.ts`

### 特性
- 指数退避重连 (1s → 2s → 4s → ... → 30s max)
- 随机抖动防止雷群效应
- 心跳超时检测
- 最大重试次数限制

### 使用方法
```typescript
import { useSSEConnection } from '@/hooks';

const { isConnected, isRetrying, reconnect } = useSSEConnection({
    url: 'http://localhost:5000/api/messages/stream',
    onMessage: (data) => console.log(data),
    maxRetries: 10,
    initialRetryDelay: 1000,
    maxRetryDelay: 30000,
});
```

---

## 新增文件清单

| 文件 | 说明 |
|-----|------|
| `python/ai_expert/rate_limiter.py` | 请求频率限制器 |
| `python/ai_expert/error_handler.py` | 统一错误处理 |
| `src/hooks/useSSEConnection.ts` | SSE 连接 Hook |
| `src/hooks/useDataCache.ts` | 数据缓存 Hook |
| `src/hooks/useAIExperts.ts` | AI 专家数据 Hook |
| `src/hooks/index.ts` | Hooks 索引 |
| `src/utils/errorHandler.ts` | 前端错误处理 |
| `src/services/api.ts` | API 服务封装 |

---

## 下一步建议

1. **组件拆分** - 将 MessageCenter 拆分为更小的组件
2. **应用新 Hooks** - 在现有组件中使用新的 Hooks
3. **添加 Toast UI** - 集成 react-hot-toast 等库

