import React, { useState } from 'react';
import { PromptConfig } from './WizardContainer';

interface Step1Props {
  config: PromptConfig;
  onUpdate: (updates: Partial<PromptConfig>) => void;
  onNext: () => void;
}

export const Step1_RoleDefinition: React.FC<Step1Props> = ({
  config,
  onUpdate,
  onNext
}) => {
  const [name, setName] = useState(config.name);
  const [roleDefinition, setRoleDefinition] = useState(config.role_definition);

  const handleNext = () => {
    if (!name.trim()) {
      alert('请输入配置名称');
      return;
    }
    
    onUpdate({
      name: name.trim(),
      role_definition: roleDefinition.trim()
    });
    onNext();
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold mb-1">步骤 1: 角色定义</h2>
        <p className="text-gray-600 text-sm">定义 AI 助手的角色和性格特点</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          配置名称 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：医美行业-小王"
          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-0.5 text-xs text-gray-500">给这个配置起一个容易识别的名称</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">角色描述</label>
        <textarea
          value={roleDefinition}
          onChange={(e) => setRoleDefinition(e.target.value)}
          placeholder="例如：你是一位专业的医美咨询顾问，拥有丰富的皮肤管理和医美项目经验..."
          rows={4}
          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-0.5 text-xs text-gray-500">描述 AI 的职业角色、专业背景和职责</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <h3 className="font-semibold text-blue-900 mb-1 text-sm">💡 提示</h3>
        <ul className="text-xs text-blue-800 space-y-0.5">
          <li>• 角色定义越具体，AI 的回复越专业</li>
          <li>• 可以包含职级、性格特点、专业领域等</li>
          <li>• 例如："资深顾问"、"热情店长"、"专业客服"</li>
        </ul>
      </div>

      <div className="flex justify-end pt-2">
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

