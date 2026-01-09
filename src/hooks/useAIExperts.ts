/**
 * useAIExperts - AI 专家数据 Hook
 * 带缓存的 AI 专家列表获取
 */

import { useDataCache } from './useDataCache';
import { API_BASE_URL } from '../services/api';

export interface AIExpert {
    id: number;
    name: string;
    role_definition: string;
    business_logic: string;
    tone_style: string;
    reply_length: string;
    emoji_usage: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

interface AIExpertsResponse {
    success: boolean;
    prompts: AIExpert[];
}

/**
 * 获取 AI 专家列表（带缓存）
 * @param ttl 缓存过期时间（毫秒），默认 2 分钟
 */
export function useAIExperts(ttl = 2 * 60 * 1000) {
    const { data, isLoading, error, refresh, isStale } = useDataCache<AIExpertsResponse>({
        cacheKey: 'ai-experts-list',
        ttl,
        revalidateOnFocus: true,
        fetcher: async () => {
            const response = await fetch(`${API_BASE_URL}/api/ai/prompts`);
            if (!response.ok) {
                throw new Error(`Failed to fetch AI experts: ${response.statusText}`);
            }
            return response.json();
        },
    });

    return {
        experts: data?.prompts || [],
        isLoading,
        error,
        refresh,
        isStale,
    };
}

/**
 * 获取当前激活的 AI 专家
 */
export function useActiveExpert() {
    const { experts, isLoading, error } = useAIExperts();
    const activeExpert = experts.find(e => e.is_active) || null;
    
    return {
        activeExpert,
        isLoading,
        error,
    };
}

