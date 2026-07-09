import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { InteractionDraft } from '../types/interaction';

interface InteractionState {
  currentInteraction: InteractionDraft | null;
  lastUpdatedFields: string[];
}

const initialState: InteractionState = {
  currentInteraction: null,
  lastUpdatedFields: []
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setInteraction: (state, action: PayloadAction<{ draft: InteractionDraft | null; updatedFields: string[] }>) => {
      state.currentInteraction = action.payload.draft;
      state.lastUpdatedFields = action.payload.updatedFields;
    },
    clearUpdatedFields: (state) => {
      state.lastUpdatedFields = [];
    }
  }
});

export const { setInteraction, clearUpdatedFields } = interactionSlice.actions;
export default interactionSlice.reducer;
