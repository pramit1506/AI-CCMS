import { apiClient } from './api';
import { APIResponse } from '../types/api';

export const uploadService = {
  async extractText(file: File): Promise<APIResponse<{text: string, filename: string}>> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<APIResponse<{text: string, filename: string}>>(`/upload/extract-text`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};
