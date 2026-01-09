/**
 * 状态管理 Context 统一导出
 * 
 * 规范：所有跨页面共享的状态必须通过 Context 管理
 * 详见 README.md
 */

// 消息状态管理
export { MessageProvider, useMessages } from './MessageContext';
export type { Message, ChatSession } from './MessageContext';

