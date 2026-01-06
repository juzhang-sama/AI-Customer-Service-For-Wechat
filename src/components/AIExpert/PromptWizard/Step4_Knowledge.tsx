import React, { useState } from 'react';
import { PromptConfig } from './WizardContainer';
import { KnowledgeBaseManager } from '../KnowledgeBaseManager';

interface Step4Props {
  config: PromptConfig;
  onUpdate: (updates: Partial<PromptConfig>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step4_Knowledge: React.FC<Step4Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  const [knowledgeBase, setKnowledgeBase] = useState(config.knowledge_base);
  const [currentTopic, setCurrentTopic] = useState('');
  const [currentPoints, setCurrentPoints] = useState('');

  const handleAddKnowledge = () => {
    if (!currentTopic.trim()) {
      alert('请输入主题');
      return;
    }

    const points = currentPoints
      .split('\n')
      .map(p => p.trim())
      .filter(p => p.length > 0);

    if (points.length === 0) {
      alert('请至少添加一个要点');
      return;
    }

    const newKnowledge = {
      topic: currentTopic.trim(),
      points: points
    };

    setKnowledgeBase([...knowledgeBase, newKnowledge]);
    setCurrentTopic('');
    setCurrentPoints('');
  };

  const handleRemoveKnowledge = (index: number) => {
    const updated = knowledgeBase.filter((_, i) => i !== index);
    setKnowledgeBase(updated);
  };

  const handleNext = () => {
    onUpdate({
      knowledge_base: knowledgeBase
    });
    onNext();
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 4: 知识库</h2>
        <p className="text-gray-600 text-sm">添加产品/服务的核心信息和常见问题</p>
      </div>

      {/* 已添加的知识 */}
      {knowledgeBase.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            已添加的知识 ({knowledgeBase.length})
          </label>
          <div className="max-h-32 overflow-y-auto space-y-2">
            {knowledgeBase.map((kb, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-2 bg-gray-50">
                <div className="flex justify-between items-start mb-1">
                  <h4 className="font-semibold text-gray-900 text-sm">{kb.topic}</h4>
                  <button onClick={() => handleRemoveKnowledge(index)} className="text-red-500 hover:text-red-700 text-xs">删除</button>
                </div>
                <ul className="list-disc list-inside text-xs text-gray-600 space-y-0.5">
                  {kb.points.slice(0, 3).map((point, i) => (<li key={i}>{point}</li>))}
                  {kb.points.length > 3 && <li className="text-gray-400">...还有 {kb.points.length - 3} 条</li>}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 添加新知识 */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-3">
        <h3 className="font-semibold mb-2 text-sm">添加新知识</h3>
        <div className="space-y-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">主题/产品名称</label>
            <input
              type="text"
              value={currentTopic}
              onChange={(e) => setCurrentTopic(e.target.value)}
              placeholder="例如：热玛吉"
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">核心要点（每行一个）</label>
            <textarea
              value={currentPoints}
              onChange={(e) => setCurrentPoints(e.target.value)}
              placeholder="紧致提升，改善面部松弛&#10;无创无恢复期，即做即走&#10;效果可持续1-2年"
              rows={3}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleAddKnowledge}
            className="w-full px-3 py-1.5 text-sm border-2 border-blue-500 text-blue-500 rounded-lg hover:bg-blue-50 transition-colors"
          >
            + 添加知识
          </button>
        </div>
      </div>

      {/* RAG 文档上传/管理 */}
      <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
        <h3 className="font-semibold mb-2 text-sm">专家知识库文档 (PDF/Word)</h3>
        {config.id ? (
          <KnowledgeBaseManager boundPromptId={config.id} />
        ) : (
          <div className="text-center py-4 bg-white border border-dashed border-gray-300 rounded text-gray-500 text-sm">
            请先保存此 AI 专家配置，再上传专属知识文档。
          </div>
        )}
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <h3 className="font-semibold text-yellow-900 mb-1 text-sm">💡 提示</h3>
        <ul className="text-xs text-yellow-800 space-y-0.5">
          <li>• 建议添加 3-10 个核心产品/服务的信息</li>
          <li>• 每个主题包含 3-5 个关键要点</li>
        </ul>
      </div>

      <div className="flex justify-between pt-2">
        <button onClick={onPrev} className="px-4 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">上一步</button>
        <button onClick={handleNext} className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">下一步</button>
      </div>
    </div>
  );
};

