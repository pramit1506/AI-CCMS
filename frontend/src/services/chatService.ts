import { apiClient } from './api';
import { ChatRequest, ConversationResponse } from '../types/chat';
import { APIResponse } from '../types/api';

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<APIResponse<ConversationResponse>> {
    const response = await apiClient.post<APIResponse<ConversationResponse>>('/chat/', request);
    return response.data;
  }
};
