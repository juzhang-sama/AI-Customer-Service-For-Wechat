# 状态管理规范

## 核心原则

**所有需要跨页面保持的状态，必须放在 Context 中，禁止放在组件内部。**

## 判断标准

| 状态类型 | 放置位置 | 示例 |
|---------|---------|------|
| 跨页面共享 | Context | 消息会话、用户设置、AI专家配置 |
| SSE/WebSocket 连接 | Context | 消息流连接 |
| 需要持久化 | Context + localStorage | 会话历史 |
| 仅当前组件使用 | 组件内 useState | 表单输入、UI 状态 |

## 现有 Context

### MessageContext
- **用途**: 微信消息状态管理
- **包含**: SSE 连接、会话列表、消息历史
- **持久化**: localStorage

## 添加新状态的检查清单

在添加新的 useState 之前，问自己：

1. ✅ 这个状态是否只在当前组件使用？
2. ✅ 页面切换后，这个状态丢失是否可接受？
3. ✅ 这个状态是否涉及长连接（SSE/WebSocket）？

如果任何一个答案是"否"，就应该使用 Context。

## 禁止事项

❌ 在组件内部建立 SSE/WebSocket 连接
❌ 在组件内部管理需要跨页面的数据
❌ 在多个组件中重复定义相同的状态

## 文件结构

```
src/contexts/
├── README.md          # 本规范文档
├── MessageContext.tsx # 消息状态管理
└── index.ts           # 统一导出
```

