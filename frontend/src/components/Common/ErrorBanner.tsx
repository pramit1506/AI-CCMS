import React from 'react';
import { AlertCircle } from 'lucide-react';
import './Common.css';

interface ErrorBannerProps {
  message: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message }) => (
  <div className="error-banner">
    <AlertCircle size={20} className="error-icon" />
    <span>{message}</span>
  </div>
);
