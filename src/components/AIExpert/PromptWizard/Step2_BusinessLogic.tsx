import React, { useState } from 'react';
import { PromptConfig } from './WizardContainer';

interface Step2Props {
  config: PromptConfig;
  onUpdate: (updates: Partial<PromptConfig>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step2_BusinessLogic: React.FC<Step2Props> = ({
  config,
  onUpdate,
  onNext,
  onPrev
}) => {
  const [businessLogic, setBusinessLogic] = useState(config.business_logic);

  const handleNext = () => {
    onUpdate({
      business_logic: businessLogic.trim()
    });
    onNext();
  };

  const presetGoals = [
    { id: 'get_phone', label: '获取电话号码', icon: '📞' },
    { id: 'collect_info', label: '收集资料', icon: '📝' },
    { id: 'close_deal', label: '促成交易', icon: '💰' },
    { id: 'repurchase', label: '促进复购', icon: '🔄' },
    { id: 'referral', label: '转介绍', icon: '🌟' }
  ];

  const handlePresetClick = (goal: string) => {
    const currentText = businessLogic;
    const newText = currentText
      ? `${currentText}\n- ${goal}`
      : `主要目标：\n- ${goal}`;
    setBusinessLogic(newText);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 2: 业务逻辑</h2>
        <p className="text-gray-600 text-sm">定义销售目标和业务策略</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">快速选择目标</label>
        <div className="grid grid-cols-5 gap-2">
          {presetGoals.map((goal) => (
            <button
              key={goal.id}
              onClick={() => handlePresetClick(goal.label)}
              className="px-2 py-2 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-center"
            >
              <span className="text-xl">{goal.icon}</span>
              <span className="block text-xs font-medium mt-0.5">{goal.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">业务目标和策略</label>
        <textarea
          value={businessLogic}
          onChange={(e) => setBusinessLogic(e.target.value)}
          placeholder="例如：主要目标是建立信任、了解客户需求、推荐合适的产品、促成到店体验..."
          rows={4}
          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-0.5 text-xs text-gray-500">描述销售流程中的关键目标和策略</p>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <h3 className="font-semibold text-green-900 mb-1 text-sm">💡 建议</h3>
        <ul className="text-xs text-green-800 space-y-0.5">
          <li>• 明确每个阶段的目标（初次接触、了解需求、促成交易）</li>
          <li>• 定义优先级策略（快速响应 vs 深度沟通）</li>
          <li>• 考虑客户生命周期（新客户、老客户、VIP客户）</li>
        </ul>
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

