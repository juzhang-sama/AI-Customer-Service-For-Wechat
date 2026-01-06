import { useState, useEffect } from 'react';
import MessageSend from '../components/MessageSend';
import ContactList from '../components/ContactList';
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
        <div className="space-y-6">
            {/* 监听关键词设置卡片 */}
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <Settings className="w-5 h-5 text-blue-500" />
                        <div>
                            <h3 className="font-semibold text-gray-800">全局监听关键词</h3>
                            <p className="text-xs text-gray-500">只监听以此关键词开头的联系人</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        {isEditing ? (
                            <>
                                <input
                                    type="text"
                                    value={monitorKeyword}
                                    onChange={(e) => setMonitorKeyword(e.target.value)}
                                    className="px-3 py-1.5 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="例如: 客户"
                                />
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-all disabled:opacity-50 flex items-center space-x-1"
                                >
                                    {saving ? (
                                        <>
                                            <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                            <span>保存中</span>
                                        </>
                                    ) : (
                                        <>
                                            <Save className="w-3 h-3" />
                                            <span>保存</span>
                                        </>
                                    )}
                                </button>
                                <button
                                    onClick={() => setIsEditing(false)}
                                    className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 transition-all"
                                >
                                    取消
                                </button>
                            </>
                        ) : (
                            <>
                                <span className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded font-medium text-sm">
                                    {monitorKeyword}
                                </span>
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="px-4 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-all"
                                >
                                    修改
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* 消息提示 */}
                {message && (
                    <div
                        className={`mt-3 p-2 rounded flex items-start space-x-2 ${
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
            </div>

            {/* 主要内容区域 - 优化后的布局 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <MessageSend />
                <div className="h-[600px]">
                    <ContactList />
                </div>
            </div>

            {/* 会话区域 - 占据更多空间 */}
            <div className="w-full">
                <MessageCenter />
            </div>
        </div>
    );
};

export default Dashboard;
