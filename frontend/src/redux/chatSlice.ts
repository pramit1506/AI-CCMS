import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { ChatMessage, ChatRequest, ConversationResponse } from '../types/chat';
import { chatService } from '../services/chatService';
import { RootState } from './store';
import { conversationMapper } from '../services/conversationMapper';
import { setClarificationRequired, setToolExecutionResult, setConversationStatus } from './agentSlice';
import { setInteraction } from './interactionSlice';

interface ChatState {
  messages: ChatMessage[];
  conversationId: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  conversationId: null,
  loading: false,
  error: null,
};

export const sendMessage = createAsyncThunk<
  ConversationResponse,
  string,
  { state: RootState }
>(
  'chat/sendMessage',
  async (message: string, { getState, dispatch, rejectWithValue }) => {
    try {
      const state = getState();
      const history = state.chat.messages.map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const request: ChatRequest = {
        user_message: message,
        conversation_id: state.chat.conversationId || undefined,
        message_history: history
      };
      
      const response = await chatService.sendMessage(request);
      const data = response.data;

      // Use the centralized mapper
      const mapped = conversationMapper.mapResponse(data);

      // Dispatch mapped data to agentSlice
      dispatch(setClarificationRequired(mapped.clarificationRequired));
      if (mapped.toolExecution) {
        dispatch(setToolExecutionResult(mapped.toolExecution));
      }
      dispatch(setConversationStatus(mapped.conversationStatus));

      // Dispatch mapped data to interactionSlice
      dispatch(setInteraction({
        draft: mapped.interactionDraft,
        updatedFields: mapped.updatedFields
      }));

      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to send message');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage: (state, action: PayloadAction<string>) => {
      state.messages.push({
        id: Date.now().toString(),
        role: 'user',
        content: action.payload,
        timestamp: new Date().toISOString()
      });
    },
    clearChat: (state) => {
      state.messages = [];
      state.conversationId = null;
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        
        const mapped = conversationMapper.mapResponse(action.payload);
        
        state.conversationId = mapped.conversationId;
        state.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: mapped.assistantMessage,
          timestamp: new Date().toISOString(),
          tool_executions: mapped.toolExecution ? [mapped.toolExecution] : undefined,
          clarification_request: mapped.clarificationRequired || undefined
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { addUserMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;
