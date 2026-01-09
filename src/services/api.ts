/**
 * API 服务配置
 * 统一管理 API 地址和认证
 */

// API 基础地址
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

// API Key (从环境变量获取)
const API_KEY = import.meta.env.VITE_API_KEY || '';

/**
 * 获取认证头
 */
export function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };
    
    if (API_KEY) {
        headers['X-API-Key'] = API_KEY;
    }
    
    return headers;
}

/**
 * 封装的 fetch 函数，自动添加认证头
 */
export async function apiFetch(
    endpoint: string, 
    options: RequestInit = {}
): Promise<Response> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    const headers = {
        ...getAuthHeaders(),
        ...options.headers,
    };
    
    return fetch(url, {
        ...options,
        headers,
    });
}

/**
 * GET 请求
 */
export async function apiGet<T>(endpoint: string): Promise<T> {
    const response = await apiFetch(endpoint);
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * POST 请求
 */
export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * PUT 请求
 */
export async function apiPut<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await apiFetch(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

/**
 * DELETE 请求
 */
export async function apiDelete<T>(endpoint: string): Promise<T> {
    const response = await apiFetch(endpoint, {
        method: 'DELETE',
    });
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

// API 端点常量
export const API_ENDPOINTS = {
    // 状态
    STATUS: '/api/status',
    
    // 消息
    SEND_MESSAGE: '/api/send',
    MESSAGE_STREAM: '/api/messages/stream',
    
    // AI 专家
    AI_PROMPTS: '/api/ai/prompts',
    AI_GENERATE: '/api/ai/generate',
    AI_RECORD_SELECTION: '/api/ai/record-selection',
    AI_RECORD_MODIFICATION: '/api/ai/record-modification',
    
    // 看板
    KANBAN_TASKS: '/api/ai/kanban/tasks',
    
    // 分析
    ANALYTICS_OVERVIEW: '/api/ai/analytics/overview',
    ANALYTICS_TRENDS: '/api/ai/analytics/trends',
    
    // 配置
    CONFIG: '/api/ai/config',
} as const;

