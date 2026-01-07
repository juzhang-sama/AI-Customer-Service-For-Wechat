import React, { useState, useEffect } from 'react';
import { Sparkles, Send, Loader2, AlertCircle, Check, Users, RefreshCw, Zap } from 'lucide-react';

interface KanbanTask {
    id: number;
    session_id: string;
    customer_name: string;
    raw_message: string;
    ai_reply_options?: {
        professional?: string;
        conservative?: string;
        aggressive?: string;
    };
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'SENT' | 'FAILED';
    error_msg?: string;
    created_at: string;
}

const BatchProcessingKanban: React.FC = () => {
    const [tasks, setTasks] = useState<KanbanTask[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<number | null>(null);
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [isBulkSending, setIsBulkSending] = useState(false);

    const fetchTasks = async () => {
        try {
            const response = await fetch('/api/ai/tasks/kanban');
            const data = await response.json();
            if (data.success) {
                setTasks(data.tasks);
            }
        } catch (error) {
            console.error('Failed to fetch kanban tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000); // 5秒轮询一次
        return () => clearInterval(interval);
    }, []);

    const handleSend = async (task: KanbanTask) => {
        if (!task.ai_reply_options?.professional) return;

        setProcessingId(task.id);
        try {
            const response = await fetch('/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    who: task.customer_name || task.session_id,
                    message: task.ai_reply_options.professional
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                // 更新后端状态
                await fetch(`/api/ai/tasks/${task.id}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'SENT' })
                });
                fetchTasks();
            } else {
                alert('发送失败: ' + result.message);
            }
        } catch (error) {
            alert('发送出错: ' + error);
        } finally {
            setProcessingId(null);
        }
    };

    const handleBatchSend = async () => {
        const tasksToSend = tasks.filter(t => selectedIds.includes(t.id) && t.status === 'COMPLETED');
        if (tasksToSend.length === 0) return;

        if (!confirm(`确认要批量发送这 ${tasksToSend.length} 条回复吗？`)) return;

        setIsBulkSending(true);
        for (const task of tasksToSend) {
            setProcessingId(task.id);
            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        who: task.customer_name || task.session_id,
                        message: task.ai_reply_options!.professional
                    })
                });
                const result = await response.json();
                if (result.status === 'success') {
                    await fetch(`/api/ai/tasks/${task.id}/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'SENT' })
                    });
                }
            } catch (error) {
                console.error(`Failed to send task ${task.id}:`, error);
            }
        }
        setIsBulkSending(false);
        setProcessingId(null);
        setSelectedIds([]);
        fetchTasks();
    };

    const toggleSelectAll = () => {
        const readyIds = tasks.filter(t => t.status === 'COMPLETED').map(t => t.id);
        if (selectedIds.length === readyIds.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(readyIds);
        }
    };

    const toggleSelect = (id: number) => {
        setSelectedIds(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const triggerBulkGenerate = async () => {
        setLoading(true);
        try {
            await fetch('/api/ai/tasks/bulk-generate', { method: 'POST', body: JSON.stringify({}) });
            fetchTasks();
        } catch (error) {
            console.error('Bulk generation failed:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading && tasks.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                <p className="text-gray-500">正在加载待处理任务...</p>
            </div>
        );
    }

    const pendingTasks = tasks.filter(t => t.status === 'PENDING');
    const readyTasks = tasks.filter(t => t.status === 'COMPLETED');
    const selectedCount = selectedIds.length;

    return (
        <div className="space-y-6 pb-24">
            {/* 顶部统计与操作 */}
            <div className="flex items-center justify-between bg-white/40 backdrop-blur-lg p-6 rounded-2xl border border-white/20 shadow-xl">
                <div className="flex items-center space-x-8">
                    <div className="flex items-center space-x-3">
                        <input
                            type="checkbox"
                            disabled={readyTasks.length === 0}
                            checked={readyTasks.length > 0 && selectedIds.length === readyTasks.length}
                            onChange={toggleSelectAll}
                            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        />
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">待回复客户</p>
                            <p className="text-2xl font-bold text-gray-800">{tasks.length}</p>
                        </div>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">建议就绪</p>
                        <p className="text-2xl font-bold text-green-600">{readyTasks.length}</p>
                    </div>
                </div>

                <div className="flex space-x-3">
                    <button
                        onClick={triggerBulkGenerate}
                        disabled={pendingTasks.length === 0 || loading}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all ${pendingTasks.length > 0 && !loading
                            ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/30'
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            }`}
                    >
                        {loading && pendingTasks.length > 0 ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Sparkles className="w-4 h-4" />
                        )}
                        <span>智能预生成 ({pendingTasks.length})</span>
                    </button>

                    <button
                        onClick={fetchTasks}
                        className="p-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-gray-600 transition-colors"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* 看板网格 */}
            {tasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 bg-white/20 rounded-2xl border border-dashed border-gray-300">
                    <Users className="w-12 h-12 text-gray-300 mb-4" />
                    <p className="text-gray-400">目前暂无待回复消息</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {tasks.map((task) => (
                        <div
                            key={task.id}
                            className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 hover:shadow-2xl ${task.status === 'COMPLETED'
                                ? selectedIds.includes(task.id)
                                    ? 'bg-blue-50/50 border-blue-400 ring-2 ring-blue-400/20'
                                    : 'bg-white/80 border-green-200 hover:-translate-y-1'
                                : 'bg-white/40 border-white/20'
                                } backdrop-blur-md`}
                        >
                            {/* 选择复选框 */}
                            {task.status === 'COMPLETED' && (
                                <div className="absolute top-4 left-4 z-10">
                                    <input
                                        type="checkbox"
                                        checked={selectedIds.includes(task.id)}
                                        onChange={() => toggleSelect(task.id)}
                                        className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer shadow-sm"
                                    />
                                </div>
                            )}

                            <div className="p-5 space-y-4 pt-10">
                                {/* 头部：客户信息 */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-100 to-purple-100 flex items-center justify-center text-blue-600 font-bold">
                                            {task.customer_name?.[0] || '?'}
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-gray-800">{task.customer_name || '未知客户'}</h4>
                                            <p className="text-[10px] text-gray-400">{new Date(task.created_at).toLocaleTimeString()}</p>
                                        </div>
                                    </div>
                                    <div className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${task.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                                        task.status === 'PROCESSING' ? 'bg-blue-100 text-blue-700' :
                                            task.status === 'FAILED' ? 'bg-red-100 text-red-700' :
                                                task.status === 'SENT' ? 'bg-gray-100 text-gray-500' :
                                                    'bg-gray-100 text-gray-500'
                                        }`}>
                                        {task.status === 'COMPLETED' ? '已就绪' :
                                            task.status === 'PROCESSING' ? '生成中...' :
                                                task.status === 'FAILED' ? '生成失败' :
                                                    task.status === 'SENT' ? '已发送' : '排队中'}
                                    </div>
                                </div>

                                {/* 原始消息 */}
                                <div className="bg-gray-50/50 p-3 rounded-xl border border-gray-100/50">
                                    <p className="text-sm text-gray-600 line-clamp-2 italic">
                                        "{task.raw_message}"
                                    </p>
                                </div>

                                {/* AI 建议预览 */}
                                {task.ai_reply_options?.professional ? (
                                    <div className="space-y-2">
                                        <div className="flex items-center space-x-1 text-[10px] font-bold text-blue-500 uppercase tracking-widest">
                                            <Zap className="w-3 h-3" />
                                            <span>推荐回复</span>
                                        </div>
                                        <p className="text-sm text-gray-800 leading-relaxed line-clamp-3">
                                            {task.ai_reply_options.professional}
                                        </p>
                                    </div>
                                ) : task.status === 'FAILED' ? (
                                    <div className="flex items-center space-x-2 text-red-500 text-xs">
                                        <AlertCircle className="w-4 h-4" />
                                        <span>{task.error_msg || '未知生成错误'}</span>
                                    </div>
                                ) : task.status === 'SENT' ? (
                                    <div className="flex items-center justify-center p-4">
                                        <span className="text-xs text-gray-400 font-medium">消息已成功发送至微信</span>
                                    </div>
                                ) : (
                                    <div className="h-20 flex items-center justify-center">
                                        <div className="flex items-center space-x-2 text-gray-400 text-xs italic">
                                            <Loader2 className="w-3 h-3 animate-spin" />
                                            <span>等待智能建议...</span>
                                        </div>
                                    </div>
                                )}

                                {/* 底部操作 */}
                                {task.status !== 'SENT' && (
                                    <div className="pt-2 flex space-x-2">
                                        <button
                                            disabled={task.status !== 'COMPLETED' || processingId === task.id || isBulkSending}
                                            onClick={() => handleSend(task)}
                                            className={`flex-1 flex items-center justify-center space-x-2 py-2.5 rounded-xl font-semibold transition-all ${task.status === 'COMPLETED'
                                                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/30'
                                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                }`}
                                        >
                                            {processingId === task.id && !isBulkSending ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <>
                                                    <Send className="w-4 h-4" />
                                                    <span>一键发送</span>
                                                </>
                                            )}
                                        </button>
                                        <button className="p-2.5 rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
                                            <Check className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 底部悬浮操作栏 */}
            {selectedCount > 0 && (
                <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-bottom-5 duration-300">
                    <div className="bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl px-6 py-4 shadow-2xl flex items-center space-x-6 text-white min-w-[300px]">
                        <div className="flex items-center space-x-3">
                            <div className="bg-blue-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">
                                {selectedCount}
                            </div>
                            <span className="text-sm font-medium">个项目已选定</span>
                        </div>
                        <div className="h-6 w-px bg-white/20"></div>
                        <button
                            onClick={handleBatchSend}
                            disabled={isBulkSending}
                            className={`flex items-center space-x-2 px-6 py-2 rounded-xl font-bold transition-all ${isBulkSending
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 shadow-lg shadow-blue-500/30'
                                }`}
                        >
                            {isBulkSending ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>正在批量发放...</span>
                                </>
                            ) : (
                                <>
                                    <Send className="w-4 h-4" />
                                    <span>批量一键发放</span>
                                </>
                            )}
                        </button>
                        <button
                            onClick={() => setSelectedIds([])}
                            disabled={isBulkSending}
                            className="text-white/60 hover:text-white transition-colors text-sm font-medium"
                        >
                            取消选择
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BatchProcessingKanban;
