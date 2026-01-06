import React, { useState } from 'react';
import { PromptConfig } from './WizardContainer';

interface Step3Props {
  config: PromptConfig;
  onUpdate: (updates: Partial<PromptConfig>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step3_ToneStyle: React.FC<Step3Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  const [toneStyle, setToneStyle] = useState(config.tone_style);
  const [replyLength, setReplyLength] = useState(config.reply_length);
  const [emojiUsage, setEmojiUsage] = useState(config.emoji_usage);

  const handleNext = () => {
    onUpdate({
      tone_style: toneStyle,
      reply_length: replyLength,
      emoji_usage: emojiUsage
    });
    onNext();
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 3: 话术风格</h2>
        <p className="text-gray-600 text-sm">设置回复的语气、长度和表情使用偏好</p>
      </div>

      {/* 语气风格 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">语气风格</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setToneStyle('professional')}
            className={`p-3 border-2 rounded-lg transition-all ${
              toneStyle === 'professional'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-xl mb-1">🎓</div>
            <div className="font-semibold text-sm">专业正式</div>
            <div className="text-xs text-gray-500">适合B2B、高端服务</div>
          </button>
          <button
            onClick={() => setToneStyle('friendly')}
            className={`p-3 border-2 rounded-lg transition-all ${
              toneStyle === 'friendly'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-xl mb-1">😊</div>
            <div className="font-semibold text-sm">亲切热情</div>
            <div className="text-xs text-gray-500">适合零售、服务业</div>
          </button>
          <button
            onClick={() => setToneStyle('casual')}
            className={`p-3 border-2 rounded-lg transition-all ${
              toneStyle === 'casual'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-xl mb-1">💬</div>
            <div className="font-semibold text-sm">轻松口语</div>
            <div className="text-xs text-gray-500">适合年轻客群</div>
          </button>
        </div>
      </div>

      {/* 回复长度 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">回复长度</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setReplyLength('short')}
            className={`p-2 border-2 rounded-lg transition-all ${
              replyLength === 'short'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">简短</div>
            <div className="text-xs text-gray-500">&lt; 50字</div>
          </button>
          <button
            onClick={() => setReplyLength('medium')}
            className={`p-2 border-2 rounded-lg transition-all ${
              replyLength === 'medium'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">适中</div>
            <div className="text-xs text-gray-500">50-150字</div>
          </button>
          <button
            onClick={() => setReplyLength('long')}
            className={`p-2 border-2 rounded-lg transition-all ${
              replyLength === 'long'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">详细</div>
            <div className="text-xs text-gray-500">&gt; 150字</div>
          </button>
        </div>
      </div>

      {/* Emoji 使用 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Emoji 使用</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setEmojiUsage('none')}
            className={`p-2 border-2 rounded-lg transition-all ${
              emojiUsage === 'none'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">不使用</div>
          </button>
          <button
            onClick={() => setEmojiUsage('occasional')}
            className={`p-2 border-2 rounded-lg transition-all ${
              emojiUsage === 'occasional'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">偶尔使用</div>
          </button>
          <button
            onClick={() => setEmojiUsage('frequent')}
            className={`p-2 border-2 rounded-lg transition-all ${
              emojiUsage === 'frequent'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-sm">经常使用</div>
          </button>
        </div>
      </div>

      <div className="flex justify-between pt-2">
        <button
          onClick={onPrev}
          className="px-4 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          上一步
        </button>
        <button
          onClick={handleNext}
          className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          下一步
        </button>
      </div>
    </div>
  );
};

