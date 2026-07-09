import { apiClient } from './api';
import { InteractionDraft } from '../types/interaction';
import { APIResponse } from '../types/api';

export const interactionService = {
  async getInteraction(id: string): Promise<APIResponse<InteractionDraft>> {
    const response = await apiClient.get<APIResponse<InteractionDraft>>(`/interactions/${id}`);
    return response.data;
  }
};
