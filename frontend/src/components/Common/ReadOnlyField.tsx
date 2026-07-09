import React from 'react';
import './Common.css';

interface ReadOnlyFieldProps {
  label: string;
  value: string | null | undefined;
}

export const ReadOnlyField: React.FC<ReadOnlyFieldProps> = ({ label, value }) => (
  <div className="readonly-field">
    <label className="field-label">{label}</label>
    <div className="field-value">{value || '-'}</div>
  </div>
);
