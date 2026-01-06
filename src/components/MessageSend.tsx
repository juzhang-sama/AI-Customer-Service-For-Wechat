import { useState } from 'react';
import { Send, Loader2, CheckCircle, XCircle } from 'lucide-react';

const MessageSend = () => {
    const [who, setWho] = useState('文件传输助手');
    const [message, setMessage] = useState('');
    const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
    const [errorMsg, setErrorMsg] = useState('');

    const handleSend = async () => {
        if (!who || !message) {
            setErrorMsg('请填写联系人和消息内容');
            setStatus('error');
            return;
        }

        setStatus('sending');
        setErrorMsg('');

        try {
            const response = await fetch('http://localhost:5000/api/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ who, message }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                setStatus('success');
                setMessage(''); // Clear message after success
                setTimeout(() => setStatus('idle'), 3000);
            } else {
                setStatus('error');
                setErrorMsg(data.message || '发送失败');
            }
        } catch (error) {
            setStatus('error');
            setErrorMsg('无法连接到后端服务');
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Send className="w-5 h-5 mr-2 text-blue-600" />
                发送微信消息
            </h3>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        联系人
                    </label>
                    <input
                        type="text"
                        value={who}
                        onChange={(e) => setWho(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="输入联系人名称"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        消息内容
                    </label>
                    <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        rows={4}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        placeholder="输入要发送的消息..."
                    />
                </div>

                <button
                    onClick={handleSend}
                    disabled={status === 'sending'}
                    className={`w-full py-3 px-4 rounded-lg font-medium flex items-center justify-center space-x-2 transition-all ${status === 'sending'
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                >
                    {status === 'sending' ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>发送中...</span>
                        </>
                    ) : (
                        <>
                            <Send className="w-5 h-5" />
                            <span>发送消息</span>
                        </>
                    )}
                </button>

                {status === 'success' && (
                    <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-lg">
                        <CheckCircle className="w-5 h-5" />
                        <span>发送成功！</span>
                    </div>
                )}

                {status === 'error' && (
                    <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
                        <XCircle className="w-5 h-5" />
                        <span>{errorMsg || '发送失败'}</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MessageSend;
