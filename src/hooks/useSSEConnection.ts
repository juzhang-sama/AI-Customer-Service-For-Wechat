/**
 * useSSEConnection - SSE 连接管理 Hook
 * 支持指数退避重连策略
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import {
    SSE_HEARTBEAT_TIMEOUT,
    SSE_RECONNECT_INITIAL,
    SSE_RECONNECT_MAX,
    SSE_MAX_RETRIES
} from '../utils/constants';

interface SSEOptions {
    url: string;
    onMessage: (data: unknown) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    maxRetries?: number;
    initialRetryDelay?: number;
    maxRetryDelay?: number;
    heartbeatTimeout?: number;
}

interface SSEState {
    isConnected: boolean;
    isRetrying: boolean;
    retryCount: number;
    lastError: string | null;
}

export function useSSEConnection(options: SSEOptions) {
    const {
        url,
        onMessage,
        onConnect,
        onDisconnect,
        maxRetries = SSE_MAX_RETRIES,
        initialRetryDelay = SSE_RECONNECT_INITIAL,
        maxRetryDelay = SSE_RECONNECT_MAX,
        heartbeatTimeout = SSE_HEARTBEAT_TIMEOUT,
    } = options;

    const [state, setState] = useState<SSEState>({
        isConnected: false,
        isRetrying: true,
        retryCount: 0,
        lastError: null,
    });

    const eventSourceRef = useRef<EventSource | null>(null);
    const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
    const lastHeartbeatRef = useRef<number>(Date.now());
    const retryCountRef = useRef<number>(0);
    const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // 计算指数退避延迟
    const getRetryDelay = useCallback((retryCount: number): number => {
        // 指数退避: delay = min(initialDelay * 2^retryCount, maxDelay)
        const delay = Math.min(
            initialRetryDelay * Math.pow(2, retryCount),
            maxRetryDelay
        );
        // 添加随机抖动 (±20%)
        const jitter = delay * 0.2 * (Math.random() - 0.5);
        return Math.floor(delay + jitter);
    }, [initialRetryDelay, maxRetryDelay]);

    // 连接 SSE
    const connect = useCallback(() => {
        // 清理现有连接
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }
        if (heartbeatTimerRef.current) {
            clearInterval(heartbeatTimerRef.current);
        }
        if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
        }

        setState(prev => ({ ...prev, isRetrying: true }));

        const es = new EventSource(url);
        eventSourceRef.current = es;
        lastHeartbeatRef.current = Date.now();

        // 心跳监控
        const monitorInterval = setInterval(() => {
            const now = Date.now();
            if (now - lastHeartbeatRef.current > heartbeatTimeout) {
                console.warn('[SSE] Heartbeat timeout, reconnecting...');
                es.close();
                clearInterval(monitorInterval);
                scheduleRetry();
            }
        }, 10000);
        heartbeatTimerRef.current = monitorInterval;

        es.onopen = () => {
            console.log('[SSE] Connected');
            retryCountRef.current = 0; // 重置重试计数
            setState({
                isConnected: true,
                isRetrying: false,
                retryCount: 0,
                lastError: null,
            });
            lastHeartbeatRef.current = Date.now();
            onConnect?.();
        };

        es.onmessage = (event) => {
            lastHeartbeatRef.current = Date.now();
            
            try {
                if (!event.data) return;
                const data = JSON.parse(event.data);
                
                // 心跳包只更新时间，不传递给回调
                if (data.type === 'heartbeat') {
                    console.log('[SSE] Heartbeat received');
                    return;
                }
                
                onMessage(data);
            } catch (e) {
                // 忽略解析错误
            }
        };

        es.onerror = () => {
            console.error('[SSE] Connection error');
            es.close();
            clearInterval(monitorInterval);
            scheduleRetry();
        };
    }, [url, onMessage, onConnect, heartbeatTimeout]);

    // 安排重试
    const scheduleRetry = useCallback(() => {
        if (retryCountRef.current >= maxRetries) {
            console.error('[SSE] Max retries reached');
            setState(prev => ({
                ...prev,
                isConnected: false,
                isRetrying: false,
                lastError: '连接失败，已达最大重试次数',
            }));
            onDisconnect?.();
            return;
        }

        const delay = getRetryDelay(retryCountRef.current);
        console.log(`[SSE] Retry #${retryCountRef.current + 1} in ${delay}ms`);
        
        setState(prev => ({
            ...prev,
            isConnected: false,
            isRetrying: true,
            retryCount: retryCountRef.current,
        }));

        retryTimeoutRef.current = setTimeout(() => {
            retryCountRef.current++;
            connect();
        }, delay);
    }, [maxRetries, getRetryDelay, connect, onDisconnect]);

    // 手动重连
    const reconnect = useCallback(() => {
        retryCountRef.current = 0;
        connect();
    }, [connect]);

    // 初始化连接
    useEffect(() => {
        connect();
        
        return () => {
            eventSourceRef.current?.close();
            if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
            if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        };
    }, [connect]);

    return {
        ...state,
        reconnect,
    };
}

