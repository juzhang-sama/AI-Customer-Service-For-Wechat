# 🟢 轻微问题修复指南

本文档总结了代码审查中发现的轻微优先级问题及其解决方案。

## 问题 1: 日志不规范 ✅ 已修复

### 解决方案
- 创建了 `python/ai_expert/logger.py` 统一日志模块
- 将所有 `print()` 替换为 `logger.info/debug/warning/error`

### 使用方法
```python
from ai_expert.logger import api_logger as logger

logger.info("操作成功")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)
logger.debug("调试信息")
```

---

## 问题 2: 魔法数字 ✅ 已修复

### 后端常量
创建了 `python/ai_expert/constants.py`:
- 时间相关: `SSE_HEARTBEAT_INTERVAL`, `API_REQUEST_TIMEOUT`
- 速率限制: `RATE_LIMIT_AI_GENERATE`, `RATE_LIMIT_WINDOW`
- 消息相关: `MAX_MESSAGES_PER_SESSION`
- AI 生成: `AI_MAX_TOKENS`, `AI_TEMPERATURE_*`

### 前端常量
创建了 `src/utils/constants.ts`:
- SSE 相关: `SSE_HEARTBEAT_TIMEOUT`, `SSE_RECONNECT_*`
- 缓存相关: `CACHE_TTL_SHORT/MEDIUM/LONG`
- UI 相关: `SIDEBAR_WIDTH`, `MOBILE_BREAKPOINT`

---

## 问题 3: 缺少单元测试 ✅ 已添加

### 测试文件
创建了 `python/tests/test_ai_expert.py`:
- `TestRateLimiter` - 速率限制器测试
- `TestErrorHandler` - 错误处理器测试
- `TestConstants` - 常量测试

### 运行测试
```bash
cd python
pytest tests/test_ai_expert.py -v
```

---

## 问题 4-8: 待完成

| 问题 | 状态 | 说明 |
|-----|------|------|
| 文档注释不完整 | ⏳ | 需要逐步补充 |
| 代码重复 | ⏳ | 需要重构 |
| 类型注解缺失 | ⏳ | 需要逐步添加 |
| TODO/FIXME 未处理 | ⏳ | 需要清理 |
| 配置硬编码 | ⏳ | 部分已通过常量解决 |

---

## 新增文件清单

| 文件 | 说明 |
|-----|------|
| `python/ai_expert/logger.py` | 统一日志配置 |
| `python/ai_expert/constants.py` | 后端常量定义 |
| `src/utils/constants.ts` | 前端常量定义 |
| `python/tests/test_ai_expert.py` | 单元测试 |

---

## 修改文件清单

| 文件 | 修改内容 |
|-----|---------|
| `python/ai_expert_api.py` | print → logger |
| `src/hooks/useSSEConnection.ts` | 使用常量 |
| `src/hooks/useDataCache.ts` | 使用常量 |

