import React, { useState } from 'react';
import { Users, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

interface Contact {
    nickname: string;
    wxid: string;
}

const ContactList = () => {
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    React.useEffect(() => {
        // @ts-ignore
        const handler = (_event, data) => {
            console.log('Received updated contacts:', data);
            setContacts(data);
            setLoading(false);
        };

        // @ts-ignore
        const statusHandler = (_event, status) => {
            if (status === 'start') {
                setLoading(true);
                setError(null);
            } else if (status === 'error') {
                setLoading(false);
                setError('扫描失败');
            }
        };

        // @ts-ignore
        if (window.ipcRenderer) {
            // @ts-ignore
            window.ipcRenderer.on('contacts-updated', handler);
            // @ts-ignore
            window.ipcRenderer.on('scan-status', statusHandler);
        }

        return () => {
            if (window.ipcRenderer) {
                // @ts-ignore
                window.ipcRenderer.off('contacts-updated', handler);
                // @ts-ignore
                window.ipcRenderer.off('scan-status', statusHandler);
            }
        };
    }, []);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col h-full overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-50 rounded-lg">
                        <Users className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900">微信号，微信名</h3>
                </div>
                {loading && (
                    <div className="flex items-center space-x-2 text-blue-600 animate-pulse">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span className="text-sm font-medium">正在扫描...</span>
                    </div>
                )}
            </div>

            <div className="flex-1 overflow-auto p-4 space-y-2">
                {error && (
                    <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-start space-x-3">
                        <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                        <div className="text-sm text-red-700">
                            <p className="font-semibold">导入出错</p>
                            <p className="mt-1">{error}</p>
                        </div>
                    </div>
                )}

                {contacts.length === 0 && !loading && !error && (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4 py-20">
                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center text-gray-300">
                            <Users size={32} />
                        </div>
                        <p>暂无联系人数据</p>
                        <p className="text-xs">点击上方按钮开始扫描导入</p>
                    </div>
                )}

                {contacts.map((contact, index) => (
                    <div
                        key={index}
                        className="flex items-center justify-between p-4 rounded-xl border border-gray-100 hover:border-blue-100 hover:bg-blue-50/50 transition-all group"
                    >
                        <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-gray-100 to-gray-200 flex items-center justify-center text-gray-600 font-bold text-sm">
                                {contact.nickname ? contact.nickname[0] : '?'}
                            </div>
                            <div>
                                <p className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                                    {contact.nickname || 'Unknown'}
                                </p>
                                <p className="text-sm text-gray-500 font-mono">{contact.wxid || 'Unknown'}</p>
                            </div>
                        </div>
                        <CheckCircle className="w-5 h-5 text-green-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                ))}

                {loading && contacts.length === 0 && (
                    <div className="space-y-3">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="animate-pulse flex items-center space-x-4 p-4 rounded-xl border border-gray-50">
                                <div className="w-10 h-10 bg-gray-100 rounded-full"></div>
                                <div className="flex-1 space-y-2">
                                    <div className="h-4 bg-gray-100 rounded w-1/4"></div>
                                    <div className="h-3 bg-gray-100 rounded w-1/2"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
                    共计 {contacts.length} 位联系人
                </p>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100/50 text-blue-600 font-medium">
                    已就绪
                </span>
            </div>
        </div>
    );
};

export default ContactList;
