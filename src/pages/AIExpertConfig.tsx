import React, { useState, useEffect } from 'react';
import { WizardContainer, PromptConfig } from '../components/AIExpert/PromptWizard/WizardContainer';
import { FavoriteReplies } from '../components/AIExpert/FavoriteReplies';
import { KnowledgeBaseManager } from '../components/AIExpert/KnowledgeBaseManager';

interface SavedPrompt extends PromptConfig {
  id: number;
  is_active: boolean;
  created_at: string;
}

type TabType = 'configs' | 'favorites' | 'knowledge';

// 辅助函数：转换英文值为中文显示
const getToneStyleLabel = (value: string | undefined): string => {
  const map: Record<string, string> = {
    'professional': '专业正式',
    'friendly': '亲切热情',
    'casual': '轻松口语'
  };
  return value ? (map[value] || value) : '无内容';
};

const getReplyLengthLabel = (value: string | undefined): string => {
  const map: Record<string, string> = {
    'short': '简短',
    'medium': '适中',
    'long': '详细'
  };
  return value ? (map[value] || value) : '无内容';
};

const getEmojiUsageLabel = (value: string | undefined): string => {
  const map: Record<string, string> = {
    'none': '不使用',
    'occasional': '偶尔使用',
    'frequent': '经常使用'
  };
  return value ? (map[value] || value) : '无内容';
};

const getMatchTypeLabel = (value: string | undefined): string => {
  const map: Record<string, string> = {
    'contains': '包含',
    'startswith': '开头',
    'exact': '精确'
  };
  return value ? (map[value] || value) : '';
};

