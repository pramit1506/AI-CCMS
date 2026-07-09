import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../../redux/hooks';
import './Chat.css';

export const TypingIndicator: React.FC = () => {
  const agent = useAppSelector((state) => state.agent);
  const toolStatus = agent?.toolStatus ?? 'idle';
  const selectedTool = agent?.selectedTool ?? null;
  const [text, setText] = useState('AI is typing');

  useEffect(() => {
    if (toolStatus === 'executing' && selectedTool) {
      setText(`Executing ${selectedTool}`);
    } else {
      setText('AI is processing request');
    }
  }, [toolStatus, selectedTool]);

  return (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span>.</span><span>.</span><span>.</span>
      </div>
      <span className="typing-text">{text}...</span>
    </div>
  );
};
