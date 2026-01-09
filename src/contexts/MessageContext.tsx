/**
 * MessageContext - 全局消息状态管理
 * 在应用顶层维护 SSE 连接，确保所有页面都能接收消息
 * 支持自动回复模式
 */

import React, { createContext, useContext, useEffect, useState, useRef, useCallback, ReactNode } from 'react';

// 类型定义
export interface Message {
    session: string;
    sender: string;
    content: string;
    unread: number;
    is_self: boolean;
    time: string;
    id?: number;
}

export interface ChatSession {
    id: string;
    lastMessage: string;
    lastTime: string;
    unreadCount: number;
    messages: Message[];
}

// 自动回复配置类型
export type ReplyStyle = 'aggressive' | 'conservative' | 'professional';

export interface AutoReplyConfig {
    enabled: boolean;
    replyStyle: ReplyStyle;
    selectedExpertId: number | null;  // 选择的 AI 专家 ID
    debounceSeconds: number;          // 防抖时间（秒）
}

// Toast 消息类型
export interface ToastMessage {
    id: string;
    type: 'success' | 'error';
    message: string;
}

interface MessageContextType {
    sessions: Record<string, ChatSession>;
    setSessions: React.Dispatch<React.SetStateAction<Record<string, ChatSession>>>;
    activeSessionId: string | null;
    setActiveSessionId: (id: string | null) => void;
    isConnected: boolean;
    isRetrying: boolean;
    deleteSession: (sessionId: string) => Promise<void>;
    deleteMessage: (sessionId: string, messageIndex: number) => void;
    clearUnread: (sessionId: string) => void;
    // 自动回复相关
    autoReplyConfig: AutoReplyConfig;
    setAutoReplyConfig: (config: AutoReplyConfig) => void;
    toasts: ToastMessage[];
    closeToast: (id: string) => void;
}

const MessageContext = createContext<MessageContextType | null>(null);

// 默认自动回复配置
const defaultAutoReplyConfig: AutoReplyConfig = {
    enabled: false,
    replyStyle: 'professional',
    selectedExpertId: null,
    debounceSeconds: 5
};

