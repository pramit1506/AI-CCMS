import { configureStore } from '@reduxjs/toolkit';
import uiReducer from './uiSlice';
import complaintReducer from './complaintSlice';
import chatReducer from './chatSlice';
import agentReducer from './agentSlice';

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    complaint: complaintReducer,
    chat: chatReducer,
    agent: agentReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
