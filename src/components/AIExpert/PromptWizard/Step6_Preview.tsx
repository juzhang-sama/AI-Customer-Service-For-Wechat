import React, { useState, useEffect } from 'react';
import { PromptConfig } from './WizardContainer';

interface Step6Props {
  config: PromptConfig;
  onSave: () => void;
  onPrev: () => void;
}

export const Step6_Preview: React.FC<Step6Props> = ({
  config,
  onSave,
  onPrev
}) => {
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    generatePreview();
  }, []);

  const generatePreview = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/ai/prompts/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      if (data.success) {
        setSystemPrompt(data.system_prompt);
      } else {
        console.error('Preview failed:', data.error);
        setSystemPrompt('预览生成失败：' + (data.error || '未知错误'));
      }
    } catch (error) {
      console.error('Failed to generate preview:', error);
      setSystemPrompt('预览生成失败：网络连接错误');
    } finally {
      setIsLoading(false);
    }
  };

  // 获取预设问答显示内容
  const getPresetQADisplay = () => {
    if (!config.preset_qa || config.preset_qa.length === 0) {
      return '无内容';
    }
    return config.preset_qa.map((qa: any) => {
      const patterns = qa.question_patterns || (qa.question_pattern ? [qa.question_pattern] : []);
      return patterns.join('、');
    }).join('；');
  };

  // 获取关键词规则显示内容
  const getKeywordsDisplay = () => {
    if (!config.keywords || config.keywords.length === 0) {
      return '无内容';
    }
    return config.keywords.map((k: any) => k.keyword).join('、');
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 7: 预览与保存</h2>
        <p className="text-gray-600 text-sm">查看配置摘要和生成的 System Prompt</p>
      </div>

      {/* 配置摘要 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-3 text-sm">📋 配置摘要</h3>
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div>
            <span className="text-gray-600">配置名称：</span>
            <span className="font-medium">{config.name || '未命名'}</span>
          </div>
          <div>
            <span className="text-gray-600">语气风格：</span>
            <span className="font-medium">
              {config.tone_style === 'professional' && '专业正式'}
              {config.tone_style === 'friendly' && '亲切热情'}
              {config.tone_style === 'casual' && '轻松口语'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">回复长度：</span>
            <span className="font-medium">
              {config.reply_length === 'short' && '简短'}
              {config.reply_length === 'medium' && '适中'}
              {config.reply_length === 'long' && '详细'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Emoji使用：</span>
            <span className="font-medium">
              {config.emoji_usage === 'none' && '不使用'}
              {config.emoji_usage === 'occasional' && '偶尔使用'}
              {config.emoji_usage === 'frequent' && '经常使用'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">知识库条目：</span>
            <span className="font-medium">{config.knowledge_base.length} 个</span>
          </div>
          <div>
            <span className="text-gray-600">禁忌词：</span>
            <span className="font-medium">{config.forbidden_words.length > 0 ? `${config.forbidden_words.length} 个` : '无内容'}</span>
          </div>
          <div className="col-span-2">
            <span className="text-gray-600">关键词规则：</span>
            <span className="font-medium">{getKeywordsDisplay()}</span>
          </div>
          <div className="col-span-2">
            <span className="text-gray-600">预设问答：</span>
            <span className="font-medium">{getPresetQADisplay()}</span>
          </div>
        </div>
      </div>

      {/* System Prompt 预览 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          生成的 System Prompt
        </label>
        {isLoading ? (
          <div className="border border-gray-200 rounded-lg p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500 text-sm">正在生成...</p>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-lg p-3 bg-gray-50 max-h-48 overflow-y-auto">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
              {systemPrompt || '暂无预览'}
            </pre>
          </div>
        )}
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <h3 className="font-semibold text-green-900 mb-1 text-sm">✅ 准备就绪</h3>
        <p className="text-xs text-green-800">
          配置完成后，点击"保存配置"即可开始使用 AI 助手。您可以随时回来修改配置。
        </p>
      </div>

      <div className="flex justify-between pt-2">
        <button
          onClick={onPrev}
          className="px-4 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          上一步
        </button>
        <button
          onClick={onSave}
          disabled={isLoading}
          className="px-6 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          💾 保存配置
        </button>
      </div>
    </div>
  );
};

