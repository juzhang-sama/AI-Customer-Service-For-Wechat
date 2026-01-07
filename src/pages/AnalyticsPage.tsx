import React, { useState, useEffect } from 'react';
import { BarChart2, TrendingUp, Zap, MessageSquare, DollarSign, Loader2, ArrowUpRight, Activity, Sparkles } from 'lucide-react';

interface AnalyticsData {
    overview: {
        total_messages: number;
        sent_messages: number;
        reply_rate: number;
        total_tokens: number;
        total_cost: number;
        total_prompts: number;
    };
    trends: Array<{
        date: string;
        total: number;
        sent: number;
    }>;
    keywords: Array<{
        word: string;
        count: number;
    }>;
    efficiency: {
        adoption_rate: number;
        edit_rate: number;
    };
    insights?: string;
}

const AnalyticsPage: React.FC = () => {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAnalytics = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/ai/analytics/dashboard');
            const result = await response.json();
            if (result.success) {
                setData(result.data);
            } else {
                setError(result.error || '获取数据失败');
            }
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
            setError('网络连接异常，请检查后端服务是否启动');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
                <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
                <p className="text-gray-500 font-medium">深度解析业务数据中...</p>
                <p className="text-xs text-gray-400">正在调用 AI 分析最近 50 条消息，可能需要 10-15 秒</p>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
                <div className="p-4 bg-red-50 text-red-600 rounded-2xl border border-red-100 max-w-md text-center">
                    <p className="font-bold mb-2">出错了</p>
                    <p className="text-sm">{error || '未能加载分析数据'}</p>
                </div>
                <button
                    onClick={fetchAnalytics}
                    className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg"
                >
                    <TrendingUp className="w-4 h-4" />
                    重试加载
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* AI 经营洞察快报 */}
            {data.insights && (
                <div className="bg-gradient-to-r from-blue-600/90 to-purple-600/90 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-150 transition-transform duration-1000">
                        <Sparkles className="w-32 h-32 text-white" />
                    </div>
                    <div className="relative z-10">
                        <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-blue-200" />
                            AI 智能经营洞察
                        </h3>
                        <div className="text-blue-50 leading-relaxed text-sm whitespace-pre-wrap">
                            {data.insights}
                        </div>
                    </div>
                    <div className="absolute bottom-0 left-0 h-1 bg-white/30 animate-pulse" style={{ width: '100%' }}></div>
                </div>
            )}

            {/* 顶层核心指标 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="累计处理消息"
                    value={data.overview.total_messages}
                    icon={<MessageSquare className="text-blue-500" />}
                    trend="+12%"
                    color="blue"
                />
                <StatCard
                    title="成功回复率"
                    value={`${data.overview.reply_rate}%`}
                    icon={<Zap className="text-amber-500" />}
                    trend="稳步提升"
                    color="amber"
                />
                <StatCard
                    title="AI 采纳率"
                    value={`${data.efficiency.adoption_rate}%`}
                    icon={<Activity className="text-green-500" />}
                    trend="高效率"
                    color="green"
                />
                <StatCard
                    title="预估节省成本"
                    value={`¥${data.overview.total_cost}`}
                    icon={<DollarSign className="text-purple-500" />}
                    trend={`用量: ${data.overview.total_tokens}`}
                    color="purple"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* 趋势图表区 (原生 SVG 模拟) */}
                <div className="lg:col-span-2 bg-white/40 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <TrendingUp className="w-6 h-6 text-blue-500" />
                            业务增长趋势
                        </h3>
                        <div className="flex gap-4 text-xs font-medium text-gray-500">
                            <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500"></span> 接收消息</div>
                            <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-green-500"></span> 成功回复</div>
                        </div>
                    </div>

                    <div className="h-64 flex items-end justify-between gap-2 px-2">
                        {data.trends.map((item, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center group relative">
                                <div className="w-full flex justify-center gap-1">
                                    <div
                                        style={{ height: `${Math.min(item.total * 3, 200)}px` }}
                                        className="w-4 bg-blue-400/30 rounded-t-lg transition-all group-hover:bg-blue-400 group-hover:scale-x-110"
                                    />
                                    <div
                                        style={{ height: `${Math.min(item.sent * 3, 200)}px` }}
                                        className="w-4 bg-green-500/30 rounded-t-lg transition-all group-hover:bg-green-500 group-hover:scale-x-110"
                                    />
                                </div>
                                <span className="text-[10px] text-gray-400 mt-3 rotate-45 origin-left">{item.date.split('-').slice(1).join('/')}</span>

                                {/* Hover Tooltip */}
                                <div className="absolute bottom-full mb-4 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-900 text-white text-[10px] p-2 rounded-lg z-20 pointer-events-none shadow-2xl">
                                    <p>总数: {item.total}</p>
                                    <p>回复: {item.sent}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 词云/热点区 */}
                <div className="bg-white/40 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-xl">
                    <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2 mb-8">
                        <BarChart2 className="w-6 h-6 text-purple-500" />
                        客户关注焦点
                    </h3>
                    <div className="flex flex-wrap gap-3">
                        {data.keywords.map((kw, i) => (
                            <div
                                key={i}
                                style={{ fontSize: `${Math.max(12, 12 + kw.count * 2)}px` }}
                                className={`px-4 py-1.5 rounded-2xl font-medium transition-all hover:scale-110 cursor-default ${i % 3 === 0 ? 'bg-blue-100 text-blue-700' :
                                    i % 3 === 1 ? 'bg-purple-100 text-purple-700' :
                                        'bg-amber-100 text-amber-700'
                                    }`}
                            >
                                {kw.word}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard: React.FC<{ title: string; value: string | number; icon: React.ReactNode; trend: string; color: string }> = ({ title, value, icon, trend, color }) => (
    <div className="bg-white/40 backdrop-blur-lg border border-white/20 rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl bg-${color}-50 group-hover:scale-110 transition-transform`}>
                {icon}
            </div>
            <div className="flex items-center text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                <ArrowUpRight className="w-3 h-3 mr-0.5" />
                {trend}
            </div>
        </div>
        <div>
            <p className="text-xs text-gray-500 font-medium mb-1 uppercase tracking-wider">{title}</p>
            <p className="text-3xl font-black text-gray-800">{value}</p>
        </div>
    </div>
);

export default AnalyticsPage;
