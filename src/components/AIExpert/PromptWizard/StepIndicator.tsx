import React from 'react';

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  onStepClick?: (step: number) => void;
  isEditMode?: boolean;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  onStepClick,
  isEditMode = false
}) => {
  const steps = [
    { number: 1, title: '角色定义' },
    { number: 2, title: '业务逻辑' },
    { number: 3, title: '话术风格' },
    { number: 4, title: '知识库' },
    { number: 5, title: '禁忌词' },
    { number: 6, title: '预设问答' },
    { number: 7, title: '预览保存' }
  ];

  const handleStepClick = (stepNumber: number) => {
    // 编辑模式下可以跳转到任意步骤
    // 新建模式下只能跳转到已完成的步骤
    if (isEditMode || stepNumber <= currentStep) {
      onStepClick?.(stepNumber);
    }
  };

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <React.Fragment key={step.number}>
          <div
            className={`flex flex-col items-center ${
              (isEditMode || step.number <= currentStep) ? 'cursor-pointer' : 'cursor-default'
            }`}
            onClick={() => handleStepClick(step.number)}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                step.number === currentStep
                  ? 'bg-blue-500 text-white ring-2 ring-blue-200'
                  : step.number < currentStep
                    ? 'bg-green-500 text-white hover:bg-green-600'
                    : isEditMode
                      ? 'bg-gray-200 text-gray-500 hover:bg-gray-300'
                      : 'bg-gray-200 text-gray-500'
              }`}
            >
              {step.number < currentStep ? '✓' : step.number}
            </div>
            <div
              className={`mt-1 text-xs ${
                step.number === currentStep
                  ? 'text-blue-500 font-semibold'
                  : step.number < currentStep
                    ? 'text-green-500'
                    : 'text-gray-400'
              }`}
            >
              {step.title}
            </div>
          </div>

          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-0.5 mx-1 ${step.number < currentStep ? 'bg-green-500' : 'bg-gray-200'}`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

