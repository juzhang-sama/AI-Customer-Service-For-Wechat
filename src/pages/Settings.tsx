import React, { useState } from 'react';
import { MonitorConfig } from '../components/Settings/MonitorConfig';
import { Settings as SettingsIcon, MessageSquare, Bot, Database } from 'lucide-react';

type TabType = 'monitor' | 'ai' | 'database';

export const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('monitor');

  const tabs = [
    { id: 'monitor' as TabType, name: '微信监听', icon: MessageSquare, description: '配置微信消息监听规则' },
    { id: 'ai' as TabType, name: 'AI配置', icon: Bot, description: 'AI模型和API配置' },
    { id: 'database' as TabType, name: '数据管理', icon: Database, description: '数据库和存储配置' }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <SettingsIcon className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-bold">系统设置</h1>
        </div>
        <p className="text-gray-600">管理系统配置和参数</p>
      </div>

      {/* 标签页导航 */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.name}
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-6">
          {/* 标签页内容 */}
          {activeTab === 'monitor' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">微信监听配置</h2>
                <p className="text-gray-600">配置微信消息监听的关键词和匹配规则</p>
              </div>
              <MonitorConfig />
            </div>
          )}

          {activeTab === 'ai' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">AI配置</h2>
                <p className="text-gray-600">配置AI模型参数和API设置</p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">AI配置功能开发中...</p>
              </div>
            </div>
          )}

          {activeTab === 'database' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">数据管理</h2>
                <p className="text-gray-600">管理数据库连接和数据存储设置</p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <Database className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">数据管理功能开发中...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
