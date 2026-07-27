import React, { useRef } from 'react';
import { Upload, FileText } from 'lucide-react';
import './Chat.css';

interface EmptyStateProps {
  onFileUpload: (file: File) => void;
  onPasteText?: (text: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onFileUpload, onPasteText }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleCardClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handlePasteCardClick = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && onPasteText) {
        onPasteText(text);
      }
    } catch (err) {
      console.error('Failed to read clipboard', err);
      // Fallback for browsers that block clipboard API without explicit permission
      const userInput = prompt("Please paste your complaint text here:");
      if (userInput && onPasteText) {
        onPasteText(userInput);
      }
    }
  };

  return (
    <div className="chat-empty-state-modern">
      <h3 className="empty-title">AI Complaint Intake Assistant</h3>
      <p className="empty-subtitle">
        Upload or paste a complaint below. The AI will extract the structured data and populate the form on the left.
      </p>
      
      <div className="empty-cards-container">
        <div 
          className="empty-card"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleCardClick}
        >
          <Upload size={32} className="card-icon" />
          <div className="card-text">
            Drag & drop complaint PDF or Email file here
          </div>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
            accept=".pdf,.txt,.docx,.eml"
          />
        </div>

        <div className="empty-card" onClick={handlePasteCardClick}>
          <FileText size={32} className="card-icon" />
          <div className="card-text">
            Or paste complaint text here
          </div>
        </div>
      </div>
    </div>
  );
};
