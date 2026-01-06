import React, { useState, useEffect } from 'react';
import { Bot, Sparkles, ChevronLeft, ChevronRight, Settings } from 'lucide-react';
import { ReplyGenerator } from './ReplyGenerator';

interface Message {
  session: string;
  sender: string;
  content: string;
  is_self: boolean;
  time: string;
}

interface AISidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentSession: string | null;
  messages: Message[];
}

export const AISidebar: React.FC<AISidebarProps> = ({
  isOpen,
  onToggle,
  currentSession,
  messages
}) => {
  const [activeConfig, setActiveConfig] = useState<any>(null);
  const [usageStats, setUsageStats] = useState<{ today: number; month: number }>({ today: 0, month: 0 });

  // 加载激活的配置
  useEffect(() => {
    const loadActiveConfig = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ai/prompts');
        const data = await response.json();

        if (data.success) {
          const active = data.prompts.find((p: any) => p.is_active);
          setActiveConfig(active);
        }
      } catch (error) {
        console.error('Failed to load active config:', error);
      }
    };

    loadActiveConfig();
  }, []);

  // 加载使用量统计
  useEffect(() => {
    const loadUsageStats = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ai/stats/usage');
        const data = await response.json();

        if (data.success && data.stats) {
          // 计算今日和本月费用
          const today = new Date().toISOString().split('T')[0];
          const thisMonth = today.substring(0, 7);

          const todayCost = data.stats
            .filter((s: any) => s.date === today)
            .reduce((sum: number, s: any) => sum + s.total_cost, 0);

          const monthCost = data.stats
            .filter((s: any) => s.date.startsWith(thisMonth))
            .reduce((sum: number, s: any) => sum + s.total_cost, 0);

          setUsageStats({ today: todayCost, month: monthCost });
        }
      } catch (error) {
        console.error('Failed to load usage stats:', error);
      }
    };

    loadUsageStats();

    // 每30秒刷新一次
    const interval = setInterval(loadUsageStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {/* 切换按钮 */}
      <button
        onClick={onToggle}
        className={`absolute top-4 ${isOpen ? 'right-[320px]' : 'right-4'} z-20 p-2 bg-white border border-gray-200 rounded-lg shadow-lg hover:bg-gray-50 transition-all duration-300`}
        title={isOpen ? '收起 AI 助手' : '展开 AI 助手'}
      >
        {isOpen ? (
          <ChevronRight className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        )}
      </button>

      {/* 侧边栏 */}
      <div
        className={`absolute top-0 right-0 h-full bg-white border-l border-gray-200 shadow-2xl transition-all duration-300 ease-in-out ${
          isOpen ? 'w-80 translate-x-0' : 'w-0 translate-x-full'
        } overflow-hidden`}
      >
        <div className="h-full flex flex-col">
          {/* 头部 */}
          <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-800 flex items-center">
                  AI 专家助手
                  <Sparkles className="w-4 h-4 ml-2 text-yellow-500" />
                </h3>
                <p className="text-xs text-gray-500">智能回复生成</p>
              </div>
            </div>
          </div>

          {/* 当前配置 */}
          <div className="p-4 border-b border-gray-100 bg-gray-50">
            {activeConfig ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">当前配置</span>
                  <button
                    onClick={() => window.location.href = '/#/ai-expert'}
                    className="text-xs text-blue-600 hover:text-blue-700 flex items-center"
                  >
                    <Settings className="w-3 h-3 mr-1" />
                    设置
                  </button>
                </div>
                <div className="bg-white p-3 rounded-lg border border-gray-200">
                  <p className="font-semibold text-gray-800 text-sm">{activeConfig.name}</p>
                  <div className="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                    <span>📚 {activeConfig.knowledge_base?.length || 0} 条知识</span>
                    <span>🚫 {activeConfig.forbidden_words?.length || 0} 个禁忌词</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-gray-500">未激活配置</p>
                <button
                  onClick={() => window.location.href = '/#/ai-expert'}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700"
                >
                  前往配置
                </button>
              </div>
            )}
          </div>

          {/* 会话信息 */}
          <div className="p-4 border-b border-gray-100">
            {currentSession ? (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-400 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                    {currentSession.slice(0, 1)}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-800 text-sm">{currentSession}</p>
                    <p className="text-xs text-gray-500">{messages.length} 条消息</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-gray-400">
                请选择一个会话
              </div>
            )}
          </div>

          {/* 回复生成区域 */}
          <div className="flex-1 overflow-y-auto p-4">
            <ReplyGenerator
              currentSession={currentSession}
              messages={messages}
              onReplySelect={(content) => {
                // TODO: 将回复内容填充到输入框
                console.log('Selected reply:', content);
              }}
            />
          </div>

          {/* 底部统计 */}
          <div className="p-4 border-t border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50">
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between items-center">
                <span>今日使用</span>
                <span className="font-bold text-blue-600">¥{usageStats.today.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>本月使用</span>
                <span className="font-bold text-purple-600">¥{usageStats.month.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

