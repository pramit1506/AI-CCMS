import React from 'react';
import { TimelineEvent } from '../../types/agent';
import { StatusBadge } from './StatusBadge';
import './Common.css';

interface TimelineProps {
  events: TimelineEvent[];
}

export const Timeline: React.FC<TimelineProps> = ({ events }) => {
  if (!events || events.length === 0) return null;

  return (
    <div className="timeline-container">
      {events.map((event, index) => (
        <div key={event.id} className="timeline-item">
          <div className="timeline-marker-container">
            <div className={`timeline-marker status-${event.status}`}></div>
            {index < events.length - 1 && <div className="timeline-line"></div>}
          </div>
          <div className="timeline-content">
            <div className="timeline-header">
              <span className="timeline-title">{event.title}</span>
              <StatusBadge status={event.status} />
            </div>
            {event.description && (
              <div className="timeline-description">{event.description}</div>
            )}
            <div className="timeline-timestamp">
              {new Date(event.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
