/**
 * Error Handler - 前端统一错误处理
 */

// API 错误响应类型
export interface APIErrorResponse {
    success: false;
    error: string;
    error_code?: string;
    details?: Record<string, unknown>;
    rate_limit?: {
        limit: number;
        remaining: number;
        reset_after: number;
    };
}

// 自定义错误类
export class APIError extends Error {
    code: string;
    details?: Record<string, unknown>;
    statusCode: number;

    constructor(message: string, code: string, statusCode: number, details?: Record<string, unknown>) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.statusCode = statusCode;
        this.details = details;
    }
}

// 错误代码到用户友好消息的映射
const ERROR_MESSAGES: Record<string, string> = {
    'VALIDATION_ERROR': '请求参数无效，请检查输入',
    'AUTH_ERROR': '认证失败，请重新登录',
    'NOT_FOUND': '请求的资源不存在',
    'RATE_LIMIT': '请求过于频繁，请稍后再试',
    'API_KEY_ERROR': 'AI 服务配置错误，请联系管理员',
    'EXTERNAL_API_ERROR': 'AI 服务暂时不可用，请稍后重试',
    'DATABASE_ERROR': '数据服务异常，请稍后重试',
    'CONNECTION_ERROR': '网络连接失败，请检查网络',
    'TIMEOUT_ERROR': '请求超时，请稍后重试',
    'INTERNAL_ERROR': '服务器内部错误，请稍后重试',
};

/**
 * 获取用户友好的错误消息
 */
export function getErrorMessage(error: unknown): string {
    if (error instanceof APIError) {
        return ERROR_MESSAGES[error.code] || error.message;
    }
    if (error instanceof Error) {
        return error.message;
    }
    return '发生未知错误';
}

/**
 * 解析 API 响应错误
 */
export async function parseAPIError(response: Response): Promise<APIError> {
    try {
        const data: APIErrorResponse = await response.json();
        return new APIError(
            data.error || '请求失败',
            data.error_code || 'UNKNOWN_ERROR',
            response.status,
            data.details
        );
    } catch {
        return new APIError(
            `HTTP ${response.status}: ${response.statusText}`,
            'HTTP_ERROR',
            response.status
        );
    }
}

/**
 * Toast 通知类型
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * 显示 Toast 通知（需要配合 UI 组件使用）
 */
export function showToast(message: string, type: ToastType = 'info') {
    // 简单实现：使用 console 和 alert
    // 实际项目中应该使用 toast 库如 react-hot-toast
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    if (type === 'error') {
        // 可以替换为更好的 UI 通知
        console.error(message);
    }
}

/**
 * 处理 API 调用的包装函数
 */
export async function handleAPICall<T>(
    apiCall: () => Promise<T>,
    options?: {
        onSuccess?: (data: T) => void;
        onError?: (error: APIError) => void;
        showErrorToast?: boolean;
    }
): Promise<T | null> {
    const { onSuccess, onError, showErrorToast = true } = options || {};
    
    try {
        const result = await apiCall();
        onSuccess?.(result);
        return result;
    } catch (error) {
        const apiError = error instanceof APIError 
            ? error 
            : new APIError(getErrorMessage(error), 'UNKNOWN_ERROR', 500);
        
        if (showErrorToast) {
            showToast(getErrorMessage(apiError), 'error');
        }
        
        onError?.(apiError);
        return null;
    }
}

