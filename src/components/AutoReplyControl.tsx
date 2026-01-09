import React, { useEffect, useState } from 'react';
import { Bot, Zap, Clock, User } from 'lucide-react';

export type ReplyStyle = 'aggressive' | 'conservative' | 'professional';

export interface AutoReplyConfig {
    enabled: boolean;
    replyStyle: ReplyStyle;
    selectedExpertId: number | null;
    debounceSeconds: number;
}

interface AIExpert {
    id: number;
    name: string;
    is_active: number;
}

interface AutoReplyControlProps {
    config: AutoReplyConfig;
    onChange: (config: AutoReplyConfig) => void;
}

const styleOptions: { value: ReplyStyle; label: string; description: string }[] = [
    { value: 'aggressive', label: '进取型', description: '积极主动，推动成交' },
    { value: 'conservative', label: '保守型', description: '稳妥谨慎，降低风险' },
    { value: 'professional', label: '专业型', description: '专业客观，建立信任' },
];

const debounceOptions = [
    { value: 3, label: '3秒' },
    { value: 5, label: '5秒' },
    { value: 8, label: '8秒' },
    { value: 10, label: '10秒' },
];

export const AutoReplyControl: React.FC<AutoReplyControlProps> = ({ config, onChange }) => {
    const [aiExperts, setAiExperts] = useState<AIExpert[]>([]);

    // 加载 AI 专家列表
    useEffect(() => {
        const fetchExperts = async () => {
            try {
                const response = await fetch('http://localhost:5000/api/ai/prompts');
                const data = await response.json();
                if (data.success && Array.isArray(data.prompts)) {
                    setAiExperts(data.prompts);
                    // 如果没有选择专家，默认选择激活的或第一个
                    if (!config.selectedExpertId && data.prompts.length > 0) {
                        const activeExpert = data.prompts.find((e: AIExpert) => e.is_active === 1);
                        onChange({
                            ...config,
                            selectedExpertId: activeExpert ? activeExpert.id : data.prompts[0].id
                        });
                    }
                }
            } catch (error) {
                console.error('Failed to load AI experts:', error);
            }
        };
        fetchExperts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleToggle = (enabled: boolean) => {
        onChange({ ...config, enabled });
    };

    const handleStyleChange = (replyStyle: ReplyStyle) => {
        onChange({ ...config, replyStyle });
    };

    const handleExpertChange = (expertId: number | null) => {
        onChange({ ...config, selectedExpertId: expertId });
    };

    const handleDebounceChange = (seconds: number) => {
        onChange({ ...config, debounceSeconds: seconds });
    };

    const selectedExpert = aiExperts.find(e => e.id === config.selectedExpertId);

    // 获取当前风格的标签
    const currentStyleLabel = styleOptions.find(s => s.value === config.replyStyle)?.label || '专业型';

    return (
        <div className="bg-gradient-to-r from-purple-50/80 to-blue-50/80 rounded-xl border border-purple-100/50 px-4 py-2.5">
            {/* 单行紧凑布局 */}
            <div className="flex items-center justify-between gap-4">
                {/* 左侧：标题和状态 */}
                <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1.5">
                        <Bot className={`w-4 h-4 ${config.enabled ? 'text-green-500' : 'text-gray-400'}`} />
                        <span className="text-sm font-semibold text-gray-700">自动回复</span>
                    </div>

                    {/* 模式切换 */}
                    <div className="flex bg-white rounded-md p-0.5 shadow-sm border border-gray-200">
                        <button
                            onClick={() => handleToggle(false)}
                            className={`px-2 py-1 text-[11px] font-medium rounded transition-all ${
                                !config.enabled
                                    ? 'bg-gray-700 text-white'
                                    : 'text-gray-400 hover:text-gray-600'
                            }`}
                        >
                            手动
                        </button>
                        <button
                            onClick={() => handleToggle(true)}
                            className={`px-2 py-1 text-[11px] font-medium rounded transition-all ${
                                config.enabled
                                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                                    : 'text-gray-400 hover:text-gray-600'
                            }`}
                        >
                            自动
                        </button>
                    </div>
                </div>

                {/* 右侧：配置选项（仅自动模式显示） */}
                {config.enabled && (
                    <div className="flex items-center gap-3">
                        {/* AI 专家 */}
                        <div className="flex items-center gap-1.5">
                            <User className="w-3 h-3 text-gray-400" />
                            <select
                                value={config.selectedExpertId || ''}
                                onChange={(e) => handleExpertChange(e.target.value ? Number(e.target.value) : null)}
                                className="px-2 py-1 bg-white border border-gray-200 rounded-md text-xs focus:ring-1 focus:ring-purple-400 outline-none min-w-[100px]"
                            >
                                {aiExperts.map((expert) => (
                                    <option key={expert.id} value={expert.id}>
                                        {expert.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* 回复风格 */}
                        <div className="flex items-center gap-1.5">
                            <Zap className="w-3 h-3 text-gray-400" />
                            <select
                                value={config.replyStyle}
                                onChange={(e) => handleStyleChange(e.target.value as ReplyStyle)}
                                className="px-2 py-1 bg-white border border-gray-200 rounded-md text-xs focus:ring-1 focus:ring-purple-400 outline-none"
                            >
                                {styleOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* 等待时间 */}
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-3 h-3 text-gray-400" />
                            <select
                                value={config.debounceSeconds || 5}
                                onChange={(e) => handleDebounceChange(Number(e.target.value))}
                                className="px-2 py-1 bg-white border border-gray-200 rounded-md text-xs focus:ring-1 focus:ring-purple-400 outline-none"
                            >
                                {debounceOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                )}

                {/* 手动模式时显示简要信息 */}
                {!config.enabled && (
                    <span className="text-xs text-gray-400">开启后自动处理客户消息</span>
                )}
            </div>
        </div>
    );
};

export default AutoReplyControl;

