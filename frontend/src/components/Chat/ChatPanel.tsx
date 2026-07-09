import React, { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/hooks';
import { sendMessage, addUserMessage } from '../../redux/chatSlice';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { TypingIndicator } from './TypingIndicator';
import { ErrorBanner } from '../Common/ErrorBanner';
import './Chat.css';

export const ChatPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, loading, error } = useAppSelector((state) => state.chat);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = (text: string) => {
    dispatch(addUserMessage(text));
    dispatch(sendMessage(text));
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>AI Assistant</h2>
      </div>
      
      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="chat-messages-list">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {loading && (
              <div className="chat-loading-indicator">
                <TypingIndicator />
              </div>
            )}
            {error && <ErrorBanner message={error} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <div className="chat-input-container">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
};
