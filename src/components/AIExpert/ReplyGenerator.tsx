import React, { useState } from 'react';
import { Sparkles, Copy, Edit, Send, Loader2, AlertCircle, Check, Star } from 'lucide-react';

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

interface ReplyGeneratorProps {
  currentSession: string | null;
  messages: Message[];
  onReplySelect?: (content: string) => void;
}

export const ReplyGenerator: React.FC<ReplyGeneratorProps> = ({
  currentSession,
  messages,
  onReplySelect
}) => {
  const [replies, setReplies] = useState<ReplyVersion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ total_tokens: number; cost: number } | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedContent, setEditedContent] = useState<string>('');

  const handleGenerate = async () => {
    if (!currentSession || messages.length === 0) {
      setError('请先选择一个会话');
      return;
    }

    setLoading(true);
    setError(null);
    setReplies([]);

    try {
      // 获取最后一条客户消息
      const customerMessages = messages.filter(msg => !msg.is_self);
      if (customerMessages.length === 0) {
        setError('没有客户消息');
        setLoading(false);
        return;
      }

      const lastCustomerMessage = customerMessages[customerMessages.length - 1];

      // 准备会话历史（最近10条消息）
      const conversationHistory = messages.slice(-10).map(msg => ({
        role: msg.is_self ? 'assistant' : 'user',
        content: msg.content
      }));

      const response = await fetch('http://localhost:5000/api/ai/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: currentSession,
          customer_message: lastCustomerMessage.content,
          conversation_history: conversationHistory
        })
      });

      const data = await response.json();

      if (data.success && data.suggestions) {
        // 转换后端返回的格式为前端期望的格式
        const formattedReplies: ReplyVersion[] = [
          {
            version: '版本1',
            content: data.suggestions.aggressive,
            style: '进取型'
          },
          {
            version: '版本2',
            content: data.suggestions.conservative,
            style: '保守型'
          },
          {
            version: '版本3',
            content: data.suggestions.professional,
            style: '专业型'
          }
        ];

        setReplies(formattedReplies);
        setStats({
          total_tokens: data.tokens_used || 0,
          cost: data.cost || 0
        });
      } else {
        setError(data.error || '生成失败');
      }
    } catch (err) {
      console.error('Generate error:', err);
      setError('网络连接失败，请检查后端服务器');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (content: string, index: number) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000); // 2秒后隐藏提示
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleEdit = (index: number, content: string) => {
    setEditingIndex(index);
    setEditedContent(content);
  };

  const handleSaveEdit = (index: number) => {
    const updatedReplies = [...replies];
    updatedReplies[index].content = editedContent;
    setReplies(updatedReplies);
    setEditingIndex(null);
    setEditedContent('');
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditedContent('');
  };

  const handleSend = async (content: string) => {
    if (!currentSession) return;

    try {
      const response = await fetch('http://localhost:5000/api/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          who: currentSession,
          message: content
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        // 发送成功，可以显示提示
        if (onReplySelect) {
          onReplySelect(content);
        }
      } else {
        alert('发送失败：' + data.message);
      }
    } catch (err) {
      console.error('Send error:', err);
      alert('发送失败，请检查网络连接');
    }
  };

  const handleFavorite = async (reply: ReplyVersion) => {
    try {
      // 获取最后一条客户消息作为问题
      const customerMessages = messages.filter(msg => !msg.is_self);
      const lastCustomerMessage = customerMessages[customerMessages.length - 1];

      const response = await fetch('http://localhost:5000/api/ai/favorites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_type: '客户咨询',
          customer_question: lastCustomerMessage?.content || '',
          reply_text: reply.content,
          tags: [reply.style, currentSession || '']
        })
      });

      const data = await response.json();
      if (data.success) {
        alert('收藏成功！');
      } else {
        alert('收藏失败：' + data.error);
      }
    } catch (err) {
      console.error('Favorite error:', err);
      alert('收藏失败，请检查网络连接');
    }
  };

  const getStyleIcon = (style: string) => {
    switch (style) {
      case '进取型':
        return '🚀';
      case '保守型':
        return '🛡️';
      case '专业型':
        return '💼';
      default:
        return '📝';
    }
  };

  const getStyleColor = (style: string) => {
    switch (style) {
      case '进取型':
        return 'from-orange-50 to-red-50 border-orange-200';
      case '保守型':
        return 'from-blue-50 to-cyan-50 border-blue-200';
      case '专业型':
        return 'from-purple-50 to-pink-50 border-purple-200';
      default:
        return 'from-gray-50 to-gray-100 border-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      {/* 生成按钮 */}
      <button
        onClick={handleGenerate}
        disabled={loading || !currentSession}
        className="w-full py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>生成中...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            <span>生成回复</span>
          </>
        )}
      </button>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-red-700">
            <p className="font-semibold">生成失败</p>
            <p className="mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* 回复列表 */}
      {replies.length > 0 && (
        <div className="space-y-3">
          {replies.map((reply, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border bg-gradient-to-br ${getStyleColor(reply.style)} transition-all hover:shadow-md`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700 flex items-center">
                  <span className="mr-2">{getStyleIcon(reply.style)}</span>
                  {reply.style}
                </span>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">{reply.version}</span>
                  <button
                    onClick={() => handleFavorite(reply)}
                    className="p-1 hover:bg-white/50 rounded transition-colors"
                    title="收藏话术"
                  >
                    <Star className="w-4 h-4 text-yellow-500" />
                  </button>
                </div>
              </div>

              {/* 编辑模式 */}
              {editingIndex === index ? (
                <div className="space-y-2 mb-3">
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                  />
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleSaveEdit(index)}
                      className="flex-1 py-1.5 px-3 bg-green-500 text-white rounded text-xs font-medium hover:bg-green-600 transition-colors"
                    >
                      保存
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="flex-1 py-1.5 px-3 bg-gray-300 text-gray-700 rounded text-xs font-medium hover:bg-gray-400 transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-800 leading-relaxed mb-3 whitespace-pre-wrap">
                  {reply.content}
                </p>
              )}

              {/* 操作按钮 */}
              {editingIndex !== index && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleCopy(reply.content, index)}
                    className="flex-1 py-2 px-3 bg-white border border-gray-300 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center space-x-1"
                  >
                    {copiedIndex === index ? (
                      <>
                        <Check className="w-3 h-3 text-green-600" />
                        <span className="text-green-600">已复制</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>复制</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleEdit(index, reply.content)}
                    className="py-2 px-3 bg-white border border-gray-300 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center space-x-1"
                  >
                    <Edit className="w-3 h-3" />
                    <span>编辑</span>
                  </button>
                  <button
                    onClick={() => handleSend(reply.content)}
                    className="flex-1 py-2 px-3 bg-blue-500 text-white rounded-lg text-xs font-medium hover:bg-blue-600 transition-colors flex items-center justify-center space-x-1"
                  >
                    <Send className="w-3 h-3" />
                    <span>发送</span>
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 统计信息 */}
      {stats && (
        <div className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">本次费用</span>
            <span className="font-bold text-green-700">¥{stats.cost.toFixed(4)}</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="text-gray-600">Token 数</span>
            <span className="font-semibold text-gray-700">{stats.total_tokens}</span>
          </div>
        </div>
      )}
    </div>
  );
};

