import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ComplaintDraft } from '../types/complaint';

interface ComplaintState {
  currentComplaint: ComplaintDraft | null;
  lastUpdatedFields: string[];
  extractionStatus: 'idle' | 'extracting' | 'completed' | 'error';
}

const initialState: ComplaintState = {
  currentComplaint: {},
  lastUpdatedFields: [],
  extractionStatus: 'idle',
};

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setComplaint: (state, action: PayloadAction<{ draft: ComplaintDraft | null; updatedFields: string[] }>) => {
      state.currentComplaint = action.payload.draft;
      state.lastUpdatedFields = action.payload.updatedFields;
    },
    clearUpdatedFields: (state) => {
      state.lastUpdatedFields = [];
    },
    clearComplaint: (state) => {
      state.currentComplaint = {};
      state.lastUpdatedFields = [];
      state.extractionStatus = 'idle';
    },
    setExtractionStatus: (state, action: PayloadAction<'idle' | 'extracting' | 'completed' | 'error'>) => {
      state.extractionStatus = action.payload;
    }
  }
});

export const { setComplaint, clearUpdatedFields, clearComplaint, setExtractionStatus } = complaintSlice.actions;
export default complaintSlice.reducer;
