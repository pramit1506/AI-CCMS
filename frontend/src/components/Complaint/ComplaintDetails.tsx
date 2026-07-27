import React, { useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '../../redux/hooks';
import { clearUpdatedFields, clearComplaint } from '../../redux/complaintSlice';
import { addUserMessage, clearChat, sendMessage } from '../../redux/chatSlice';
import { ReadOnlyField } from '../Common/ReadOnlyField';
import { UpdateHighlight } from './UpdateHighlight';
import { RiskAssessment } from './RiskAssessment';
import './Complaint.css';

export const ComplaintDetails: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currentComplaint, lastUpdatedFields } = useAppSelector((state) => state.complaint);

  const handleHighlightEnd = useCallback(() => {
    if (lastUpdatedFields.length > 0) {
      dispatch(clearUpdatedFields());
    }
  }, [dispatch, lastUpdatedFields]);

  const handleSave = () => {
    dispatch(addUserMessage('Save complaint'));
    dispatch(sendMessage('Save complaint'));
  };

  const handleReset = () => {
    dispatch(clearComplaint());
    dispatch(clearChat());
  };

  const isUpdated = (field: string) => lastUpdatedFields.includes(field);

  const complaint = currentComplaint || {};

  return (
    <div className="complaint-details">
      <h2 className="section-title">Complaint Details</h2>
      <div className="details-grid">
        <UpdateHighlight isUpdated={isUpdated('customer_name')} onHighlightEnd={handleHighlightEnd}>
          <ReadOnlyField 
            label="Customer Name" 
            value={complaint.customer_name} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('complaint_date')}>
          <ReadOnlyField 
            label="Date" 
            value={complaint.complaint_date} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('complaint_source')}>
          <ReadOnlyField 
            label="Source" 
            value={complaint.complaint_source} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('complaint_type')}>
          <ReadOnlyField 
            label="Type" 
            value={complaint.complaint_type} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('status')}>
          <ReadOnlyField 
            label="Status" 
            value={complaint.status} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('initial_severity')}>
          <ReadOnlyField 
            label="Severity" 
            value={complaint.initial_severity} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('priority')}>
          <ReadOnlyField 
            label="Priority" 
            value={complaint.priority} 
          />
        </UpdateHighlight>
      </div>
      
      <h3 className="section-subtitle">Product Details</h3>
      <div className="details-grid">
        <UpdateHighlight isUpdated={isUpdated('product_name')}>
          <ReadOnlyField 
            label="Product Name" 
            value={complaint.product_name} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('product_strength')}>
          <ReadOnlyField 
            label="Product Strength" 
            value={complaint.product_strength} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('batch_number')}>
          <ReadOnlyField 
            label="Batch Number" 
            value={complaint.batch_number} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('manufacturing_date')}>
          <ReadOnlyField 
            label="Mfg Date" 
            value={complaint.manufacturing_date} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('expiry_date')}>
          <ReadOnlyField 
            label="Expiry Date" 
            value={complaint.expiry_date} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('quantity_affected')}>
          <ReadOnlyField 
            label="Quantity Affected" 
            value={complaint.quantity_affected} 
          />
        </UpdateHighlight>
      </div>

      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('detailed_description')}>
          <ReadOnlyField 
            label="Detailed Description" 
            value={complaint.detailed_description} 
          />
        </UpdateHighlight>
      </div>

      <RiskAssessment />

      <div className="complaint-actions" style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
        <button className="primary-button" onClick={handleSave}>Save Complaint</button>
        <button className="secondary-button" onClick={handleReset}>Reset Form</button>
      </div>
    </div>
  );
};
