import React from 'react';
import { ToolStatus } from '../../types/agent';
import './Common.css';

interface StatusBadgeProps {
  status: ToolStatus;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  return (
    <span className={`status-badge status-${status}`}>
      {label || status}
    </span>
  );
};
