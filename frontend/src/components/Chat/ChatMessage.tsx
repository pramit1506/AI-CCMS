import React, { useState } from 'react';
import { ChatMessage as IChatMessage } from '../../types/chat';
import { ToolExecutionCard } from './ToolExecutionCard';
import { ClarificationCard } from './ClarificationCard';
import './Chat.css';

interface ChatMessageProps {
  message: IChatMessage;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className={`chat-message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      <div className="chat-message-content">
        {!isUser && message.tool_executions && message.tool_executions.length > 0 && (
          <ToolExecutionCard executions={message.tool_executions} />
        )}
        <div className="chat-message-bubble">
          {message.content}
        </div>
        {!isUser && message.clarification_request && message.clarification_request.required && (
          <ClarificationCard payload={message.clarification_request} />
        )}
      </div>
      <div className="chat-message-footer">
        <span className="chat-message-time">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        {!isUser && (
          <button className="chat-message-copy" onClick={handleCopy} title="Copy to clipboard">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        )}
      </div>
    </div>
  );
};
