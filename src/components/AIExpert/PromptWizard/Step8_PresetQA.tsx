import React, { useState } from 'react';
import { Plus, X, MessageCircle } from 'lucide-react';

interface PresetQA {
  question_patterns: string[];  // 改为数组，支持多个关键词
  answer: string;
  match_type: 'contains' | 'exact' | 'startswith';
  priority: number;
}

interface Step8Props {
  config: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step8_PresetQA: React.FC<Step8Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  // 兼容旧数据格式
  const initQaList = (config.preset_qa || []).map((qa: any) => ({
    ...qa,
    question_patterns: qa.question_patterns || (qa.question_pattern ? [qa.question_pattern] : [])
  }));

  const [qaList, setQaList] = useState<PresetQA[]>(initQaList);
  const [newKeywords, setNewKeywords] = useState<string[]>([]);
  const [currentKeyword, setCurrentKeyword] = useState('');
  const [newAnswer, setNewAnswer] = useState('');
  const [matchType, setMatchType] = useState<'contains' | 'exact' | 'startswith'>('contains');

  const handleAddKeyword = () => {
    if (!currentKeyword.trim()) return;
    if (!newKeywords.includes(currentKeyword.trim())) {
      setNewKeywords([...newKeywords, currentKeyword.trim()]);
    }
    setCurrentKeyword('');
  };

  const handleRemoveKeyword = (keyword: string) => {
    setNewKeywords(newKeywords.filter(k => k !== keyword));
  };

  const handleAddQA = () => {
    if (newKeywords.length === 0 || !newAnswer.trim()) return;

    const qa: PresetQA = {
      question_patterns: newKeywords,
      answer: newAnswer.trim(),
      match_type: matchType,
      priority: qaList.length
    };

    const updated = [...qaList, qa];
    setQaList(updated);
    onUpdate({ preset_qa: updated });
    setNewKeywords([]);
    setNewAnswer('');
  };

  const handleRemoveQA = (index: number) => {
    const updated = qaList.filter((_, i) => i !== index);
    setQaList(updated);
    onUpdate({ preset_qa: updated });
  };

  const handleNext = () => {
    onUpdate({ preset_qa: qaList });
    onNext();
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold mb-1">💬 预设问答</h2>
        <p className="text-gray-600 text-sm">
          为常见问题设置固定答案，匹配到时将直接返回预设答案（不消耗 AI Token）
        </p>
      </div>

      {/* 添加问答 */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            客户问题关键词（可添加多个）
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={currentKeyword}
              onChange={(e) => setCurrentKeyword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
              placeholder="输入关键词后按回车或点击添加"
              className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <button
              onClick={handleAddKeyword}
              disabled={!currentKeyword.trim()}
              className="px-3 py-1.5 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 disabled:opacity-50"
            >
              添加
            </button>
          </div>
          {newKeywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {newKeywords.map((keyword, idx) => (
                <span key={idx} className="inline-flex items-center px-2 py-0.5 bg-green-100 text-green-800 text-sm rounded-full">
                  {keyword}
                  <button onClick={() => handleRemoveKeyword(keyword)} className="ml-1 hover:text-green-600">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            预设回复内容
          </label>
          <textarea
            value={newAnswer}
            onChange={(e) => setNewAnswer(e.target.value)}
            placeholder="例如：我们的地址是XX市XX区XX路XX号"
            rows={2}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
          />
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={matchType}
            onChange={(e) => setMatchType(e.target.value as any)}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="contains">包含匹配（推荐）</option>
            <option value="startswith">开头匹配</option>
            <option value="exact">精确匹配</option>
          </select>
          <button
            onClick={handleAddQA}
            disabled={newKeywords.length === 0 || !newAnswer.trim()}
            className="px-4 py-1.5 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
          >
            <Plus className="w-4 h-4" />
            <span>添加问答</span>
          </button>
        </div>
      </div>

      {/* 问答列表 */}
      {qaList.length > 0 ? (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            已添加的预设问答 ({qaList.length})
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {qaList.map((qa, index) => (
              <div
                key={index}
                className="p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center flex-wrap gap-1">
                    <MessageCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                    {qa.question_patterns.map((pattern, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                        {pattern}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                      {qa.match_type === 'contains' && '包含'}
                      {qa.match_type === 'startswith' && '开头'}
                      {qa.match_type === 'exact' && '精确'}
                    </span>
                    <button
                      onClick={() => handleRemoveQA(index)}
                      className="p-1 hover:bg-red-50 rounded transition-colors"
                    >
                      <X className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 pl-5 whitespace-pre-wrap line-clamp-2">{qa.answer}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <MessageCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-gray-500 text-sm">还没有添加预设问答</p>
          <p className="text-xs text-gray-400">可选：添加常见问题的固定答案</p>
        </div>
      )}

      {/* 导航按钮 */}
      <div className="flex justify-between pt-4 border-t">
        <button
          onClick={onPrev}
          className="px-4 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          上一步
        </button>
        <button
          onClick={handleNext}
          className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          下一步
        </button>
      </div>
    </div>
  );
};

