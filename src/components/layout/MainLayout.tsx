import Sidebar from './Sidebar';

type Page = 'dashboard' | 'ai-expert' | 'settings' | 'kanban' | 'analytics';

interface MainLayoutProps {
    children: React.ReactNode;
    currentPage: Page;
    onNavigate: (page: Page) => void;
}

const pageTitle: Record<Page, string> = {
    'dashboard': '仪表盘',
    'ai-expert': 'AI 专家配置',
    'kanban': '批量处理看板',
    'analytics': '业务洞察中心',
    'settings': '系统设置'
};

const MainLayout = ({ children, currentPage, onNavigate }: MainLayoutProps) => {
    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden">
            <Sidebar currentPage={currentPage} onNavigate={onNavigate} />
            <main className="flex-1 overflow-auto">
                <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
                    <h2 className="text-xl font-semibold text-gray-800">
                        {pageTitle[currentPage]}
                    </h2>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-500">v0.0.1 Beta</span>
                    </div>
                </header>
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
