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
from ai_expert.message_queue_manager import MessageQueueManager
from ai_expert.background_processor import BackgroundProcessor
from ai_expert.analytics_manager import AnalyticsManager
from ai_expert.logger import api_logger as logger
from ai_expert.constants import (
    RATE_LIMIT_AI_GENERATE, RATE_LIMIT_WINDOW,
    MAX_MESSAGES_PER_SESSION
)
import json
import os
import threading

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

# 初始化消息队列管理器
queue_manager = MessageQueueManager(db)

# 初始化数据分析引擎
analytics_manager = AnalyticsManager(db)

# 全局后台处理器实例
bg_processor = None

# API Key 管理（优先环境变量，兼容旧配置文件）
def get_api_key() -> str:
    """获取 DeepSeek API Key - 使用统一配置管理"""
    from ai_expert.config import Config
    return Config.get_deepseek_api_key()

def start_background_worker():
    """初始化并启动后台预生成服务"""
    global bg_processor
    api_key = get_api_key()
    if not api_key:
        logger.warning("API key not found, background worker not started")
        logger.warning("Please set DEEPSEEK_API_KEY environment variable or configure in .env file")
        return

    from ai_expert.enhanced_reply_generator import EnhancedReplyGenerator
    generator = EnhancedReplyGenerator(api_key, db, kb_manager=kb_manager)

    bg_processor = BackgroundProcessor(db, queue_manager, generator)
    bg_processor.start()
    logger.info("Background worker pipeline initialized and running")

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
        logger.debug(f"获取 {len(prompts)} 个配置")

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
                logger.debug(f"{prompt['name']} - keywords: {len(prompt['keywords'])}")
            except Exception as kw_err:
                logger.warning(f"{prompt['name']} - keywords 错误: {kw_err}")
                prompt['keywords'] = []

            # 获取预设问答
            try:
                preset_qa = db.get_preset_qa(prompt['id'])
                prompt['preset_qa'] = preset_qa if preset_qa else []
                logger.debug(f"{prompt['name']} - preset_qa: {len(prompt['preset_qa'])}")
            except Exception as qa_err:
                logger.warning(f"{prompt['name']} - preset_qa 错误: {qa_err}")
                prompt['preset_qa'] = []

        logger.debug(f"返回 {len(prompts)} 个增强的配置")
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

