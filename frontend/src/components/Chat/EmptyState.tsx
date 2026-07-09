import React from 'react';
import { MessageSquare } from 'lucide-react';
import './Chat.css';

export const EmptyState: React.FC = () => (
  <div className="chat-empty-state">
    <MessageSquare size={48} className="empty-icon" />
    <h3>Start a Conversation</h3>
    <p>Ask the AI assistant to log this interaction or ask questions about the HCP.</p>
  </div>
);
