import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../redux/hooks';
import { sendMessage, addUserMessage } from '../../redux/chatSlice';
import { setExtractionStatus } from '../../redux/complaintSlice';
import { uploadService } from '../../services/uploadService';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { TypingIndicator } from './TypingIndicator';
import { ErrorBanner } from '../Common/ErrorBanner';
import './Chat.css';

export const ChatPanel: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, loading, error } = useAppSelector((state) => state.chat);
  const { extractionStatus } = useAppSelector((state) => state.complaint);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, extractionStatus]);

  const handleSend = (text: string) => {
    dispatch(addUserMessage(text));
    dispatch(sendMessage(text));
  };

  const handleFileUpload = async (file: File) => {
    dispatch(setExtractionStatus('extracting'));
    try {
      const response = await uploadService.extractText(file);
      if (response.success && response.data) {
        const textToProcess = `Process this uploaded document (${response.data.filename}):\n\n${response.data.text}`;
        handleSend(textToProcess);
      }
      dispatch(setExtractionStatus('completed'));
    } catch (error) {
      console.error('File upload failed:', error);
      dispatch(setExtractionStatus('error'));
    }
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  }, [dispatch]);

  return (
    <div 
      className={`chat-panel ${isDragging ? 'chat-panel-dragging' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="chat-header">
        <h2>AI Assistant</h2>
      </div>
      
      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <EmptyState 
            onFileUpload={handleFileUpload} 
            onPasteText={handleSend} 
          />
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
            {extractionStatus === 'extracting' && (
              <div className="chat-loading-indicator">
                <span className="typing-text">Extracting document text...</span>
              </div>
            )}
            {error && <ErrorBanner message={error} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <div className="chat-input-container">
        <ChatInput 
          onSend={handleSend} 
          onFileUpload={handleFileUpload}
          disabled={loading || extractionStatus === 'extracting'} 
        />
      </div>
      
      {isDragging && (
        <div className="chat-drop-overlay">
          <div className="chat-drop-message">Drop file here to upload</div>
        </div>
      )}
    </div>
  );
};
