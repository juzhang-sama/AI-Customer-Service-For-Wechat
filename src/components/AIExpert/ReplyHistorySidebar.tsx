import React, { useState, useEffect } from 'react';
import { History, MessageSquare, User, Bot, ChevronRight, Calendar, ExternalLink } from 'lucide-react';

interface HistoryItem {
    id: number;
    session_id: string;
    customer_message: string;
    suggestion_aggressive: string;
    suggestion_conservative: string;
    suggestion_professional: string;
    selected_type: string;
    edited_content: string;
    created_at: string;
}

interface ReplyHistorySidebarProps {
    currentSession: string;
    onSelectHistoricalReply?: (content: string) => void;
}

const ReplyHistorySidebar: React.FC<ReplyHistorySidebarProps> = ({ currentSession, onSelectHistoricalReply }) => {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [expandedId, setExpandedId] = useState<number | null>(null);

    const fetchHistory = async () => {
        if (!currentSession) return;
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:5000/api/ai/history/${encodeURIComponent(currentSession)}?limit=10`);
            const data = await response.json();
            if (data.success) {
                setHistory(data.history);
            }
        } catch (error) {
            console.error('Failed to fetch history:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [currentSession]);

    if (!currentSession) return null;

    return (
        <div className="flex flex-col h-full bg-white/60 backdrop-blur-xl border-l border-white/20">
            <div className="p-4 border-b border-white/20 bg-white/40 flex items-center justify-between">
                <h3 className="font-bold text-gray-800 flex items-center text-sm">
                    <History className="w-4 h-4 mr-2 text-blue-600" />
                    历史建议记录
                </h3>
                <button
                    onClick={fetchHistory}
                    className="text-[10px] text-blue-600 hover:underline font-medium"
                >
                    刷新
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {loading ? (
                    <div className="flex justify-center py-10">
                        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : history.length === 0 ? (
                    <div className="text-center py-10 text-gray-400 text-xs">
                        暂无历史建议记录
                    </div>
                ) : (
                    history.map((item) => (
                        <div
                            key={item.id}
                            className={`rounded-xl border transition-all overflow-hidden ${expandedId === item.id ? 'border-blue-200 bg-white/80 shadow-sm' : 'border-white/40 bg-white/30 hover:bg-white/50'
                                }`}
                        >
                            <button
                                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                                className="w-full p-3 text-left space-y-2"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-1 text-[10px] text-gray-400">
                                        <Calendar className="w-3 h-3" />
                                        <span>{new Date(item.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
                                    </div>
                                    <ChevronRight className={`w-3 h-3 text-gray-400 transition-transform ${expandedId === item.id ? 'rotate-90' : ''}`} />
                                </div>
                                <div className="line-clamp-2 text-xs text-gray-700 font-medium">
                                    {item.customer_message}
                                </div>
                            </button>

                            {expandedId === item.id && (
                                <div className="px-3 pb-3 pt-1 border-t border-blue-50/50 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
                                    <div className="space-y-1.5">
                                        <div className="flex items-center space-x-1.5 text-[10px] font-bold text-blue-600">
                                            <Bot className="w-3 h-3" />
                                            <span>最终采用回复：</span>
                                        </div>
                                        <div className="p-2 bg-blue-50/50 rounded-lg text-xs text-gray-800 leading-relaxed border border-blue-100/50">
                                            {item.edited_content || (item.selected_type === 'aggressive' ? item.suggestion_aggressive :
                                                item.selected_type === 'professional' ? item.suggestion_professional :
                                                    item.suggestion_conservative)}
                                        </div>
                                    </div>

                                    {onSelectHistoricalReply && (
                                        <button
                                            onClick={() => onSelectHistoricalReply(item.edited_content || item.suggestion_professional)}
                                            className="w-full py-1.5 text-[10px] font-bold text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-600 hover:text-white transition-all flex items-center justify-center space-x-1"
                                        >
                                            <ExternalLink className="w-3 h-3" />
                                            <span>复用此话术</span>
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ReplyHistorySidebar;