@ai_expert_bp.route('/prompts/<int:prompt_id>/full-update', methods=['POST'])
def full_update_prompt(prompt_id):
    """一键全量保存：Prompt 配置 + 关键词规则 + 预设问答（事务化版本）"""
    try:
        data = request.json
        logger.info(f"Full update triggered for prompt {prompt_id}")

        # 生成最新的 System Prompt
        system_prompt = prompt_builder.build_system_prompt(data)
        data['system_prompt'] = system_prompt

        # 使用底层的原子事务方法，一次锁表，一次完成，彻底解决 Deadlock
        db.full_update_prompt_transactional(prompt_id, data)

        return jsonify({
            'success': True,
            'prompt_id': prompt_id,
            'message': 'Full configuration updated atomically'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
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

from ai_expert.rate_limiter import rate_limit
from ai_expert.error_handler import handle_errors, ValidationError, APIKeyError, ExternalAPIError

@ai_expert_bp.route('/generate', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)  # 每分钟最多 20 次 AI 生成
@handle_errors  # 统一错误处理
def generate_reply():
    """生成 AI 回复建议"""
    data = request.json or {}
    session_id = data.get('session_id')
    customer_message = data.get('customer_message')
    conversation_history = data.get('conversation_history', [])
    prompt_id = data.get('prompt_id')

    # 参数验证
    if not session_id or not customer_message:
        raise ValidationError('缺少必填字段', details={
            'required': ['session_id', 'customer_message'],
            'received': list(data.keys())
        })

    # ========== 用户选择 AI 专家 ==========
    if prompt_id:
        active_prompt = db.get_prompt_by_id(prompt_id)
        if not active_prompt:
            raise ValidationError(f'AI 专家配置不存在 (ID: {prompt_id})')
        logger.info(f"使用用户选择的 AI 专家: {active_prompt.get('name', 'Unknown')} (ID: {prompt_id})")
    else:
        active_prompt = db.get_active_prompt()
        if not active_prompt:
            raise ValidationError('请先创建并激活一个 AI 专家配置，或在生成时选择 AI 专家')
        logger.info(f"使用默认激活的 AI 专家: {active_prompt.get('name', 'Unknown')} (ID: {active_prompt['id']})")

    # 获取 API Key
    api_key = get_api_key()
    if not api_key:
        raise APIKeyError('DeepSeek API Key 未配置')

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

    if not result.get('success'):
        raise ExternalAPIError(result.get('error', 'AI 生成失败'))

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

        logger.info(f"Feedback received: {action} | Orig: {(original_reply or '')[:10]}... | Final: {(final_reply or '')[:10]}...")

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
                 logger.info(f"Saved Golden Reply for prompt {prompt_id}")
        
        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Feedback error: {e}")
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

        logger.debug(f"Deleting session: {session_id}")
        deleted_count = db.delete_session_messages(session_id)
        logger.debug(f"Deleted {deleted_count} messages")

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}", exc_info=True)
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
            'keywords': rules  # 修改为 keywords 以保持前端一致性
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

# ========== Phase 5.5: 消息历史与任务持久化 API ==========

@ai_expert_bp.route('/tasks/<int:task_id>/status', methods=['POST'])
def update_task_status(task_id):
    """更新单个任务的状态"""
    try:
        data = request.json
        status = data.get('status')
        error_msg = data.get('error_msg')
        
        if not status:
            return jsonify({'success': False, 'error': 'Missing status'}), 400
            
        queue_manager.update_status(task_id, status, error_msg=error_msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_expert_bp.route('/tasks/recent', methods=['GET'])
def get_recent_tasks():
    """获取最近的 AI 任务列表"""
    try:
        limit = request.args.get('limit', default=20, type=int)
        # 获取所有任务，不仅仅是 PENDING
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM message_queue 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            task = dict(row)
            if task['ai_reply_options']:
                task['ai_reply_options'] = json.loads(task['ai_reply_options'])
            tasks.append(task)
            
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_expert_bp.route('/history/<session_id>', methods=['GET'])
def get_session_history(session_id):
    """获取特定会话的历史建议记录"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        # 联查建议记录
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM ai_suggestions 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            item = dict(row)
            # 解析 context
            if item['context']:
                try:
                    item['context'] = json.loads(item['context'])
                except:
                    pass
            history.append(item)
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_expert_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取单个任务详情"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM message_queue WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
            
        task = dict(row)
        if task['ai_reply_options']:
            task['ai_reply_options'] = json.loads(task['ai_reply_options'])
            
        return jsonify({
            'success': True,
            'task': task
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# ========== 消息队列与看板 API (Phase 7: Batch Processing) ==========

@ai_expert_bp.route('/tasks/kanban', methods=['GET'])
def get_kanban_tasks():
    """获取看板所需的批量任务列表"""
    try:
        limit = request.args.get('limit', 50, type=int)
        tasks = queue_manager.get_kanban_tasks(limit)
        
        # 确保 ai_reply_options 是解析后的 JSON
        for task in tasks:
            if task.get('ai_reply_options'):
                try:
                    task['ai_reply_options'] = json.loads(task['ai_reply_options'])
                except:
                    pass
                    
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_expert_bp.route('/tasks/bulk-generate', methods=['POST'])
def bulk_generate_replies():
    """批量触发 PENDING 状态任务的 AI 生成"""
    try:
        data = request.json
        prompt_id = data.get('prompt_id')
        task_ids = data.get('task_ids', []) # 可选：指定任务 ID 列表
        
        # 如果没传 prompt_id，使用默认激活的
        if not prompt_id:
            active_prompt = db.get_active_prompt()
            if not active_prompt:
                return jsonify({'success': False, 'error': 'No active prompt found'}), 400
            prompt_id = active_prompt['id']
        else:
            active_prompt = db.get_prompt_by_id(prompt_id)

        # 获取待处理任务
        if task_ids:
            pending_tasks = [t for t in [queue_manager.get_task_by_id(tid) for tid in task_ids] if t and t['status'] == 'PENDING']
        else:
            pending_tasks = queue_manager.get_pending_tasks(limit=10) # 默认处理前 10 条
            
        if not pending_tasks:
            return jsonify({'success': True, 'count': 0, 'message': 'No pending tasks'})

        api_key = get_api_key()
        generator = EnhancedReplyGenerator(api_key, db, kb_manager=kb_manager)
        
        # 批量处理逻辑
        processed_count = 0
        for task in pending_tasks:
            try:
                # 更新状态为 PROCESSING 防止重复执行
                queue_manager.update_status(task['id'], 'PROCESSING')
                
                # 构造生成所需的配置
                system_prompt_config = {
                    'role_definition': active_prompt.get('role_definition', ''),
                    'business_logic': active_prompt.get('business_logic', ''),
                    'tone_style': active_prompt.get('tone_style', 'professional'),
                    'reply_length': active_prompt.get('reply_length', 'medium'),
                    'emoji_usage': active_prompt.get('emoji_usage', 'occasional'),
                    'knowledge_base': json.loads(active_prompt.get('knowledge_base', '[]')),
                    'forbidden_words': json.loads(active_prompt.get('forbidden_words', '[]'))
                }
                
                # 获取简单的历史记录（此处可扩展）
                history = db.get_recent_messages(task['session_id'], limit=5)
                
                # 执行生成
                result = generator.generate_three_versions(
                    session_id=task['session_id'],
                    customer_message=task['raw_message'],
                    system_prompt_config=system_prompt_config,
                    prompt_id=prompt_id,
                    conversation_history=history
                )
                
                if result['success']:
                    # 更新状态为 COMPLETED 并存储建议
                    queue_manager.update_status(
                        task['id'], 
                        'COMPLETED', 
                        ai_reply_options={
                            'aggressive': result['aggressive'],
                            'conservative': result['conservative'],
                            'professional': result['professional']
                        }
                    )
                    processed_count += 1
                else:
                    queue_manager.update_status(task['id'], 'FAILED', error_msg=result.get('error'))
                    
            except Exception as task_err:
                logger.error(f"Bulk Gen Error - Task {task['id']}: {task_err}")
                queue_manager.update_status(task['id'], 'FAILED', error_msg=str(task_err))

        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'total_found': len(pending_tasks)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== Phase 8: 智能数据仪表盘 API ==========

@ai_expert_bp.route('/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """获取仪表盘全量统计数据"""
    try:
        overview = analytics_manager.get_overview_stats()
        trends = analytics_manager.get_daily_trends(limit_days=7)
        keywords = analytics_manager.get_hot_keywords(top_n=12)
        efficiency = analytics_manager.get_ai_efficiency()
        
        # AI 洞察逻辑 (调用大模型，设置超时保护以免阻塞大屏显示)
        insights = "点击刷新或稍后再试以获取 AI 经营简报。"
        try:
            api_key = get_api_key()
            if api_key:
                def generator_fn(prompt):
                    from ai_expert.deepseek_adapter import DeepSeekAdapter
                    # 可以在这里设置更短的超时，或者使用线程池
                    adapter = DeepSeekAdapter(api_key)
                    return adapter.chat(prompt, system_prompt="你是一位商业分析助手。")

                # 设置获取洞察的最长等待时间（例如 8 秒）
                # 这里简单处理：如果失败则降级
                insights = analytics_manager.get_ai_insights(generator_fn)
        except Exception as ai_err:
            logger.warning(f"Analytics AI Error: {ai_err}")
            insights = "AI 简报生成超时或失败，但不影响核心数据查看。"
        
        return jsonify({
            'success': True,
            'data': {
                'overview': overview,
                'trends': trends,
                'keywords': keywords,
                'efficiency': efficiency,
                'insights': insights
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
