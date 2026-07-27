import React, { useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '../../redux/hooks';
import { clearUpdatedFields } from '../../redux/complaintSlice';
import { ReadOnlyField } from '../Common/ReadOnlyField';
import { UpdateHighlight } from './UpdateHighlight';
import './Complaint.css';

export const RiskAssessment: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currentComplaint, lastUpdatedFields } = useAppSelector((state) => state.complaint);

  const handleHighlightEnd = useCallback(() => {
    if (lastUpdatedFields.length > 0) {
      dispatch(clearUpdatedFields());
    }
  }, [dispatch, lastUpdatedFields]);

  const isUpdated = (field: string) => lastUpdatedFields.includes(field);

  const complaint = currentComplaint || {};

  return (
    <div className="risk-assessment-section" style={{ marginTop: '2rem' }}>
      <h3 className="section-subtitle">AI Co-pilot Risk Assessment</h3>
      <div className="details-grid">
        <UpdateHighlight isUpdated={isUpdated('risk_classification')} onHighlightEnd={handleHighlightEnd}>
          <ReadOnlyField 
            label="Risk Classification" 
            value={complaint.risk_classification} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('root_cause_recommendation')}>
          <ReadOnlyField 
            label="Root Cause Recommendation" 
            value={complaint.root_cause_recommendation} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('capa_recommendation')}>
          <ReadOnlyField 
            label="CAPA Recommendation" 
            value={complaint.capa_recommendation} 
          />
        </UpdateHighlight>
      </div>
      <div className="details-full-width" style={{ marginTop: '1rem' }}>
        <UpdateHighlight isUpdated={isUpdated('risk_reasoning')}>
          <ReadOnlyField 
            label="Risk Reasoning" 
            value={complaint.risk_reasoning} 
          />
        </UpdateHighlight>
      </div>
    </div>
  );
};
