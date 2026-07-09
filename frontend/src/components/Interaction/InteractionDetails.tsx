import React, { useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '../../redux/hooks';
import { clearUpdatedFields } from '../../redux/interactionSlice';
import { ReadOnlyField } from '../Common/ReadOnlyField';
import { UpdateHighlight } from './UpdateHighlight';
import './Interaction.css';

export const InteractionDetails: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currentInteraction, lastUpdatedFields } = useAppSelector((state) => state.interaction);

  const handleHighlightEnd = useCallback(() => {
    if (lastUpdatedFields.length > 0) {
      dispatch(clearUpdatedFields());
    }
  }, [dispatch, lastUpdatedFields]);

  const isUpdated = (field: string) => lastUpdatedFields.includes(field);
  const listValue = (items?: string[]) => items && items.length > 0 ? items.join(', ') : undefined;

  if (!currentInteraction) {
    return <div className="interaction-empty">No interaction selected.</div>;
  }

  return (
    <div className="interaction-details">
      <h2 className="section-title">Interaction Details</h2>
      <div className="details-grid">
        <UpdateHighlight isUpdated={isUpdated('hcp_name')} onHighlightEnd={handleHighlightEnd}>
          <ReadOnlyField 
            label="HCP Name" 
            value={currentInteraction.hcp_name} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('interaction_date')}>
          <ReadOnlyField 
            label="Date" 
            value={currentInteraction.interaction_date} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('interaction_time')}>
          <ReadOnlyField 
            label="Time" 
            value={currentInteraction.interaction_time} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('interaction_type')}>
          <ReadOnlyField 
            label="Type" 
            value={currentInteraction.interaction_type} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('status')}>
          <ReadOnlyField 
            label="Status" 
            value={currentInteraction.status} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('follow_up_required')}>
          <ReadOnlyField 
            label="Follow-up Required" 
            value={currentInteraction.follow_up_required ? 'Yes' : 'No'} 
          />
        </UpdateHighlight>
        <UpdateHighlight isUpdated={isUpdated('sentiment')}>
          <ReadOnlyField 
            label="HCP Sentiment" 
            value={currentInteraction.sentiment} 
          />
        </UpdateHighlight>
        {currentInteraction.follow_up_required && (
          <UpdateHighlight isUpdated={isUpdated('follow_up_date')}>
            <ReadOnlyField 
              label="Follow-up Date" 
              value={currentInteraction.follow_up_date} 
            />
          </UpdateHighlight>
        )}
      </div>
      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('topics_discussed')}>
          <ReadOnlyField 
            label="Topics Discussed" 
            value={listValue(currentInteraction.topics_discussed)} 
          />
        </UpdateHighlight>
      </div>
      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('attendees')}>
          <ReadOnlyField 
            label="Attendees" 
            value={listValue(currentInteraction.attendees)} 
          />
        </UpdateHighlight>
      </div>
      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('materials_shared')}>
          <ReadOnlyField 
            label="Materials Shared" 
            value={listValue(currentInteraction.materials_shared)} 
          />
        </UpdateHighlight>
      </div>
      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('discussion_summary')}>
          <ReadOnlyField 
            label="Discussion Summary" 
            value={currentInteraction.discussion_summary} 
          />
        </UpdateHighlight>
      </div>
      <div className="details-full-width">
        <UpdateHighlight isUpdated={isUpdated('follow_up_date')}>
          <ReadOnlyField 
            label="Follow-up Actions" 
            value={currentInteraction.follow_up_required
              ? currentInteraction.follow_up_date
                ? `Follow up on ${currentInteraction.follow_up_date}`
                : 'Follow-up required'
              : undefined}
          />
        </UpdateHighlight>
      </div>
    </div>
  );
};
