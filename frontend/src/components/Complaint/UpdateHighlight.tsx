import React, { useEffect, useState } from 'react';
import './Complaint.css';

interface UpdateHighlightProps {
  children: React.ReactNode;
  isUpdated: boolean;
  onHighlightEnd?: () => void;
}

export const UpdateHighlight: React.FC<UpdateHighlightProps> = ({ children, isUpdated, onHighlightEnd }) => {
  const [highlight, setHighlight] = useState(false);

  useEffect(() => {
    if (isUpdated) {
      setHighlight(true);
      const timer = setTimeout(() => {
        setHighlight(false);
        if (onHighlightEnd) {
          onHighlightEnd();
        }
      }, 2000); // Highlight duration
      return () => clearTimeout(timer);
    }
  }, [isUpdated, onHighlightEnd]);

  return (
    <div className={`update-highlight ${highlight ? 'highlight-active' : ''}`}>
      {children}
    </div>
  );
};
