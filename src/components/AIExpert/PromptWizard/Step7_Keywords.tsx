import React, { useState } from 'react';
import { Plus, X, Tag } from 'lucide-react';

interface Keyword {
  keyword: string;
  match_type: 'startswith' | 'contains' | 'exact';
  priority: number;
}

interface Step7Props {
  config: any;
  onUpdate: (updates: any) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step7_Keywords: React.FC<Step7Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  const [keywords, setKeywords] = useState<Keyword[]>(config.keywords || []);
  const [newKeyword, setNewKeyword] = useState('');
  const [matchType, setMatchType] = useState<'startswith' | 'contains' | 'exact'>('startswith');

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) return;

    const keyword: Keyword = {
      keyword: newKeyword.trim(),
      match_type: matchType,
      priority: keywords.length
    };

    const updated = [...keywords, keyword];
    setKeywords(updated);
    onUpdate({ keywords: updated });
    setNewKeyword('');
  };

  const handleRemoveKeyword = (index: number) => {
    const updated = keywords.filter((_, i) => i !== index);
    setKeywords(updated);
    onUpdate({ keywords: updated });
  };

  const handleNext = () => {
    onUpdate({ keywords });
    onNext();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">🔑 关键词匹配规则</h2>
        <p className="text-gray-600">
          设置微信会话名称的匹配关键词，只有匹配的会话才会使用此 AI 专家
        </p>
      </div>

      {/* 添加关键词 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          添加关键词
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
            placeholder="例如：客户、VIP、重要"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={matchType}
            onChange={(e) => setMatchType(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="startswith">开头匹配</option>
            <option value="contains">包含匹配</option>
            <option value="exact">精确匹配</option>
          </select>
          <button
            onClick={handleAddKeyword}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-1"
          >
            <Plus className="w-4 h-4" />
            <span>添加</span>
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          💡 开头匹配：会话名以关键词开头 | 包含匹配：会话名包含关键词 | 精确匹配：会话名完全相同
        </p>
      </div>

      {/* 关键词列表 */}
      {keywords.length > 0 ? (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            已添加的关键词 ({keywords.length})
          </label>
          <div className="space-y-2">
            {keywords.map((kw, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center space-x-3">
                  <Tag className="w-4 h-4 text-blue-500" />
                  <span className="font-medium">{kw.keyword}</span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    {kw.match_type === 'startswith' && '开头匹配'}
                    {kw.match_type === 'contains' && '包含匹配'}
                    {kw.match_type === 'exact' && '精确匹配'}
                  </span>
                </div>
                <button
                  onClick={() => handleRemoveKeyword(index)}
                  className="p-1 hover:bg-red-50 rounded transition-colors"
                >
                  <X className="w-4 h-4 text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Tag className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p className="text-gray-500">还没有添加关键词</p>
          <p className="text-sm text-gray-400 mt-1">添加至少一个关键词来匹配微信会话</p>
        </div>
      )}

      {/* 导航按钮 */}
      <div className="flex justify-between pt-6 border-t">
        <button
          onClick={onPrev}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          上一步
        </button>
        <button
          onClick={handleNext}
          disabled={keywords.length === 0}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一步
        </button>
      </div>
    </div>
  );
};

