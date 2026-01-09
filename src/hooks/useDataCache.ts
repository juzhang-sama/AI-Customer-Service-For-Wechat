/**
 * useDataCache - 简单的数据缓存 Hook
 * 支持过期时间和手动刷新
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { CACHE_TTL_MEDIUM } from '../utils/constants';

interface CacheOptions<T> {
    /** 获取数据的函数 */
    fetcher: () => Promise<T>;
    /** 缓存键 */
    cacheKey: string;
    /** 缓存过期时间（毫秒），默认 5 分钟 */
    ttl?: number;
    /** 是否在窗口获得焦点时重新验证 */
    revalidateOnFocus?: boolean;
    /** 初始数据 */
    initialData?: T;
}

interface CacheState<T> {
    data: T | undefined;
    isLoading: boolean;
    error: Error | null;
    lastUpdated: number | null;
}

// 全局缓存存储
const globalCache = new Map<string, { data: unknown; timestamp: number }>();

export function useDataCache<T>(options: CacheOptions<T>) {
    const {
        fetcher,
        cacheKey,
        ttl = CACHE_TTL_MEDIUM,
        revalidateOnFocus = false,
        initialData,
    } = options;

    const [state, setState] = useState<CacheState<T>>(() => {
        // 尝试从缓存获取初始数据
        const cached = globalCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < ttl) {
            return {
                data: cached.data as T,
                isLoading: false,
                error: null,
                lastUpdated: cached.timestamp,
            };
        }
        return {
            data: initialData,
            isLoading: true,
            error: null,
            lastUpdated: null,
        };
    });

    const isMountedRef = useRef(true);

    // 获取数据
    const fetchData = useCallback(async (force = false) => {
        // 检查缓存是否有效
        if (!force) {
            const cached = globalCache.get(cacheKey);
            if (cached && Date.now() - cached.timestamp < ttl) {
                setState({
                    data: cached.data as T,
                    isLoading: false,
                    error: null,
                    lastUpdated: cached.timestamp,
                });
                return;
            }
        }

        setState(prev => ({ ...prev, isLoading: true, error: null }));

        try {
            const data = await fetcher();
            const timestamp = Date.now();
            
            // 更新全局缓存
            globalCache.set(cacheKey, { data, timestamp });
            
            if (isMountedRef.current) {
                setState({
                    data,
                    isLoading: false,
                    error: null,
                    lastUpdated: timestamp,
                });
            }
        } catch (err) {
            if (isMountedRef.current) {
                setState(prev => ({
                    ...prev,
                    isLoading: false,
                    error: err instanceof Error ? err : new Error(String(err)),
                }));
            }
        }
    }, [cacheKey, fetcher, ttl]);

    // 强制刷新
    const refresh = useCallback(() => fetchData(true), [fetchData]);

    // 初始加载
    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // 窗口焦点重新验证
    useEffect(() => {
        if (!revalidateOnFocus) return;

        const handleFocus = () => {
            const cached = globalCache.get(cacheKey);
            if (!cached || Date.now() - cached.timestamp > ttl) {
                fetchData();
            }
        };

        window.addEventListener('focus', handleFocus);
        return () => window.removeEventListener('focus', handleFocus);
    }, [cacheKey, fetchData, revalidateOnFocus, ttl]);

    // 清理
    useEffect(() => {
        isMountedRef.current = true;
        return () => {
            isMountedRef.current = false;
        };
    }, []);

    return {
        ...state,
        refresh,
        isStale: state.lastUpdated ? Date.now() - state.lastUpdated > ttl : true,
    };
}

// 清除特定缓存
export function clearCache(cacheKey: string) {
    globalCache.delete(cacheKey);
}

// 清除所有缓存
export function clearAllCache() {
    globalCache.clear();
}

