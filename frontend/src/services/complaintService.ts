import { apiClient } from './api';
import { ComplaintDraft } from '../types/complaint';
import { APIResponse } from '../types/api';

export const complaintService = {
  async getComplaint(id: string): Promise<APIResponse<ComplaintDraft>> {
    const response = await apiClient.get<APIResponse<ComplaintDraft>>(`/complaints/${id}`);
    return response.data;
  }
};
