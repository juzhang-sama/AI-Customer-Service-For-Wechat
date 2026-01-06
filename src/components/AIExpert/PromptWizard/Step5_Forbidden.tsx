import React, { useState } from 'react';
import { PromptConfig } from './WizardContainer';

interface Step5Props {
  config: PromptConfig;
  onUpdate: (updates: Partial<PromptConfig>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step5_Forbidden: React.FC<Step5Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  const [forbiddenWords, setForbiddenWords] = useState(config.forbidden_words);
  const [inputValue, setInputValue] = useState('');

  const commonForbidden = [
    '保证', '一定', '绝对', '永久', '治疗', '治愈',
    '最好', '第一', '独家', '秘方', '神效'
  ];

  const handleAddWord = () => {
    const word = inputValue.trim();
    if (word && !forbiddenWords.includes(word)) {
      setForbiddenWords([...forbiddenWords, word]);
      setInputValue('');
    }
  };

  const handleRemoveWord = (word: string) => {
    setForbiddenWords(forbiddenWords.filter(w => w !== word));
  };

  const handleAddCommon = (word: string) => {
    if (!forbiddenWords.includes(word)) {
      setForbiddenWords([...forbiddenWords, word]);
    }
  };

  const handleNext = () => {
    onUpdate({
      forbidden_words: forbiddenWords
    });
    onNext();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddWord();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 5: 禁忌词</h2>
        <p className="text-gray-600 text-sm">设置严禁在回复中出现的词汇和内容</p>
      </div>

      {/* 常用禁忌词 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">常用禁忌词（点击添加）</label>
        <div className="flex flex-wrap gap-1.5">
          {commonForbidden.map((word) => (
            <button
              key={word}
              onClick={() => handleAddCommon(word)}
              disabled={forbiddenWords.includes(word)}
              className={`px-2 py-0.5 rounded-full text-xs transition-colors ${
                forbiddenWords.includes(word)
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-red-100 text-red-700 hover:bg-red-200'
              }`}
            >
              {word}
            </button>
          ))}
        </div>
      </div>

      {/* 自定义添加 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">自定义禁忌词</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入禁忌词，按回车添加"
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button onClick={handleAddWord} className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">添加</button>
        </div>
      </div>

      {/* 已添加的禁忌词 */}
      {forbiddenWords.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">已添加的禁忌词 ({forbiddenWords.length})</label>
          <div className="border border-gray-200 rounded-lg p-2 bg-gray-50 max-h-24 overflow-y-auto">
            <div className="flex flex-wrap gap-1.5">
              {forbiddenWords.map((word) => (
                <div key={word} className="flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                  <span className="text-xs">{word}</span>
                  <button onClick={() => handleRemoveWord(word)} className="text-red-500 hover:text-red-700 text-sm">×</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
        <h3 className="font-semibold text-red-900 mb-1 text-sm">⚠️ 重要提示</h3>
        <ul className="text-xs text-red-800 space-y-0.5">
          <li>• 禁忌词会严格过滤，AI 不会在回复中使用这些词汇</li>
          <li>• 建议添加可能引起法律风险的词汇（如医疗承诺、绝对化用语）</li>
        </ul>
      </div>

      <div className="flex justify-between pt-2">
        <button onClick={onPrev} className="px-4 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">上一步</button>
        <button onClick={handleNext} className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">下一步</button>
      </div>
    </div>
  );
};

