import React from 'react';
import { Loader2 } from 'lucide-react';
import './Common.css';

export const LoadingSpinner: React.FC = () => (
  <div className="loading-spinner">
    <Loader2 className="spinner-icon" size={24} />
  </div>
);
