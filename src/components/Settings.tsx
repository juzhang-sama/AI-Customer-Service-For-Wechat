import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, AlertCircle, CheckCircle } from 'lucide-react';

export const Settings = () => {
  const [monitorKeyword, setMonitorKeyword] = useState('客户');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 加载配置
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/ai/config');
        const data = await response.json();
        if (data.monitor_keyword) {
          setMonitorKeyword(data.monitor_keyword);
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };

    fetchConfig();
  }, []);

  // 保存配置
  const handleSave = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:5000/api/ai/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          monitor_keyword: monitorKeyword
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: '配置保存成功！请重启后端服务以生效。' });
      } else {
        setMessage({ type: 'error', text: data.error || '保存失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '网络错误，请检查后端服务' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-6 max-w-2xl mx-auto">
      {/* 标题 */}
      <div className="flex items-center space-x-3 mb-6">
        <SettingsIcon className="w-6 h-6 text-blue-500" />
        <h2 className="text-2xl font-bold text-gray-800">系统设置</h2>
      </div>

      {/* 监听关键词设置 */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            全局监听关键词
          </label>
          <input
            type="text"
            value={monitorKeyword}
            onChange={(e) => setMonitorKeyword(e.target.value)}
            placeholder="例如: 客户"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-2 text-xs text-gray-500">
            只有联系人名称以此关键词开头的会话才会被监听。例如设置为"客户"，则只监听"客户-张三"、"客户-李四"等联系人。
          </p>
        </div>

        {/* 示例说明 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">使用示例</h3>
          <div className="space-y-1 text-xs text-blue-700">
            <p>• 关键词设置为 <code className="bg-blue-100 px-1 rounded">客户</code></p>
            <p>• 会监听: "客户-张三"、"客户-李四"、"客户ABC"</p>
            <p>• 不监听: "张三"、"代理-王五"、"员工-赵六"</p>
          </div>
        </div>

        {/* 消息提示 */}
        {message && (
          <div
            className={`p-3 rounded-lg flex items-start space-x-2 ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
            )}
            <p
              className={`text-xs ${
                message.type === 'success' ? 'text-green-700' : 'text-red-700'
              }`}
            >
              {message.text}
            </p>
          </div>
        )}

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>保存中...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>保存配置</span>
            </>
          )}
        </button>
      </div>

      {/* 重要提示 */}
      <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-yellow-800 mb-2">⚠️ 重要提示</h3>
        <ul className="space-y-1 text-xs text-yellow-700">
          <li>• 修改配置后需要<strong>重启后端服务</strong>才能生效</li>
          <li>• 建议在微信中统一联系人命名格式，例如: "客户-姓名"</li>
          <li>• 关键词区分大小写，请确保与联系人名称一致</li>
        </ul>
      </div>
    </div>
  );
};

