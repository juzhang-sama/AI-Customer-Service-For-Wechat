import React, { useState, useEffect } from 'react';
import { Sparkles, Copy, Send, Loader2, AlertCircle, Check, Edit2, Brain, Info, Zap, ChevronDown, ChevronUp, History, Bot } from 'lucide-react';
import ReplyHistorySidebar from './ReplyHistorySidebar';
import { useMessages } from '../../contexts';

interface Message {
  session: string;
  sender: string;
  content: string;
  is_self: boolean;
  time: string;
}

interface ReplyVersion {
  version: string;
  content: string;
  style: string;
}

interface AIExpert {
  id: number;
  name: string;
  is_active: number;
}

interface InlineReplyGeneratorProps {
  currentSession: string;
  messages: Message[];
  onReplySelect?: (content: string) => void;
}

// Typing Text Effect Component
const TypingText: React.FC<{ text: string; speed?: number }> = ({ text, speed = 20 }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setDisplayedText('');
    setIndex(0);
  }, [text]);

  useEffect(() => {
    if (index < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText((prev: string) => prev + text[index]);
        setIndex((prev: number) => prev + 1);
      }, speed);
      return () => clearTimeout(timeout);
    }
  }, [index, text, speed]);

  return <span>{displayedText}</span>;
};

