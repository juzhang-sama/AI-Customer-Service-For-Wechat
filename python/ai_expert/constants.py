# -*- coding: utf-8 -*-
"""
Constants - 常量定义
避免魔法数字，集中管理配置值
"""

# ========== 时间相关 (秒) ==========
SSE_HEARTBEAT_INTERVAL = 15          # SSE 心跳间隔
SSE_HEARTBEAT_TIMEOUT = 30           # SSE 心跳超时
SSE_RECONNECT_DELAY = 5              # SSE 重连延迟
API_REQUEST_TIMEOUT = 60             # API 请求超时
BACKGROUND_TASK_INTERVAL = 2         # 后台任务检查间隔

# ========== 速率限制 ==========
RATE_LIMIT_AI_GENERATE = 20          # AI 生成每分钟最大次数
RATE_LIMIT_NORMAL = 60               # 普通 API 每分钟最大次数
RATE_LIMIT_WINDOW = 60               # 速率限制窗口 (秒)

# ========== 消息相关 ==========
MAX_MESSAGES_PER_SESSION = 100       # 每个会话最大消息数
MAX_CONVERSATION_HISTORY = 10        # AI 上下文最大历史消息数
MESSAGE_PREVIEW_LENGTH = 50          # 消息预览长度

# ========== AI 生成相关 ==========
AI_MAX_TOKENS = 2000                 # AI 生成最大 token 数
AI_TEMPERATURE_AGGRESSIVE = 0.8      # 激进版温度
AI_TEMPERATURE_CONSERVATIVE = 0.3    # 保守版温度
AI_TEMPERATURE_PROFESSIONAL = 0.5    # 专业版温度
AI_MODEL_DEFAULT = "deepseek-chat"   # 默认模型

# ========== 知识库相关 ==========
KB_CHUNK_SIZE = 500                  # 知识库分块大小
KB_CHUNK_OVERLAP = 50                # 知识库分块重叠
KB_TOP_K_RESULTS = 3                 # 知识库检索返回数量
KB_SIMILARITY_THRESHOLD = 0.7        # 相似度阈值

# ========== 缓存相关 (秒) ==========
CACHE_TTL_SHORT = 60                 # 短期缓存 1 分钟
CACHE_TTL_MEDIUM = 300               # 中期缓存 5 分钟
CACHE_TTL_LONG = 3600                # 长期缓存 1 小时

# ========== 文件上传 ==========
MAX_UPLOAD_SIZE_MB = 10              # 最大上传文件大小 (MB)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}

# ========== 数据库 ==========
DB_POOL_SIZE = 5                     # 连接池大小
DB_TIMEOUT = 30                      # 数据库超时

# ========== 重试策略 ==========
MAX_RETRIES = 3                      # 最大重试次数
RETRY_DELAY_BASE = 1                 # 重试基础延迟 (秒)
RETRY_DELAY_MAX = 30                 # 重试最大延迟 (秒)

