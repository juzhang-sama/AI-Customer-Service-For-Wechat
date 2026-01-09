import { useState, useEffect } from 'react';
import MessageCenter from '../components/MessageCenter';
import { Settings, Save, AlertCircle, CheckCircle } from 'lucide-react';

const Dashboard = () => {
    const [monitorKeyword, setMonitorKeyword] = useState('客户');
    const [isEditing, setIsEditing] = useState(false);
    const [saving, setSaving] = useState(false);
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
        setSaving(true);
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
                setMessage({ type: 'success', text: '保存成功！请重启后端服务以生效。' });
                setIsEditing(false);
            } else {
                setMessage({ type: 'error', text: data.error || '保存失败' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: '网络错误，请检查后端服务' });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* 监听关键词设置卡片 - 紧凑版 */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Settings className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium text-gray-700">监听关键词</span>
                    </div>

                    <div className="flex items-center space-x-2">
                        {isEditing ? (
                            <>
                                <input
                                    type="text"
                                    value={monitorKeyword}
                                    onChange={(e) => setMonitorKeyword(e.target.value)}
                                    className="px-2 py-1 border border-gray-300 rounded text-sm w-24 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="例如: 客户"
                                />
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-all disabled:opacity-50"
                                >
                                    {saving ? '...' : '保存'}
                                </button>
                                <button
                                    onClick={() => setIsEditing(false)}
                                    className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs hover:bg-gray-300 transition-all"
                                >
                                    取消
                                </button>
                            </>
                        ) : (
                            <>
                                <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded font-medium text-sm">
                                    {monitorKeyword}
                                </span>
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-all"
                                >
                                    修改
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* 消息提示 */}
                {message && (
                    <div className={`mt-2 p-2 rounded flex items-center space-x-2 text-xs ${
                        message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                    }`}>
                        {message.type === 'success' ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        <span>{message.text}</span>
                    </div>
                )}
            </div>

            {/* 会话区域 - 占据全部空间 */}
            <div className="w-full">
                <MessageCenter />
            </div>
        </div>
    );
};

export default Dashboard;