// Thinking Process Component
const ThinkingProcess: React.FC<{ metadata: any }> = ({ metadata }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!metadata) return null;

  return (
    <div className="mb-4 overflow-hidden rounded-xl border border-white/20 bg-white/10 backdrop-blur-md shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-3 text-sm font-medium text-purple-700 bg-purple-50/50 hover:bg-purple-100/50 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4" />
          <span>🧠 AI 思考过程</span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="p-3 space-y-3 text-xs border-t border-purple-100/50 animate-in slide-in-from-top-2 duration-300">
          <div className="flex items-start space-x-2">
            <Zap className="w-3 h-3 mt-0.5 text-yellow-500" />
            <div>
              <span className="font-semibold text-gray-700">意图识别：</span>
              <span className="text-gray-600">{metadata.intent || '咨询'}</span>
            </div>
          </div>
          <div className="flex items-start space-x-2">
            <Info className="w-3 h-3 mt-0.5 text-blue-500" />
            <div>
              <span className="font-semibold text-gray-700">对话阶段：</span>
              <span className="text-gray-600">{metadata.conversation_stage || '方案推荐'}</span>
            </div>
          </div>
          {metadata.objection_type && (
            <div className="flex items-start space-x-2 text-red-600">
              <AlertCircle className="w-3 h-3 mt-0.5" />
              <div>
                <span className="font-semibold">异议类型：</span>
                <span>{metadata.objection_type}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const InlineReplyGenerator: React.FC<InlineReplyGeneratorProps> = ({
  currentSession,
  messages,
  onReplySelect
}) => {
  // 获取自动回复配置
  const { autoReplyConfig } = useMessages();
  const isAutoMode = autoReplyConfig.enabled;

  const [, setIsExpanded] = useState(false);
  const [replies, setReplies] = useState<ReplyVersion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ total_tokens: number; cost: number } | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [lastSession, setLastSession] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<any>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [lastTaskLoaded, setLastTaskLoaded] = useState<number | null>(null);

  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [sendingIndex, setSendingIndex] = useState<number | null>(null);

  const [aiExperts, setAiExperts] = useState<AIExpert[]>([]);
  const [selectedExpertId, setSelectedExpertId] = useState<number | null>(null);

  useEffect(() => {
    const fetchExperts = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ai/prompts');
        const data = await response.json();
        if (data.success && Array.isArray(data.prompts)) {
          setAiExperts(data.prompts);
          const activeExpert = data.prompts.find((expert: AIExpert) => expert.is_active === 1);
          if (activeExpert) setSelectedExpertId(activeExpert.id);
        }
      } catch (error) {
        console.error('Failed to load AI experts:', error);
      }
    };
    fetchExperts();
  }, []);

  useEffect(() => {
    if (currentSession !== lastSession) {
      setReplies([]);
      setError(null);
      setStats(null);
      setIsExpanded(false);
      setLastSession(currentSession);
      setMetadata(null);
      setLastTaskLoaded(null);

      const recoverLastTask = async () => {
        try {
          const response = await fetch(`http://localhost:5000/api/ai/tasks/recent?limit=50`);
          const data = await response.json();
          if (data.success && Array.isArray(data.tasks)) {
            const task = data.tasks.find((t: any) => t.session_id === currentSession);
            if (task && task.ai_reply_options) {
              const options = task.ai_reply_options;
              setReplies([
                { version: '版本1', content: options.aggressive, style: '进取型' },
                { version: '版本2', content: options.conservative, style: '保守型' },
                { version: '版本3', content: options.professional, style: '专业型' }
              ]);
              setIsExpanded(true);
              setIsTyping(false);
              setLastTaskLoaded(task.id);
            }
          }
        } catch (err) {
          console.error('Failed to recover last task:', err);
        }
      };

      if (currentSession) recoverLastTask();
    }
  }, [currentSession, lastSession]);

  const handleGenerate = async () => {
    if (!currentSession) return;
    setLoading(true);
    setError(null);
    try {
      const customerMessages = messages.filter(msg => !msg.is_self);
      const lastCustomerMessage = customerMessages[customerMessages.length - 1];
      if (!lastCustomerMessage) {
        setError('没有找到客户消息');
        setLoading(false);
        return;
      }
      const response = await fetch('http://localhost:5000/api/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession,
          customer_message: lastCustomerMessage.content,
          prompt_id: selectedExpertId,
          conversation_history: messages.slice(-10).map(msg => ({
            role: msg.is_self ? 'assistant' : 'user',
            content: msg.content
          }))
        })
      });
      const data = await response.json();
      if (data.success && data.suggestions) {
        setReplies([
          { version: '版本1', content: data.suggestions.aggressive, style: '进取型' },
          { version: '版本2', content: data.suggestions.conservative, style: '保守型' },
          { version: '版本3', content: data.suggestions.professional, style: '专业型' }
        ]);
        setMetadata(data.metadata);
        setStats({ total_tokens: data.tokens_used || 0, cost: data.cost || 0 });
        setIsExpanded(true);
        setIsTyping(true);
      } else {
        setError(data.error || '生成失败');
      }
    } catch (err) {
      setError('网络连接失败，请检查后端服务器');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (content: string, index: number) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) { }
  };

  const handleEdit = (content: string, index: number) => {
    setEditingIndex(index);
    setEditContent(content);
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditContent('');
  };

  const handleSend = async (finalContent: string, originalContent?: string, index?: number) => {
    if (!currentSession) return;
    if (index !== undefined) setSendingIndex(index);
    try {
      const sendResponse = await fetch('http://localhost:5000/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ who: currentSession, message: finalContent })
      });
      const sendData = await sendResponse.json();
      if (sendData.status === 'success') {
        if (onReplySelect) onReplySelect(finalContent);
        if (originalContent) {
          const customerMessages = messages.filter(msg => !msg.is_self);
          const lastCustomerMessage = customerMessages[customerMessages.length - 1]?.content || '';
          const action = finalContent === originalContent ? 'ACCEPTED' : 'MODIFIED';
          await fetch('http://localhost:5000/api/ai/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: currentSession,
              user_query: lastCustomerMessage,
              original_reply: originalContent,
              final_reply: finalContent,
              action: action,
              prompt_id: selectedExpertId
            })
          });
        }
        setEditingIndex(null);
      } else {
        alert('发送失败：' + sendData.message);
      }
    } catch (err) {
      alert('发送失败，请检查网络连接');
    } finally {
      setSendingIndex(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-50/50 to-white/50 backdrop-blur-xl relative">
      {/* 自动模式遮罩层 */}
      {isAutoMode && (
        <div className="absolute inset-0 z-50 bg-gray-900/60 backdrop-blur-sm flex flex-col items-center justify-center">
          <div className="bg-white rounded-2xl p-6 shadow-2xl text-center max-w-xs mx-4">
            <Bot className="w-12 h-12 text-green-500 mx-auto mb-3 animate-pulse" />
            <h4 className="font-bold text-gray-800 mb-2">自动回复模式已开启</h4>
            <p className="text-sm text-gray-500 mb-4">
              系统将自动处理客户消息，无需手动操作
            </p>
            <div className="text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
              <p>💡 如需手动回复，请先关闭自动模式</p>
            </div>
          </div>
        </div>
      )}

      {/* 标题栏 */}
      <div className="p-4 border-b border-white/20 bg-white/40 sticky top-0 z-10 backdrop-blur-md">
        <h3 className="font-bold text-gray-800 flex items-center justify-between tracking-tight w-full">
          <div className="flex items-center">
            <Sparkles className="w-5 h-5 mr-2 text-purple-600 animate-pulse" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-blue-600">
              AI 智能回复 2.0
            </span>
            {isAutoMode && (
              <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-600 text-[10px] font-bold rounded-full">
                自动
              </span>
            )}
          </div>
          <button
            onClick={() => setShowHistory(!showHistory)}
            disabled={isAutoMode}
            className={`p-2 rounded-lg transition-all ${showHistory ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-gray-100'} ${isAutoMode ? 'opacity-50 cursor-not-allowed' : ''}`}
            title="查看历史记录"
          >
            <History className="w-4 h-4" />
          </button>
        </h3>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        <div className={`flex flex-col flex-1 transition-all duration-300 ${showHistory ? 'mr-80' : ''}`}>
          {/* AI 专家选择 */}
          <div className="p-4 border-b border-white/10 bg-white/20 backdrop-blur-sm">
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2 px-1">
              当前 AI 专家
            </label>
            <select
              value={selectedExpertId || ''}
              onChange={(e) => setSelectedExpertId(Number(e.target.value))}
              className="w-full px-4 py-2 bg-white/60 border border-white/40 rounded-xl text-sm font-medium text-gray-700 focus:ring-2 focus:ring-purple-400 focus:border-transparent outline-none transition-all hover:bg-white/80"
            >
              <option value="">使用默认配置</option>
              {aiExperts.map((expert) => (
                <option key={expert.id} value={expert.id}>
                  {expert.name} {expert.is_active === 1 ? '(激活)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* 生成按钮 */}
          <div className="p-4">
            <button
              onClick={handleGenerate}
              disabled={loading || !currentSession}
              className="group relative w-full overflow-hidden py-3.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-2xl font-bold transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20"
            >
              <div className="relative z-10 flex items-center justify-center space-x-2">
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>正在思考中...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 group-hover:animate-bounce" />
                    <span>立即生成回复</span>
                  </>
                )}
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            </button>
          </div>

          {/* 回复内容区域 */}
          <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-4">
            <ThinkingProcess metadata={metadata} />
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-200/50 backdrop-blur-md rounded-2xl flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800 font-medium">{error}</p>
              </div>
            )}

            {replies.map((reply, index) => (
              <div key={index} className="group p-4 rounded-2xl border border-white/40 bg-white/40 backdrop-blur-md shadow-sm transition-all hover:shadow-md hover:bg-white/60">
                <div className="flex items-center justify-between mb-3">
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${reply.style === '进取型' ? 'bg-orange-100 text-orange-600' : reply.style === '保守型' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'}`}>
                    {reply.style}
                  </span>
                  {editingIndex !== index && (
                    <button onClick={() => handleEdit(reply.content, index)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-gray-400 hover:text-blue-500 hover:bg-blue-50">
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {editingIndex === index ? (
                  <div className="space-y-3">
                    <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} className="w-full text-sm p-3 bg-white/80 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-400 outline-none min-h-[100px]" autoFocus />
                    <div className="flex justify-end space-x-2">
                      <button onClick={cancelEdit} className="px-4 py-2 text-xs font-semibold text-gray-500 hover:bg-gray-100 rounded-xl">取消</button>
                      <button onClick={() => handleSend(editContent, reply.content, index)} disabled={sendingIndex === index} className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2">
                        {sendingIndex === index ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                        <span>发送修改</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="text-sm text-gray-800 leading-relaxed mb-4 whitespace-pre-wrap font-medium">
                      {isTyping ? <TypingText text={reply.content} /> : reply.content}
                    </div>
                    <div className="flex items-center space-x-3">
                      <button onClick={() => handleCopy(reply.content, index)} className="flex-1 py-2.5 px-3 bg-white/80 border border-gray-200 rounded-xl text-xs font-bold text-gray-700 hover:bg-white transition-all flex items-center justify-center space-x-2">
                        {copiedIndex === index ? <><Check className="w-4 h-4 text-green-500" /><span>已复制</span></> : <><Copy className="w-4 h-4 text-gray-400" /><span>复制</span></>}
                      </button>
                      <button onClick={() => handleSend(reply.content, reply.content, index)} disabled={sendingIndex === index} className="flex-1 py-2.5 px-3 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-xl text-xs font-bold hover:shadow-lg transition-all flex items-center justify-center space-x-2">
                        {sendingIndex === index ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        <span>直接发送</span>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}

            {stats && (
              <div className="p-4 bg-gradient-to-br from-green-400/10 to-emerald-400/20 border border-green-200/50 backdrop-blur-md rounded-2xl">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="text-gray-500 font-medium">本次响应成本</span>
                  <span className="font-extrabold text-green-700">¥ {stats.cost.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500 font-medium">消耗 Token</span>
                  <span className="font-bold text-gray-700">{stats.total_tokens}</span>
                </div>
              </div>
            )}

            {replies.length === 0 && !error && !loading && (
              <div className="text-center py-20">
                <Sparkles className="w-16 h-16 text-purple-200 animate-pulse mx-auto mb-4" />
                <p className="text-sm font-bold text-gray-400">点击上方按钮，开启 AI 智能辅助</p>
              </div>
            )}
          </div>
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="absolute right-0 top-0 bottom-0 w-80 border-l border-white/20 bg-white shadow-2xl z-20 animate-in slide-in-from-right duration-300">
            <ReplyHistorySidebar
              currentSession={currentSession}
              onSelectHistoricalReply={(content) => {
                setEditContent(content);
                setEditingIndex(2);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};
