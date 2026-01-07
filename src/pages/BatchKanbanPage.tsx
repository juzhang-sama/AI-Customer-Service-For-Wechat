import React from 'react';
import BatchProcessingKanban from '../components/AIExpert/BatchProcessingKanban';

const BatchKanbanPage: React.FC = () => {
    return (
        <div className="max-w-7xl mx-auto py-6">
            <div className="mb-8">
                <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">批量处理看板</h1>
                <p className="mt-2 text-gray-600">汇总所有未回复客户，一键审阅并批量发放 AI 建议回复。</p>
            </div>

            <BatchProcessingKanban />
        </div>
    );
};

export default BatchKanbanPage;
