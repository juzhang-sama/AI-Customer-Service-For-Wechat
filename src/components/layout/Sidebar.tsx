import { Home, Settings, Users, Brain } from 'lucide-react';

type Page = 'dashboard' | 'ai-expert' | 'settings';

interface SidebarProps {
    currentPage: Page;
    onNavigate: (page: Page) => void;
}

const Sidebar = ({ currentPage, onNavigate }: SidebarProps) => {
    const menuItems = [
        { icon: Home, label: '首页', page: 'dashboard' as Page },
        { icon: Brain, label: 'AI专家搭建', page: 'ai-expert' as Page },
        { icon: Settings, label: '系统设置', page: 'settings' as Page },
    ];

    return (
        <div className="w-64 h-screen bg-slate-900 text-white flex flex-col">
            <div className="p-6 flex items-center space-x-3 border-b border-slate-800">
                <div className="w-8 h-8 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <span className="font-bold text-lg">G</span>
                </div>
                <span className="font-bold text-lg tracking-wide">天才群策</span>
            </div>

            <div className="flex-1 py-6">
                <nav className="space-y-1 px-3">
                    {menuItems.map((item, index) => (
                        <button
                            key={index}
                            onClick={() => onNavigate(item.page)}
                            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                                currentPage === item.page
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                            }`}
                        >
                            <item.icon size={20} className={`${currentPage === item.page ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
                            <span className="font-medium">{item.label}</span>
                        </button>
                    ))}
                </nav>
            </div>

            <div className="px-3 pb-4">
                <button
                    onClick={() => {
                        // @ts-ignore
                        window.ipcRenderer.send('scan-contacts-trigger');
                    }}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600 hover:text-white transition-all duration-200 shadow-sm"
                >
                    <Users size={18} />
                    <span className="font-semibold text-sm">同步联系人</span>
                </button>
            </div>

            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-slate-800/50">
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                        <Users size={16} />
                    </div>
                    <div className="flex-1">
                        <p className="text-sm font-medium">管理员</p>
                        <p className="text-xs text-slate-500">在线</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
