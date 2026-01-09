/**
 * Constants - 前端常量定义
 * 避免魔法数字，集中管理配置值
 */

// ========== 时间相关 (毫秒) ==========
export const SSE_HEARTBEAT_TIMEOUT = 30000;      // SSE 心跳超时 30秒
export const SSE_RECONNECT_INITIAL = 1000;       // SSE 初始重连延迟 1秒
export const SSE_RECONNECT_MAX = 30000;          // SSE 最大重连延迟 30秒
export const SSE_MAX_RETRIES = 10;               // SSE 最大重试次数
export const DEBOUNCE_DELAY = 300;               // 防抖延迟
export const TOAST_DURATION = 3000;              // Toast 显示时长

// ========== 消息相关 ==========
export const MAX_MESSAGES_PER_SESSION = 100;     // 每个会话最大消息数
export const MESSAGE_PREVIEW_LENGTH = 50;        // 消息预览长度

// ========== 缓存相关 (毫秒) ==========
export const CACHE_TTL_SHORT = 60 * 1000;        // 短期缓存 1 分钟
export const CACHE_TTL_MEDIUM = 5 * 60 * 1000;   // 中期缓存 5 分钟
export const CACHE_TTL_LONG = 60 * 60 * 1000;    // 长期缓存 1 小时

// ========== UI 相关 ==========
export const SIDEBAR_WIDTH = 280;                // 侧边栏宽度
export const MOBILE_BREAKPOINT = 768;            // 移动端断点

// ========== API 相关 ==========
export const API_TIMEOUT = 60000;                // API 请求超时 60秒
export const MAX_RETRY_ATTEMPTS = 3;             // 最大重试次数

// ========== 文件上传 ==========
export const MAX_UPLOAD_SIZE_MB = 10;            // 最大上传文件大小 (MB)
export const ALLOWED_FILE_TYPES = ['.txt', '.pdf', '.doc', '.docx', '.md'];

