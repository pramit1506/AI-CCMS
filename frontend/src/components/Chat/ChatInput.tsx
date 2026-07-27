import React, { useState, useRef } from 'react';
import { Send, Paperclip } from 'lucide-react';
import './Chat.css';

interface ChatInputProps {
  onSend: (message: string) => void;
  onFileUpload: (file: File) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, onFileUpload, disabled }) => {
  const [input, setInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && !disabled) {
      onFileUpload(file);
      // reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <button
        type="button"
        className="chat-attach-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
      >
        <Paperclip size={20} />
      </button>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
        accept=".pdf,.docx,.txt,.eml"
      />
      <input
        type="text"
        className="chat-input-field"
        placeholder="Type a message or drop a file..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
      />
      <button 
        type="submit" 
        className="chat-send-btn" 
        disabled={!input.trim() || disabled}
      >
        <Send size={20} />
      </button>
    </form>
  );
};
