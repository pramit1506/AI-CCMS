import React from 'react';
import { ToolExecutionEvent, TimelineEvent } from '../../types/agent';
import { Timeline } from '../Common/Timeline';
import './Chat.css';

interface ToolExecutionCardProps {
  executions: ToolExecutionEvent[];
}

export const ToolExecutionCard: React.FC<ToolExecutionCardProps> = ({ executions }) => {
  if (!executions || executions.length === 0) return null;

  // Convert ToolExecutionEvents to TimelineEvents
  const timelineEvents: TimelineEvent[] = executions.map((exec, index) => ({
    id: `tool-exec-${index}-${Date.now()}`,
    timestamp: new Date().toISOString(), // In a real app, this should come from backend
    title: exec.tool_name,
    description: exec.error || (exec.status === 'success' ? 'Complaint updated successfully' : undefined),
    status: exec.status
  }));

  return (
    <div className="tool-execution-card">
      <div className="tool-execution-header">
        <span className="tool-execution-title">AI Action Trace</span>
      </div>
      <Timeline events={timelineEvents} />
    </div>
  );
};
