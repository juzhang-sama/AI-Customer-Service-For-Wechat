# -*- coding: utf-8 -*-
"""
AI Expert API
AI 专家模块的 Flask API 路由
"""

from flask import Blueprint, request, jsonify
from ai_expert.database import AIExpertDatabase
from ai_expert.prompt_builder import PromptBuilder
from ai_expert.reply_generator import ReplyGenerator
from ai_expert.enhanced_reply_generator import EnhancedReplyGenerator
from ai_expert.deepseek_adapter import DeepSeekAdapter
from ai_expert.template_loader import TemplateLoader
from ai_expert.knowledge_base_manager import KnowledgeBaseManager
import json
import os

# 创建 Blueprint
ai_expert_bp = Blueprint('ai_expert', __name__, url_prefix='/api/ai')

# 初始化数据库
db = AIExpertDatabase()

# 初始化 Prompt Builder
prompt_builder = PromptBuilder()

# 初始化 Template Loader
template_loader = TemplateLoader()

# 初始化 RAG Knowledge Base Manager (全局单例，避免重复加载模型)
kb_manager = KnowledgeBaseManager()


# API Key 管理（从配置文件读取）
def get_api_key():
    """获取 DeepSeek API Key"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('deepseek_api_key', '')
    
    return ''

# ========== 配置管理模块已合并到下方 [配置管理 API] 区域 ==========

# ========== AI 专家配置管理 API ==========

@ai_expert_bp.route('/prompts/preview', methods=['POST'])
def preview_prompt():
    """预览提示词配置（不保存到数据库）"""
    try:
        data = request.json

        # 仅生成 System Prompt，不保存
        system_prompt = prompt_builder.build_system_prompt(data)

        return jsonify({
            'success': True,
            'system_prompt': system_prompt
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts', methods=['POST'])
def create_prompt():
    """创建新的提示词配置"""
    try:
        data = request.json

        # 生成 System Prompt
        system_prompt = prompt_builder.build_system_prompt(data)
        data['system_prompt'] = system_prompt

        # 保存到数据库
        prompt_id = db.create_prompt(data)

        return jsonify({
            'success': True,
            'prompt_id': prompt_id,
            'system_prompt': system_prompt
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts', methods=['GET'])
def get_prompts():
    """获取所有配置"""
    try:
        prompts = db.get_all_prompts()
        print(f"[DEBUG] 获取 {len(prompts)} 个配置")
        
        # 解析 JSON 字段并获取关键词规则和预设问答
        for prompt in prompts:
            # 解析 JSON 字段
            if prompt.get('knowledge_base'):
                prompt['knowledge_base'] = json.loads(prompt['knowledge_base'])
            if prompt.get('forbidden_words'):
                prompt['forbidden_words'] = json.loads(prompt['forbidden_words'])
            
            # 获取关键词规则
            try:
                keywords = db.get_keyword_rules(prompt['id'])
                prompt['keywords'] = keywords if keywords else []
                print(f"[DEBUG] {prompt['name']} - keywords: {len(prompt['keywords'])}")
            except Exception as kw_err:
                print(f"[DEBUG] {prompt['name']} - keywords 错误: {kw_err}")
                prompt['keywords'] = []
            
            # 获取预设问答
            try:
                preset_qa = db.get_preset_qa(prompt['id'])
                prompt['preset_qa'] = preset_qa if preset_qa else []
                print(f"[DEBUG] {prompt['name']} - preset_qa: {len(prompt['preset_qa'])}")
            except Exception as qa_err:
                print(f"[DEBUG] {prompt['name']} - preset_qa 错误: {qa_err}")
                prompt['preset_qa'] = []
        
        print(f"[DEBUG] 返回 {len(prompts)} 个增强的配置")
        return jsonify({
            'success': True,
            'prompts': prompts
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts/<int:prompt_id>', methods=['GET'])
def get_prompt(prompt_id):
    """获取单个配置"""
    try:
        prompts = db.get_all_prompts()
        prompt = next((p for p in prompts if p['id'] == prompt_id), None)
        
        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404
        
        # 解析 JSON 字段
        if prompt.get('knowledge_base'):
            prompt['knowledge_base'] = json.loads(prompt['knowledge_base'])
        if prompt.get('forbidden_words'):
            prompt['forbidden_words'] = json.loads(prompt['forbidden_words'])
        
        return jsonify({
            'success': True,
            'prompt': prompt
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """更新提示词配置"""
    try:
        data = request.json

        # 生成 System Prompt
        system_prompt = prompt_builder.build_system_prompt(data)
        data['system_prompt'] = system_prompt

        # 更新数据库
        db.update_prompt(prompt_id, data)

        return jsonify({
            'success': True,
            'prompt_id': prompt_id,
            'system_prompt': system_prompt
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts/<int:prompt_id>/activate', methods=['POST'])
def activate_prompt(prompt_id):
    """激活配置"""
    try:
        db.activate_prompt(prompt_id)

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """删除配置"""
    try:
        db.delete_prompt(prompt_id)
        
        return jsonify({
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== AI 生成 API ==========

@ai_expert_bp.route('/generate', methods=['POST'])
def generate_reply():
    """生成 AI 回复建议"""
    try:
        data = request.json
        session_id = data.get('session_id')
        customer_message = data.get('customer_message')
        conversation_history = data.get('conversation_history', [])  # 可选的会话历史
        prompt_id = data.get('prompt_id')  # 用户选择的 AI 专家 ID

        if not session_id or not customer_message:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: session_id and customer_message'
            }), 400

        # ========== 用户选择 AI 专家 ==========
        if prompt_id:
            # 用户指定了 AI 专家
            active_prompt = db.get_prompt_by_id(prompt_id)
            if not active_prompt:
                return jsonify({
                    'success': False,
                    'error': f'AI 专家配置不存在 (ID: {prompt_id})'
                }), 400
            print(f"[AI生成] 使用用户选择的 AI 专家: {active_prompt.get('name', 'Unknown')} (ID: {prompt_id})")
        else:
            # 用户未指定，使用默认激活的配置
            active_prompt = db.get_active_prompt()
            if not active_prompt:
                return jsonify({
                    'success': False,
                    'error': '请先创建并激活一个 AI 专家配置，或在生成时选择 AI 专家'
                }), 400
            print(f"[AI生成] 使用默认激活的 AI 专家: {active_prompt.get('name', 'Unknown')} (ID: {active_prompt['id']})")

        # 获取 API Key
        api_key = get_api_key()
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'DeepSeek API Key not configured'
            }), 400

        # 初始化 Adapter
        deepseek_adapter = DeepSeekAdapter(api_key)

        # 先尝试匹配预设问答 (传入 deepseek_adapter 以支持语义匹配)
        preset_answer = db.match_preset_answer(active_prompt['id'], customer_message, deepseek_adapter=deepseek_adapter)

        if preset_answer:
            # 如果匹配到预设答案，直接返回（三个版本都用预设答案）
            return jsonify({
                'success': True,
                'suggestions': {
                    'aggressive': preset_answer,
                    'conservative': preset_answer,
                    'professional': preset_answer
                },
                'is_preset': True,
                'tokens_used': 0,
                'cost': 0,
                'response_time': 0
            })

        # 没有匹配到预设答案，使用增强版 AI 生成
        generator = EnhancedReplyGenerator(api_key, db, kb_manager=kb_manager)

        # 解析配置（将 JSON 字符串转换为字典/列表）
        knowledge_base_raw = active_prompt.get('knowledge_base', '[]')
        forbidden_words_raw = active_prompt.get('forbidden_words', '[]')
        
        # 安全解析 JSON 字符串
        try:
            knowledge_base = json.loads(knowledge_base_raw) if isinstance(knowledge_base_raw, str) else knowledge_base_raw
        except:
            knowledge_base = []
        
        try:
            forbidden_words = json.loads(forbidden_words_raw) if isinstance(forbidden_words_raw, str) else forbidden_words_raw
        except:
            forbidden_words = []
        
        system_prompt_config = {
            'role_definition': active_prompt.get('role_definition', ''),
            'business_logic': active_prompt.get('business_logic', ''),
            'tone_style': active_prompt.get('tone_style', 'professional'),
            'reply_length': active_prompt.get('reply_length', 'medium'),
            'emoji_usage': active_prompt.get('emoji_usage', 'occasional'),
            'knowledge_base': knowledge_base,
            'forbidden_words': forbidden_words
        }

        # 生成三个版本（使用增强版生成器）
        result = generator.generate_three_versions(
            session_id=session_id,
            customer_message=customer_message,
            system_prompt_config=system_prompt_config,
            prompt_id=active_prompt['id'],
            conversation_history=conversation_history
        )

        return jsonify({
            'success': result['success'],
            'suggestions': {
                'aggressive': result['aggressive'],
                'conservative': result['conservative'],
                'professional': result['professional']
            },
            'suggestion_id': result.get('suggestion_id'),
            'metadata': result.get('metadata', {}),
            'tokens_used': result.get('tokens_used', 0),
            'cost': result.get('cost', 0),
            'response_time': result.get('response_time', 0)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 版本选择记录 API（改进点5：反馈学习）==========

@ai_expert_bp.route('/record-selection', methods=['POST'])
def record_selection():
    """记录用户选择的版本"""
    try:
        data = request.json
        session_id = data.get('session_id')
        customer_message = data.get('customer_message')
        selected_version = data.get('selected_version')  # aggressive/conservative/professional
        suggestion_id = data.get('suggestion_id')

        if not all([session_id, customer_message, selected_version]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # 获取 API Key 并创建生成器
        api_key = get_api_key()
        if api_key:
            generator = EnhancedReplyGenerator(api_key, db, kb_manager=kb_manager)
            generator.record_version_selection(
                session_id=session_id,
                customer_message=customer_message,
                selected_version=selected_version,
                suggestion_id=suggestion_id
            )

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/record-modification', methods=['POST'])
def record_modification():
    """记录用户对回复的修改"""
    try:
        data = request.json
        session_id = data.get('session_id')
        original_reply = data.get('original_reply')
        modified_reply = data.get('modified_reply')

        if not all([session_id, original_reply, modified_reply]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # 获取 API Key 并创建生成器
        api_key = get_api_key()
        if api_key:
            generator = EnhancedReplyGenerator(api_key, db, kb_manager=kb_manager)
            generator.record_reply_modification(
                session_id=session_id,
                original_reply=original_reply,
                modified_reply=modified_reply
            )

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/learning-insights', methods=['GET'])
def get_learning_insights():
    """获取学习洞察"""
    try:
        api_key = get_api_key()
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API Key not configured'
            }), 400

        generator = EnhancedReplyGenerator(api_key, db)
        insights = generator.get_learning_insights()

        return jsonify({
            'success': True,
            'insights': insights
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 反馈 API ==========

# ========== 反馈 API ==========

@ai_expert_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """提交回复反馈 (Accept/Edit) - 自我进化核心"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_query = data.get('user_query')
        original_reply = data.get('original_reply')
        final_reply = data.get('final_reply')
        action = data.get('action') # 'ACCEPTED' or 'MODIFIED'
        prompt_id = data.get('prompt_id')

        print(f"[Feedback] Rcvd: {action} | Orig: {original_reply[:10]}... | Final: {final_reply[:10]}...")

        # 1. 记录反馈日志
        db.add_reply_feedback(
            session_id=session_id,
            prompt_id=prompt_id,
            user_query=user_query,
            original_reply=original_reply,
            final_reply=final_reply,
            action=action
        )

        # 2. 挖掘“金牌话术”
        # 只有当用户“采纳”或者“微调”后发送了消息，且该消息有内容，才视为金牌话术
        # 如果是 accepted (modify=False)，则 original=final -> 是一次成功的生成 -> 存入 Golden Reply
        # 如果是 modified，则 final 是更好的回答 -> 存入 Golden Reply
        
        if final_reply and len(final_reply.strip()) > 3: # 太短的忽略
             # 保存到金牌话术库
             if prompt_id:
                 db.add_golden_reply(prompt_id, user_query, final_reply)
                 print(f"[Learning] Saved Golden Reply for prompt {prompt_id}")
        
        return jsonify({
            'success': True
        })

    except Exception as e:
        print(f"[Feedback Error] {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 收藏 API ==========

@ai_expert_bp.route('/favorites', methods=['POST'])
def add_favorite():
    """添加收藏话术"""
    try:
        data = request.json

        favorite_id = db.add_favorite(data)

        return jsonify({
            'success': True,
            'favorite_id': favorite_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """获取收藏话术"""
    try:
        prompt_id = request.args.get('prompt_id', type=int)

        favorites = db.get_favorites(prompt_id)

        # 解析 JSON 字段
        for fav in favorites:
            if fav.get('tags'):
                fav['tags'] = json.loads(fav['tags'])

        return jsonify({
            'success': True,
            'favorites': favorites
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    """删除收藏"""
    try:
        # TODO: 实现删除逻辑
        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 统计 API ==========

@ai_expert_bp.route('/stats/usage', methods=['GET'])
def get_usage_stats():
    """获取使用统计"""
    try:
        today_stats = db.get_usage_stats('today')
        week_stats = db.get_usage_stats('week')
        month_stats = db.get_usage_stats('month')
        total_stats = db.get_usage_stats('all')

        return jsonify({
            'success': True,
            'today': today_stats,
            'week': week_stats,
            'month': month_stats,
            'total': total_stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/stats/performance', methods=['GET'])
def get_performance_stats():
    """获取性能统计"""
    try:
        stats = db.get_usage_stats('all')

        return jsonify({
            'success': True,
            'avg_response_time': stats['avg_response_time'],
            'success_rate': stats['success_rate'],
            'total_requests': stats['requests']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 上下文管理 API ==========

@ai_expert_bp.route('/context', methods=['POST'])
def update_context():
    """更新对话上下文"""
    try:
        data = request.json
        session_id = data.get('session_id')
        sender = data.get('sender')
        message = data.get('message')
        is_customer = data.get('is_customer', True)

        if not all([session_id, sender, message]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        db.add_message(session_id, sender, message, is_customer)

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/context/<session_id>', methods=['GET'])
def get_context(session_id):
    """获取会话上下文"""
    try:
        limit = request.args.get('limit', 10, type=int)

        messages = db.get_recent_messages(session_id, limit)

        return jsonify({
            'success': True,
            'messages': messages
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/context/cleanup', methods=['DELETE'])
def cleanup_context():
    """清理旧数据"""
    try:
        days = request.args.get('days', 30, type=int)

        deleted_count = db.cleanup_old_conversations(days)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/context/message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """删除单条消息"""
    try:
        db.delete_message(message_id)

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/context/session/<path:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除整个会话的所有消息"""
    try:
        from urllib.parse import unquote
        # URL 解码
        session_id = unquote(session_id)

        print(f"[DEBUG] Deleting session: {session_id}")
        deleted_count = db.delete_session_messages(session_id)
        print(f"[DEBUG] Deleted {deleted_count} messages")

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        print(f"[ERROR] Failed to delete session: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 配置管理 API ==========

@ai_expert_bp.route('/config', methods=['GET'])
def get_config():
    """获取全局配置 (兼容 AI 配置和监控配置)"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 创建响应副本
                response_data = {
                    'success': True,
                    'config': config.copy(),
                    'monitor_keyword': config.get('monitor_keyword', '客户')
                }
                
                # 隐藏 API Key (仅在 config 嵌套对象中隐藏)
                if 'deepseek_api_key' in response_data['config']:
                    key = response_data['config']['deepseek_api_key']
                    response_data['config']['deepseek_api_key'] = '***' + key[-4:] if key else ''

                return jsonify(response_data)
        else:
            return jsonify({
                'success': True,
                'monitor_keyword': '客户',
                'config': {
                    'deepseek_api_key': '',
                    'daily_budget': 10.0,
                    'monthly_budget': 200.0,
                    'warning_threshold': 0.8,
                    'monitor_keyword': '客户'
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/config', methods=['POST', 'PUT'])
def update_config():
    """更新全局配置 (支持 POST 和 PUT)"""
    try:
        data = request.json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_config.json')

        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 读取现有配置
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # 合并新配置
        config.update(data)

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return jsonify({
            'success': True,
            'config': config
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 模板 API ==========

@ai_expert_bp.route('/templates', methods=['GET'])
def get_templates():
    """获取所有模板"""
    try:
        templates = template_loader.get_template_list()

        return jsonify({
            'success': True,
            'templates': templates
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """获取单个模板详情"""
    try:
        template = template_loader.load_template(template_id)

        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404

        return jsonify({
            'success': True,
            'template': template
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 关键词规则 API ==========

@ai_expert_bp.route('/keywords', methods=['POST'])
def add_keyword():
    """添加关键词规则"""
    try:
        data = request.json

        if not data.get('prompt_id') or not data.get('keyword'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        rule_id = db.add_keyword_rule(
            prompt_id=data['prompt_id'],
            keyword=data['keyword'],
            match_type=data.get('match_type', 'startswith'),
            priority=data.get('priority', 0)
        )

        return jsonify({
            'success': True,
            'rule_id': rule_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/keywords', methods=['GET'])
def get_keywords():
    """获取关键词规则列表"""
    try:
        prompt_id = request.args.get('prompt_id', type=int)
        rules = db.get_keyword_rules(prompt_id)

        return jsonify({
            'success': True,
            'rules': rules
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/keywords/<int:rule_id>', methods=['DELETE'])
def delete_keyword(rule_id):
    """删除关键词规则"""
    try:
        db.delete_keyword_rule(rule_id)

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 预设问答 API ==========

@ai_expert_bp.route('/preset-qa', methods=['POST'])
def add_preset_qa():
    """添加预设问答"""
    try:
        data = request.json

        if not data.get('prompt_id') or not data.get('question_pattern') or not data.get('answer'):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        qa_id = db.add_preset_qa(
            prompt_id=data['prompt_id'],
            question_pattern=data['question_pattern'],
            answer=data['answer'],
            match_type=data.get('match_type', 'contains'),
            priority=data.get('priority', 0)
        )

        return jsonify({
            'success': True,
            'qa_id': qa_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/preset-qa', methods=['GET'])
def get_preset_qa():
    """获取预设问答列表"""
    try:
        prompt_id = request.args.get('prompt_id', type=int, required=True)
        qa_list = db.get_preset_qa(prompt_id)

        return jsonify({
            'success': True,
            'qa_list': qa_list
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/preset-qa/<int:qa_id>', methods=['PUT'])
def update_preset_qa(qa_id):
    """更新预设问答"""
    try:
        data = request.json

        db.update_preset_qa(
            qa_id=qa_id,
            question_pattern=data['question_pattern'],
            answer=data['answer']
        )

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/preset-qa/<int:qa_id>', methods=['DELETE'])
def delete_preset_qa(qa_id):
    """删除预设问答"""
    try:
        db.delete_preset_qa(qa_id)

        return jsonify({
            'success': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== 文档管理 API (RAG) ==========

@ai_expert_bp.route('/documents', methods=['POST'])
def upload_document():
    """上传文档到知识库"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        bound_prompt_id = request.form.get('bound_prompt_id', type=int)
        description = request.form.get('description', '')
        
        # Save to temp path
        # Fix path: go up properly
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        # 加上时间戳防止重名
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        file.save(file_path)
        
        # Add to RAG
        success = kb_manager.add_document(file_path, bound_prompt_id, description)
        
        if success:
            return jsonify({'success': True, 'message': 'Document indexed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to index document'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_expert_bp.route('/documents', methods=['GET'])
def list_documents():
    """获取文档列表"""
    try:
        bound_prompt_id = request.args.get('bound_prompt_id', type=int)
        docs = kb_manager.get_file_list(bound_prompt_id)
        
        formatted_docs = []
        for doc in docs:
            # Assuming row factory is not set to dict, manual indexing
            # id, file_name, file_path, file_type, file_size, bound_prompt_id, upload_time, description
            formatted_docs.append({
                'id': doc[0],
                'file_name': doc[1],
                'file_type': doc[3],
                'file_size': doc[4],
                'bound_prompt_id': doc[5],
                'upload_time': doc[6],
                'description': doc[7]
            })
            
        return jsonify({'success': True, 'documents': formatted_docs})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_expert_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """删除文档"""
    try:
        success = kb_manager.delete_file(doc_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Document not found or failed to delete'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
