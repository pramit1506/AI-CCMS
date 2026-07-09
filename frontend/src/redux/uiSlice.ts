import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
  theme: 'light' | 'dark';
  notifications: { id: string; message: string; type: 'success' | 'error' | 'info' }[];
}

const initialState: UiState = {
  theme: 'light',
  notifications: []
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<{ message: string; type: 'success' | 'error' | 'info' }>) => {
      state.notifications.push({ id: Date.now().toString(), ...action.payload });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    }
  }
});

export const { addNotification, removeNotification } = uiSlice.actions;
export default uiSlice.reducer;
