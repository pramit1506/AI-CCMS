import React from 'react';
import { ClarificationPayload } from '../../types/agent';
import { useAppDispatch } from '../../redux/hooks';
import { sendMessage } from '../../redux/chatSlice';
import { addUserMessage } from '../../redux/chatSlice';
import './Chat.css';

interface ClarificationCardProps {
  payload: ClarificationPayload;
}

export const ClarificationCard: React.FC<ClarificationCardProps> = ({ payload }) => {
  const dispatch = useAppDispatch();

  const handleOptionSelect = (option: string) => {
    dispatch(addUserMessage(option));
    dispatch(sendMessage(option));
  };

  if (!payload.required) return null;

  return (
    <div className="clarification-card">
      <div className="clarification-question">
        {payload.question || 'I need some clarification to proceed.'}
      </div>
      {payload.options && payload.options.length > 0 && (
        <div className="clarification-options">
          {payload.options.map((option, index) => (
            <button 
              key={index} 
              className="clarification-option-btn"
              onClick={() => handleOptionSelect(option)}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
