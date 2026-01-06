import React, { useState } from 'react';
import { Step1_RoleDefinition } from './Step1_RoleDefinition';
import { Step2_BusinessLogic } from './Step2_BusinessLogic';
import { Step3_ToneStyle } from './Step3_ToneStyle';
import { Step4_Knowledge } from './Step4_Knowledge';
import { Step5_Forbidden } from './Step5_Forbidden';
import { Step6_Preview } from './Step6_Preview';
import { Step8_PresetQA } from './Step8_PresetQA';
import { StepIndicator } from './StepIndicator';


export interface PromptConfig {
  id?: number;
  name: string;
  role_definition: string;
  business_logic: string;
  tone_style: string;
  reply_length: string;
  emoji_usage: string;
  knowledge_base: Array<{ topic: string; points: string[] }>;
  forbidden_words: string[];
  keywords?: Array<{ keyword: string; match_type: string; priority: number }>;
  preset_qa?: Array<{ question_patterns?: string[]; question_pattern?: string; answer: string; match_type: string; priority: number }>;
}

interface WizardContainerProps {
  onSave: (config: PromptConfig) => void;
  onCancel: () => void;
  initialConfig?: Partial<PromptConfig>;
}

export const WizardContainer: React.FC<WizardContainerProps> = ({
  onSave,
  onCancel,
  initialConfig
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  // 判断是否为编辑模式（如果有初始配置名称则为编辑模式）
  const isEditMode = !!(initialConfig?.name);

  const [config, setConfig] = useState<PromptConfig>({
    id: initialConfig?.id,
    name: initialConfig?.name || '',
    role_definition: initialConfig?.role_definition || '',
    business_logic: initialConfig?.business_logic || '',
    tone_style: initialConfig?.tone_style || 'professional',
    reply_length: initialConfig?.reply_length || 'medium',
    emoji_usage: initialConfig?.emoji_usage || 'occasional',
    knowledge_base: initialConfig?.knowledge_base || [],
    forbidden_words: initialConfig?.forbidden_words || [],
    keywords: initialConfig?.keywords || [],
    preset_qa: initialConfig?.preset_qa || []
  });

  const totalSteps = 7;

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (step: number) => {
    setCurrentStep(step);
  };

  const handleUpdateConfig = (updates: Partial<PromptConfig>) => {
    setConfig({ ...config, ...updates });
  };

  const handleSave = () => {
    onSave(config);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1_RoleDefinition
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
          />
        );
      case 2:
        return (
          <Step2_BusinessLogic
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        );
      case 3:
        return (
          <Step3_ToneStyle
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        );
      case 4:
        return (
          <Step4_Knowledge
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        );
      case 5:
        return (
          <Step5_Forbidden
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        );
      case 6:
        return (
          <Step8_PresetQA
            config={config}
            onUpdate={handleUpdateConfig}
            onNext={handleNext}
            onPrev={handlePrev}
          />
        );
      case 7:
        return (
          <Step6_Preview
            config={config}
            onSave={handleSave}
            onPrev={handlePrev}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="bg-white rounded-lg shadow-lg p-5">
        <h1 className="text-xl font-bold mb-4">AI 专家配置向导</h1>

        <StepIndicator
          currentStep={currentStep}
          totalSteps={totalSteps}
          onStepClick={handleStepClick}
          isEditMode={isEditMode}
        />

        <div className="mt-5">
          {renderStep()}
        </div>

        <div className="mt-4 flex justify-between">
          <button
            onClick={onCancel}
            className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-800"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  );
};

