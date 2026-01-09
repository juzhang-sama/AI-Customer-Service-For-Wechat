
import { useEffect, useRef, useState } from 'react';
import { MessageSquare, Bell, RefreshCw, Trash2, X } from 'lucide-react';
import { InlineReplyGenerator } from './AIExpert/InlineReplyGenerator';
import { useMessages } from '../contexts';
import { AutoReplyControl } from './AutoReplyControl';
import { ToastContainer } from './Toast';

const MessageCenter = () => {
    // 使用全局消息状态
    const {
        sessions,
        activeSessionId,
        setActiveSessionId,
        isConnected,
        isRetrying,
        deleteSession,
        deleteMessage,
        clearUnread,
        autoReplyConfig,
        setAutoReplyConfig,
        toasts,
        closeToast
    } = useMessages();

    const [hoveredMessageIndex, setHoveredMessageIndex] = useState<number | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    const sortedSessionIds = Object.keys(sessions).sort((a, b) => {
        return sessions[b].lastTime.localeCompare(sessions[a].lastTime);
    });

    // 选择会话时清除未读数
    const handleSelectSession = (id: string) => {
        setActiveSessionId(id);
        clearUnread(id);
    };

    // 删除单条消息
    const handleDeleteMessage = async (sessionId: string, messageIndex: number) => {
        if (!confirm('确定要删除这条消息吗？')) {
            return;
        }
        deleteMessage(sessionId, messageIndex);
    };

    // 删除整个会话
    const handleDeleteSession = async (sessionId: string) => {
        if (!confirm(`确定要删除与 "${sessionId}" 的所有对话吗？`)) {
            return;
        }

        try {
            await deleteSession(sessionId);
            alert('会话删除成功');
        } catch (error) {
            alert(`删除会话失败: ${error}`);
        }
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [activeSessionId, sessions]);

    const activeSession = activeSessionId ? sessions[activeSessionId] : null;

    return (
        <>
            {/* Toast 通知容器 */}
            <ToastContainer toasts={toasts} onClose={closeToast} />

            {/* 自动回复控制面板 */}
            <div className="mb-4">
                <AutoReplyControl config={autoReplyConfig} onChange={setAutoReplyConfig} />
            </div>

            <div className="bg-white rounded-2xl shadow-xl border border-gray-200 flex h-[600px] overflow-hidden antialiased relative">
            {/* Session List (Left) */}
            <div className="w-64 border-r border-gray-100 flex flex-col bg-[#f0f0f0]/50 backdrop-blur-sm">
                <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                    <h2 className="font-bold text-gray-800 flex items-center">
                        <MessageSquare className="w-4 h-4 mr-2 text-blue-500" />
                        会话
                    </h2>
                    <div className="flex items-center space-x-1">
                        {isRetrying && !isConnected && <RefreshCw className="w-3 h-3 text-orange-400 animate-spin" />}
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {sortedSessionIds.length === 0 ? (
                        <div className="p-8 text-center text-gray-400 text-xs">等待微信同步...</div>
                    ) : (
                        sortedSessionIds.map(id => {
                            const session = sessions[id];
                            return (
                                <div
                                    key={id}
                                    className={`p-3 transition-all border-b border-gray-50/50 flex items-center space-x-3 group
                    ${activeSessionId === id ? 'bg-white shadow-sm ring-1 ring-black/5' : 'hover:bg-black/5'}`}
                                >
                                    <div
                                        onClick={() => handleSelectSession(id)}
                                        className="flex items-center space-x-3 flex-1 min-w-0 cursor-pointer"
                                    >
                                        <div className="w-10 h-10 bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center text-gray-500 font-bold text-sm shrink-0">
                                            {id.slice(0, 1)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-baseline">
                                                <h3 className="text-sm font-semibold text-gray-800 truncate">{id}</h3>
                                                <span className="text-[10px] text-gray-400">{session.lastTime.slice(0, 5)}</span>
                                            </div>
                                            <p className="text-xs text-gray-500 truncate mt-0.5">{session.lastMessage}</p>
                                        </div>
                                    </div>

                                    {/* 删除按钮 */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteSession(id);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-red-50 rounded-lg"
                                        title="删除会话"
                                    >
                                        <Trash2 className="w-3.5 h-3.5 text-red-500" />
                                    </button>

                                    {session.unreadCount > 0 && activeSessionId !== id && (
                                        <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-[9px] text-white">
                                            {session.unreadCount}
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* Chat Area (Center) */}
            <div className="flex-1 flex flex-col bg-white">
                {activeSession ? (
                    <>
                        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white/80 backdrop-blur-md sticky top-0 z-10">
                            <h3 className="font-bold text-gray-800">{activeSession.id}</h3>
                            <span className="text-[10px] text-gray-400 italic">实时监控中</span>
                        </div>

                        <div
                            ref={scrollRef}
                            className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#f5f5f5]/30 scroll-smooth"
                        >
                            {activeSession.messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`flex ${msg.is_self ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-500 group`}
                                    onMouseEnter={() => setHoveredMessageIndex(idx)}
                                    onMouseLeave={() => setHoveredMessageIndex(null)}
                                >
                                    <div className={`flex flex-col max-w-[80%] ${msg.is_self ? 'items-end' : 'items-start'} relative`}>
                                        <div className="flex items-center space-x-2 mb-1 px-1">
                                            {!msg.is_self && <span className="text-[10px] font-medium text-gray-500 uppercase tracking-tighter">{msg.sender}</span>}
                                            <span className="text-[9px] text-gray-300 font-mono">{msg.time}</span>

                                            {/* 删除按钮 */}
                                            {hoveredMessageIndex === idx && (
                                                <button
                                                    onClick={() => handleDeleteMessage(activeSession.id, idx)}
                                                    className="p-1 hover:bg-red-50 rounded transition-colors"
                                                    title="删除消息"
                                                >
                                                    <X className="w-3 h-3 text-red-500" />
                                                </button>
                                            )}
                                        </div>
                                        <div className={`p-3.5 rounded-2xl shadow-sm border ${msg.is_self
                                            ? 'bg-[#95ec69] border-[#89d961] text-gray-800 rounded-tr-none'
                                            : 'bg-white border-gray-200 text-gray-800 rounded-tl-none'
                                            }`}>
                                            <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-300 space-y-4">
                        <Bell className="w-16 h-16 stroke-1 opacity-20" />
                        <p className="text-sm">选择左侧会话开始同步消息</p>
                    </div>
                )}
            </div>

            {/* AI 回复生成器 - 固定在右侧 */}
            {activeSession && activeSessionId && (
                <div className="w-80 border-l border-gray-200 bg-gray-50 flex flex-col">
                    <InlineReplyGenerator
                        currentSession={activeSessionId}
                        messages={activeSession.messages}
                    />
                </div>
            )}
        </div>
        </>
    );
};

export default MessageCenter;