// Provider 组件
export function MessageProvider({ children }: { children: ReactNode }) {
    // 从 localStorage 恢复会话数据
    const [sessions, setSessions] = useState<Record<string, ChatSession>>(() => {
        try {
            const saved = localStorage.getItem('wechat_sessions');
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });

    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isRetrying, setIsRetrying] = useState(true);

    // 自动回复配置状态
    const [autoReplyConfig, setAutoReplyConfigState] = useState<AutoReplyConfig>(() => {
        try {
            const saved = localStorage.getItem('auto_reply_config');
            return saved ? JSON.parse(saved) : defaultAutoReplyConfig;
        } catch {
            return defaultAutoReplyConfig;
        }
    });

    // Toast 通知状态
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const eventSourceRef = useRef<EventSource | null>(null);
    const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
    const lastHeartbeatRef = useRef<number>(Date.now());

    // 自动回复防抖计时器
    const autoReplyTimersRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
    // 用于获取最新 sessions 的 ref
    const sessionsRef = useRef(sessions);
    const autoReplyConfigRef = useRef(autoReplyConfig);
    // triggerAutoReply 函数的 ref，避免 SSE 重连
    const triggerAutoReplyRef = useRef<((sessionId: string) => Promise<void>) | null>(null);

    // 同步 ref
    useEffect(() => {
        sessionsRef.current = sessions;
    }, [sessions]);

    useEffect(() => {
        autoReplyConfigRef.current = autoReplyConfig;
    }, [autoReplyConfig]);

    // 保存会话数据到 localStorage
    useEffect(() => {
        try {
            localStorage.setItem('wechat_sessions', JSON.stringify(sessions));
        } catch (error) {
            console.error('Failed to save sessions to localStorage:', error);
        }
    }, [sessions]);

    // 保存自动回复配置到 localStorage
    useEffect(() => {
        try {
            localStorage.setItem('auto_reply_config', JSON.stringify(autoReplyConfig));
        } catch (error) {
            console.error('Failed to save auto reply config:', error);
        }
    }, [autoReplyConfig]);

    // 设置自动回复配置
    const setAutoReplyConfig = useCallback((config: AutoReplyConfig) => {
        setAutoReplyConfigState(config);
    }, []);

    // Toast 通知函数
    const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
        const id = Date.now().toString();
        setToasts(prev => [...prev, { id, type, message }]);
        // 5秒后自动移除
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 5000);
    }, []);

    const closeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    // 自动回复核心函数
    const triggerAutoReply = useCallback(async (sessionId: string) => {
        const currentSessions = sessionsRef.current;
        const currentConfig = autoReplyConfigRef.current;

        const session = currentSessions[sessionId];
        if (!session) {
            console.log(`[AutoReply] 会话 ${sessionId} 不存在，跳过`);
            return;
        }

        // 获取最后一条客户消息
        const customerMessages = session.messages.filter(m => !m.is_self);
        const lastCustomerMessage = customerMessages[customerMessages.length - 1];

        if (!lastCustomerMessage) {
            console.log(`[AutoReply] 会话 ${sessionId} 没有客户消息，跳过`);
            return;
        }

        console.log(`[AutoReply] 开始为 ${sessionId} 生成自动回复...`);

        try {
            // 0. 确定使用的 AI 专家 ID
            let promptId: number | undefined = currentConfig.selectedExpertId || undefined;

            // 如果没有配置专家，尝试获取激活的或第一个可用的
            if (!promptId) {
                try {
                    const expertsResponse = await fetch('http://localhost:5000/api/ai/prompts');
                    const expertsData = await expertsResponse.json();
                    if (expertsData.success && expertsData.prompts && expertsData.prompts.length > 0) {
                        const activeExpert = expertsData.prompts.find((p: { is_active: number }) => p.is_active === 1);
                        promptId = activeExpert ? activeExpert.id : expertsData.prompts[0].id;
                    }
                } catch (e) {
                    console.log(`[AutoReply] 获取 AI 专家列表失败，将使用默认配置`);
                }
            }

            console.log(`[AutoReply] 使用 AI 专家 ID: ${promptId}`);

            // 1. 调用 AI 生成回复
            const requestBody: Record<string, unknown> = {
                session_id: sessionId,
                customer_message: lastCustomerMessage.content,
                conversation_history: session.messages.slice(-10).map(msg => ({
                    role: msg.is_self ? 'assistant' : 'user',
                    content: msg.content
                }))
            };

            // 如果有 prompt_id，添加到请求中
            if (promptId) {
                requestBody.prompt_id = promptId;
            }

            const response = await fetch('http://localhost:5000/api/ai/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log(`[AutoReply] AI 生成响应:`, data);

            if (!data.success || !data.suggestions) {
                // 显示具体的错误原因
                const errorMsg = data.error || 'AI 生成失败';
                throw new Error(errorMsg);
            }

            // 2. 根据配置选择回复风格
            const replyContent = data.suggestions[currentConfig.replyStyle];

            if (!replyContent) {
                throw new Error('未能获取到回复内容');
            }

            console.log(`[AutoReply] 生成回复成功，风格: ${currentConfig.replyStyle}, 内容: ${replyContent.substring(0, 50)}...`);

            // 3. 发送消息
            const sendResponse = await fetch('http://localhost:5000/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ who: sessionId, message: replyContent })
            });

            const sendData = await sendResponse.json();
            console.log(`[AutoReply] 发送响应:`, sendData);

            if (sendData.status !== 'success') {
                throw new Error(sendData.message || '发送失败');
            }

            console.log(`[AutoReply] 自动回复发送成功: ${sessionId}`);
            showToast(`已自动回复 ${sessionId}`, 'success');

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '未知错误';
            console.error(`[AutoReply] 自动回复失败:`, errorMessage);
            showToast(`自动回复失败: ${errorMessage}`, 'error');
        }
    }, [showToast]);

    // 同步 triggerAutoReply 到 ref
    useEffect(() => {
        triggerAutoReplyRef.current = triggerAutoReply;
    }, [triggerAutoReply]);

    // SSE 连接函数 - 不依赖 triggerAutoReply，使用 ref 调用
    const connectSSE = useCallback(() => {
        if (eventSourceRef.current) eventSourceRef.current.close();
        if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);

        setIsRetrying(true);
        const es = new EventSource('http://127.0.0.1:5000/api/messages/stream');
        eventSourceRef.current = es;
        lastHeartbeatRef.current = Date.now();

        // 心跳监控
        const monitorInterval = setInterval(() => {
            const now = Date.now();
            if (now - lastHeartbeatRef.current > 30000) {
                console.warn("[SSE Global] Watchdog detected zombie connection, reconnecting...");
                setIsConnected(false);
                setIsRetrying(true);
                es.close();
                clearInterval(monitorInterval);
                setTimeout(connectSSE, 2000);
            }
        }, 10000);
        heartbeatTimerRef.current = monitorInterval;

        es.onopen = () => {
            console.log("[SSE Global] Connected to backend message stream");
            setIsConnected(true);
            setIsRetrying(false);
            lastHeartbeatRef.current = Date.now();
        };

        es.onmessage = (event) => {
            lastHeartbeatRef.current = Date.now();

            try {
                if (!event.data) return;
                const data = JSON.parse(event.data);

                // 心跳包
                if (data.type === 'heartbeat' || !data.session) {
                    return;
                }

                // 调试日志：查看接收到的消息
                console.log("[SSE Global] 收到消息:", {
                    session: data.session,
                    sender: data.sender,
                    content: data.content?.substring(0, 20),
                    is_self: data.is_self,
                    unread: data.unread
                });

                const msg: Message = data;
                const sid = msg.session;

                setSessions(prev => {
                    const existing = prev[sid] || {
                        id: sid,
                        lastMessage: '',
                        lastTime: '',
                        unreadCount: 0,
                        messages: []
                    };

                    return {
                        ...prev,
                        [sid]: {
                            ...existing,
                            lastMessage: msg.content,
                            lastTime: msg.time,
                            unreadCount: msg.is_self ? 0 : (existing.unreadCount + 1),
                            messages: [...existing.messages, msg].slice(-100)
                        }
                    };
                });

                // 🔧 自动回复逻辑：收到对方消息时触发防抖计时器
                if (!msg.is_self && autoReplyConfigRef.current.enabled) {
                    const debounceMs = (autoReplyConfigRef.current.debounceSeconds || 5) * 1000;
                    console.log(`[AutoReply] 收到 ${sid} 的消息，启动 ${autoReplyConfigRef.current.debounceSeconds || 5} 秒防抖计时器`);

                    // 清除该会话之前的计时器
                    const existingTimer = autoReplyTimersRef.current.get(sid);
                    if (existingTimer) {
                        clearTimeout(existingTimer);
                        console.log(`[AutoReply] 清除 ${sid} 的旧计时器`);
                    }

                    // 设置新的计时器，使用 ref 调用最新的函数
                    const timer = setTimeout(() => {
                        console.log(`[AutoReply] ${sid} ${autoReplyConfigRef.current.debounceSeconds || 5} 秒内无新消息，触发自动回复`);
                        triggerAutoReplyRef.current?.(sid);
                        autoReplyTimersRef.current.delete(sid);
                    }, debounceMs);

                    autoReplyTimersRef.current.set(sid, timer);
                }
            } catch (e) {
                // 忽略解析错误
            }
        };

        es.onerror = () => {
            console.error("[SSE Global] Connection error");
            setIsConnected(false);
            setIsRetrying(true);
            es.close();
            clearInterval(monitorInterval);
            setTimeout(connectSSE, 5000);
        };
    }, []); // 移除 triggerAutoReply 依赖，使用 ref 代替

    // 初始化 SSE 连接
    useEffect(() => {
        connectSSE();
        return () => {
            eventSourceRef.current?.close();
            if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
            // 清理所有自动回复计时器
            autoReplyTimersRef.current.forEach(timer => clearTimeout(timer));
            autoReplyTimersRef.current.clear();
        };
    }, [connectSSE]);

    // 删除会话
    const deleteSession = useCallback(async (sessionId: string) => {
        try {
            const response = await fetch(`http://localhost:5000/api/ai/context/session/${encodeURIComponent(sessionId)}`, {
                method: 'DELETE'
            });
            const data = await response.json();

            if (data.success) {
                setSessions(prev => {
                    const newSessions = { ...prev };
                    delete newSessions[sessionId];
                    return newSessions;
                });

                if (activeSessionId === sessionId) {
                    setActiveSessionId(null);
                }
            } else {
                throw new Error(data.error || '删除失败');
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
            throw error;
        }
    }, [activeSessionId]);

    // 删除单条消息
    const deleteMessage = useCallback((sessionId: string, messageIndex: number) => {
        setSessions(prev => {
            const session = prev[sessionId];
            if (!session) return prev;

            const newMessages = session.messages.filter((_, idx) => idx !== messageIndex);

            return {
                ...prev,
                [sessionId]: {
                    ...session,
                    messages: newMessages,
                    lastMessage: newMessages.length > 0 ? newMessages[newMessages.length - 1].content : '',
                    lastTime: newMessages.length > 0 ? newMessages[newMessages.length - 1].time : ''
                }
            };
        });
    }, []);

    // 清除未读数
    const clearUnread = useCallback((sessionId: string) => {
        setSessions(prev => {
            const session = prev[sessionId];
            if (!session) return prev;
            return {
                ...prev,
                [sessionId]: { ...session, unreadCount: 0 }
            };
        });
    }, []);

    const value: MessageContextType = {
        sessions,
        setSessions,
        activeSessionId,
        setActiveSessionId,
        isConnected,
        isRetrying,
        deleteSession,
        deleteMessage,
        clearUnread,
        // 自动回复相关
        autoReplyConfig,
        setAutoReplyConfig,
        toasts,
        closeToast
    };

    return (
        <MessageContext.Provider value={value}>
            {children}
        </MessageContext.Provider>
    );
}

// Hook 用于访问消息上下文
export function useMessages() {
    const context = useContext(MessageContext);
    if (!context) {
        throw new Error('useMessages must be used within a MessageProvider');
    }
    return context;
}

