import { useState } from 'react';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import { AIExpertConfig } from './pages/AIExpertConfig';
import BatchKanbanPage from './pages/BatchKanbanPage';
import AnalyticsPage from './pages/AnalyticsPage';
import { Settings } from './pages/Settings';

type Page = 'dashboard' | 'ai-expert' | 'settings' | 'kanban' | 'analytics';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'ai-expert':
        return <AIExpertConfig />;
      case 'kanban':
        return <div className="p-4"><BatchKanbanPage /></div>;
      case 'analytics':
        return <div className="p-4"><AnalyticsPage /></div>;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <MainLayout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderPage()}
    </MainLayout>
  );
}

export default App;