export const AIExpertConfig: React.FC = () => {
  const [showWizard, setShowWizard] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<SavedPrompt | null>(null);
  const [prompts, setPrompts] = useState<SavedPrompt[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('configs');

  useEffect(() => {
    loadPrompts();
    checkConnection();
  }, []);

  const loadPrompts = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ai/prompts');
      const data = await response.json();
      if (data.success) {
        setPrompts(data.prompts);
      }
    } catch (error) {
      console.error('Failed to load prompts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkConnection = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/ai/config');
      const data = await response.json();
      // API Key 被隐藏为 ***xxxx 格式，只要不为空就认为已配置
      if (data.success && data.config && data.config.deepseek_api_key && data.config.deepseek_api_key.length > 0) {
        setIsConnected(true);
      } else {
        setIsConnected(false);
      }
    } catch (error) {
      console.error('Failed to check connection:', error);
      setIsConnected(false);
    }
  };

  const handleSavePrompt = async (config: PromptConfig) => {
    try {
      // 判断是新建还是编辑
      const isEditing = editingPrompt !== null;

      // 1. 如果是新建，先创建基础 Prompt 获取 ID
      let promptId = isEditing ? editingPrompt.id : null;

      if (!isEditing) {
        const createRes = await fetch('http://localhost:5000/api/ai/prompts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        });
        const createData = await createRes.json();
        if (createData.success) {
          promptId = createData.prompt_id;
        } else {
          alert('创建失败：' + createData.error);
          return;
        }
      }

      // 2. 调用全量更新接口（不管是新建还是编辑，后续流程一致）
      // 这一步会原子化地保存 Prompt、Keywords 和 Preset QA，避免网络延迟导致的冗余
      const updateUrl = `http://localhost:5000/api/ai/prompts/${promptId}/full-update`;
      const response = await fetch(updateUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();
      if (data.success) {
        alert(isEditing ? '配置更新成功！' : '配置保存成功！');
        setShowWizard(false);
        setEditingPrompt(null);
        await loadPrompts(); // 刷新列表
      } else {
        alert('保存失败：' + data.error);
      }
    } catch (error) {
      console.error('Failed to save prompt:', error);
      alert('保存失败，请检查网络连接');
    }
  };

  const handleEditPrompt = async (prompt: SavedPrompt) => {
    // 加载关键词和预设问答
    try {
      const [keywordsRes, qaRes] = await Promise.all([
        fetch(`http://localhost:5000/api/ai/keywords?prompt_id=${prompt.id}`),
        fetch(`http://localhost:5000/api/ai/preset-qa?prompt_id=${prompt.id}`)
      ]);

      const keywordsData = await keywordsRes.json();
      const qaData = await qaRes.json();

      // 合并数据（修正字段名：keywords <- rules, preset_qa <- qa_list）
      const fullPrompt = {
        ...prompt,
        keywords: keywordsData.success ? keywordsData.keywords : [], // 关键修复：rules -> keywords
        preset_qa: qaData.success ? qaData.qa_list.map((qa: any) => ({
          ...qa,
          // 兼容新格式：将单个 question_pattern 转换为 question_patterns 数组
          question_patterns: qa.question_pattern ? [qa.question_pattern] : [],
          // 保留原字段以防万一
          question_pattern: qa.question_pattern
        })) : []
      };

      setEditingPrompt(fullPrompt);
      setShowWizard(true);
    } catch (error) {
      console.error('Failed to load prompt details:', error);
      alert('加载配置失败');
    }
  };

  const handleDeletePrompt = async (promptId: number) => {
    if (!confirm('确定要删除这个配置吗？')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/api/ai/prompts/${promptId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        loadPrompts();
      }
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    }
  };

  if (showWizard) {
    return (
      <WizardContainer
        initialConfig={editingPrompt || undefined}
        onSave={handleSavePrompt}
        onCancel={() => {
          setShowWizard(false);
          setEditingPrompt(null);
        }}
      />
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">AI 专家配置</h1>
            <p className="text-gray-600 text-sm">配置 AI 销售助手的行业知识和话术风格</p>
          </div>
          {/* DeepSeek 连接指示灯 */}
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow border border-gray-200">
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm font-medium text-gray-700">
              DeepSeek {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
      </div>

      {/* 标签页 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <div className="flex space-x-6 px-4">
            <button
              onClick={() => setActiveTab('configs')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${activeTab === 'configs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              📋 我的配置
            </button>
            <button
              onClick={() => setActiveTab('favorites')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${activeTab === 'favorites'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              ⭐ 收藏话术
            </button>
            <button
              onClick={() => setActiveTab('knowledge')}
              className={`py-3 px-2 border-b-2 font-medium text-sm transition-colors ${activeTab === 'knowledge'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
            >
              📚 知识库管理
            </button>
          </div>
        </div>

        <div className="p-4">
          {activeTab === 'configs' ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">配置管理</h2>
                <button
                  onClick={() => setShowWizard(true)}
                  className="px-4 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  + 新建配置
                </button>
              </div>

              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-3 text-gray-500 text-sm">加载中...</p>
                </div>
              ) : prompts.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 text-sm mb-3">还没有配置，点击上方按钮创建第一个配置</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {prompts.map((prompt) => (
                    <div
                      key={prompt.id}
                      className={`border rounded-lg p-4 ${prompt.is_active ? 'border-green-500 bg-green-50' : 'border-gray-200'
                        }`}
                    >
                      {/* 头部：标题和操作按钮 */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-0.5">
                            <h3 className="text-base font-bold text-gray-800">{prompt.name}</h3>
                            {prompt.is_active && (
                              <span className="px-2 py-0.5 bg-green-500 text-white text-xs font-medium rounded-full">使用中</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">创建：{new Date(prompt.created_at).toLocaleString()}</p>
                        </div>
                        <div className="flex gap-1.5">
                          <button onClick={() => handleEditPrompt(prompt)} className="px-3 py-1 text-xs border border-blue-300 text-blue-600 rounded hover:bg-blue-50">编辑</button>
                          <button onClick={() => handleDeletePrompt(prompt.id)} className="px-3 py-1 text-xs border border-red-300 text-red-600 rounded hover:bg-red-50">删除</button>
                        </div>
                      </div>

                      {/* 配置详情：紧凑布局 */}
                      <div className="grid grid-cols-12 gap-3 text-xs">
                        {/* 左侧：角色定义+业务逻辑 */}
                        <div className="col-span-4 space-y-2">
                          <div>
                            <label className="text-gray-500 block mb-0.5">角色定义</label>
                            <p className="text-gray-700 bg-white p-2 rounded border border-gray-200 line-clamp-2">{prompt.role_definition || '无内容'}</p>
                          </div>
                          <div>
                            <label className="text-gray-500 block mb-0.5">业务逻辑</label>
                            <p className="text-gray-700 bg-white p-2 rounded border border-gray-200 line-clamp-2">{prompt.business_logic || '无内容'}</p>
                          </div>
                        </div>

                        {/* 中间：风格设置+知识库 */}
                        <div className="col-span-4 space-y-2">
                          <div className="grid grid-cols-3 gap-1.5">
                            <div>
                              <label className="text-gray-500 block mb-0.5">语气风格</label>
                              <p className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-center">{getToneStyleLabel(prompt.tone_style)}</p>
                            </div>
                            <div>
                              <label className="text-gray-500 block mb-0.5">回复长度</label>
                              <p className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-center">{getReplyLengthLabel(prompt.reply_length)}</p>
                            </div>
                            <div>
                              <label className="text-gray-500 block mb-0.5">Emoji</label>
                              <p className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-center">{getEmojiUsageLabel(prompt.emoji_usage)}</p>
                            </div>
                          </div>
                          <div>
                            <label className="text-gray-500 block mb-0.5">知识库（{prompt.knowledge_base?.length || 0}条）</label>
                            <div className="bg-white border border-gray-200 rounded p-2 h-16 overflow-y-auto">
                              {Array.isArray(prompt.knowledge_base) && prompt.knowledge_base.length > 0 ? (
                                <ul className="space-y-1">
                                  {prompt.knowledge_base.slice(0, 3).map((kb: any, idx: number) => (
                                    <li key={idx} className="text-gray-600 truncate">📌 {kb.topic || '未命名'}</li>
                                  ))}
                                  {prompt.knowledge_base.length > 3 && <li className="text-gray-400">...还有 {prompt.knowledge_base.length - 3} 条</li>}
                                </ul>
                              ) : (<p className="text-gray-400">无内容</p>)}
                            </div>
                          </div>
                        </div>

                        {/* 右侧：禁忌词+关键词+预设问答 */}
                        <div className="col-span-4 space-y-2">
                          <div>
                            <label className="text-gray-500 block mb-0.5">禁忌词（{Array.isArray(prompt.forbidden_words) ? prompt.forbidden_words.length : 0}个）</label>
                            <div className="bg-white border border-gray-200 rounded p-2 h-10 overflow-y-auto">
                              {Array.isArray(prompt.forbidden_words) && prompt.forbidden_words.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {prompt.forbidden_words.slice(0, 5).map((word: string, idx: number) => (
                                    <span key={idx} className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded">{word}</span>
                                  ))}
                                  {prompt.forbidden_words.length > 5 && <span className="text-gray-400">+{prompt.forbidden_words.length - 5}</span>}
                                </div>
                              ) : (<p className="text-gray-400">无内容</p>)}
                            </div>
                          </div>
                          <div>
                            <label className="text-gray-500 block mb-0.5">关键词规则（{Array.isArray(prompt.keywords) ? prompt.keywords.length : 0}条）</label>
                            <div className="bg-white border border-gray-200 rounded p-2 h-10 overflow-y-auto">
                              {Array.isArray(prompt.keywords) && prompt.keywords.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {prompt.keywords.slice(0, 4).map((kw: any, idx: number) => (
                                    <span key={idx} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">{kw.keyword}</span>
                                  ))}
                                  {prompt.keywords.length > 4 && <span className="text-gray-400">+{prompt.keywords.length - 4}</span>}
                                </div>
                              ) : (<p className="text-gray-400">无内容</p>)}
                            </div>
                          </div>
                          <div>
                            <label className="text-gray-500 block mb-0.5">预设问答（{Array.isArray(prompt.preset_qa) ? prompt.preset_qa.length : 0}条）</label>
                            <div className="bg-white border border-gray-200 rounded p-2 h-10 overflow-y-auto">
                              {Array.isArray(prompt.preset_qa) && prompt.preset_qa.length > 0 ? (
                                <ul className="space-y-0.5">
                                  {prompt.preset_qa.slice(0, 2).map((qa: any, idx: number) => {
                                    const patterns = qa.question_patterns || (qa.question_pattern ? [qa.question_pattern] : []);
                                    return (<li key={idx} className="text-gray-600 truncate">Q: {patterns.join('、') || '—'}</li>);
                                  })}
                                  {prompt.preset_qa.length > 2 && <li className="text-gray-400">...还有 {prompt.preset_qa.length - 2} 条</li>}
                                </ul>
                              ) : (<p className="text-gray-400">无内容</p>)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : activeTab === 'favorites' ? (
            <FavoriteReplies />
          ) : (
            /* Knowledge Base Tab - Currently Global View (boundPromptId=0 or undefined, passing nothing shows all or handled by component logic to show global + maybe selector later? 
               For now let's pass nothing to show ALL documents, or pass 0 for global only?
               The component logic: if boundPromptId provided, filtered. If not, filtered by query param logic in API.
               Let's show a global manager for now.
            */
            <div className="space-y-6">
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">
                      这里管理的是<b>全局通用知识库</b>（如公司简介、产品手册）。<br />
                      这些资料所有 AI 专家都能查阅。如果想为特定专家上传“独家秘笈”，请去编辑该专家配置。
                    </p>
                  </div>
                </div>
              </div>
              <KnowledgeBaseManager boundPromptId={0} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

