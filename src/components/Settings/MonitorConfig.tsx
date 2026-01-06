import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw } from 'lucide-react';

interface MonitorConfig {
  monitor_keyword: string;
  monitor_match_mode: 'contains' | 'startswith' | 'exact';
}

export const MonitorConfig: React.FC = () => {
  const [config, setConfig] = useState<MonitorConfig>({
    monitor_keyword: '客户',
    monitor_match_mode: 'contains'
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/ai/config');
      const data = await response.json();
      if (data.success) {
        setConfig({
          monitor_keyword: data.config.monitor_keyword || '客户',
          monitor_match_mode: data.config.monitor_match_mode || 'contains'
        });
      }
    } catch (error) {
      console.error('Failed to load config:', error);
      setMessage({ type: 'error', text: '加载配置失败' });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:5000/api/ai/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      if (data.success) {
        setMessage({ type: 'success', text: '配置保存成功！监听器将在下次扫描时生效' });
      } else {
        setMessage({ type: 'error', text: '保存失败：' + data.error });
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      setMessage({ type: 'error', text: '保存失败，请检查网络连接' });
    } finally {
      setSaving(false);
    }
  };

  const handleKeywordChange = (value: string) => {
    setConfig(prev => ({ ...prev, monitor_keyword: value }));
    setMessage(null);
  };

  const handleMatchModeChange = (value: 'contains' | 'startswith' | 'exact') => {
    setConfig(prev => ({ ...prev, monitor_match_mode: value }));
    setMessage(null);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-6 h-6 text-blue-500" />
        <h2 className="text-xl font-semibold">微信监听配置</h2>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
          <p className="text-gray-500">加载配置中...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* 监听关键词 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              监听关键词
            </label>
            <input
              type="text"
              value={config.monitor_keyword}
              onChange={(e) => handleKeywordChange(e.target.value)}
              placeholder="输入要监听的关键词，如：客户"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              只有联系人名称匹配此关键词的会话才会被监听
            </p>
          </div>

          {/* 匹配模式 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              匹配模式
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_mode"
                  value="contains"
                  checked={config.monitor_match_mode === 'contains'}
                  onChange={(e) => handleMatchModeChange(e.target.value as any)}
                  className="mr-2"
                />
                <span className="text-sm">包含匹配（推荐）</span>
                <span className="text-xs text-gray-500 ml-2">- 联系人名称包含关键词即可</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_mode"
                  value="startswith"
                  checked={config.monitor_match_mode === 'startswith'}
                  onChange={(e) => handleMatchModeChange(e.target.value as any)}
                  className="mr-2"
                />
                <span className="text-sm">开头匹配</span>
                <span className="text-xs text-gray-500 ml-2">- 联系人名称必须以关键词开头</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_mode"
                  value="exact"
                  checked={config.monitor_match_mode === 'exact'}
                  onChange={(e) => handleMatchModeChange(e.target.value as any)}
                  className="mr-2"
                />
                <span className="text-sm">精确匹配</span>
                <span className="text-xs text-gray-500 ml-2">- 联系人名称必须完全等于关键词</span>
              </label>
            </div>
          </div>

          {/* 示例说明 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">匹配示例</h3>
            <div className="text-sm text-blue-800 space-y-1">
              <p><strong>关键词：</strong>"{config.monitor_keyword}"</p>
              <p><strong>当前模式：</strong>{
                config.monitor_match_mode === 'contains' ? '包含匹配' :
                config.monitor_match_mode === 'startswith' ? '开头匹配' : '精确匹配'
              }</p>
              <div className="mt-2">
                <p className="font-medium">会匹配的联系人名称：</p>
                <ul className="list-disc list-inside ml-2 space-y-0.5">
                  {config.monitor_match_mode === 'contains' && (
                    <>
                      <li>✅ {config.monitor_keyword}张三</li>
                      <li>✅ VIP{config.monitor_keyword}</li>
                      <li>✅ 重要{config.monitor_keyword}李四</li>
                    </>
                  )}
                  {config.monitor_match_mode === 'startswith' && (
                    <>
                      <li>✅ {config.monitor_keyword}张三</li>
                      <li>✅ {config.monitor_keyword}-李四</li>
                      <li>❌ VIP{config.monitor_keyword}</li>
                    </>
                  )}
                  {config.monitor_match_mode === 'exact' && (
                    <>
                      <li>✅ {config.monitor_keyword}</li>
                      <li>❌ {config.monitor_keyword}张三</li>
                      <li>❌ VIP{config.monitor_keyword}</li>
                    </>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* 消息提示 */}
          {message && (
            <div className={`p-3 rounded-lg ${
              message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 
              'bg-red-50 text-red-800 border border-red-200'
            }`}>
              {message.text}
            </div>
          )}

          {/* 保存按钮 */}
          <div className="flex justify-end">
            <button
              onClick={saveConfig}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {saving ? '保存中...' : '保存配置'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
