import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AgentState, TimelineEvent, ClarificationPayload, ToolExecutionEvent, ConversationStatus } from '../types/agent';

const initialState: AgentState = {
  graphExecutionId: null,
  selectedTool: null,
  toolStatus: 'idle',
  clarificationRequired: null,
  currentStep: null,
  executionTimeline: [],
  lastToolResult: null,
  conversationStatus: undefined,
};

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    setGraphExecutionId: (state, action: PayloadAction<string>) => {
      state.graphExecutionId = action.payload;
    },
    setToolExecutionStart: (state, action: PayloadAction<{ toolName: string }>) => {
      state.selectedTool = action.payload.toolName;
      state.toolStatus = 'executing';
      state.executionTimeline.push({
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        title: `Executing ${action.payload.toolName}`,
        status: 'executing'
      });
    },
    setToolExecutionResult: (state, action: PayloadAction<ToolExecutionEvent>) => {
      state.toolStatus = action.payload.status;
      state.lastToolResult = action.payload.result;
      
      const lastEvent = state.executionTimeline[state.executionTimeline.length - 1];
      if (lastEvent && lastEvent.status === 'executing') {
        lastEvent.status = action.payload.status;
        lastEvent.description = action.payload.error || 'Execution completed successfully.';
      } else {
        state.executionTimeline.push({
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          title: `Executed ${action.payload.tool_name}`,
          description: action.payload.error || 'Execution completed successfully.',
          status: action.payload.status
        });
      }
    },
    setClarificationRequired: (state, action: PayloadAction<ClarificationPayload | null>) => {
      state.clarificationRequired = action.payload;
    },
    setConversationStatus: (state, action: PayloadAction<ConversationStatus | string>) => {
      state.conversationStatus = action.payload as ConversationStatus;
    },
    addTimelineEvent: (state, action: PayloadAction<TimelineEvent>) => {
      state.executionTimeline.push(action.payload);
    },
    clearAgentState: (state) => {
      state.graphExecutionId = null;
      state.selectedTool = null;
      state.toolStatus = 'idle';
      state.clarificationRequired = null;
      state.currentStep = null;
      state.executionTimeline = [];
      state.lastToolResult = null;
      state.conversationStatus = undefined;
    }
  }
});

export const {
  setGraphExecutionId,
  setToolExecutionStart,
  setToolExecutionResult,
  setClarificationRequired,
  setConversationStatus,
  addTimelineEvent,
  clearAgentState
} = agentSlice.actions;

export default agentSlice.reducer;
