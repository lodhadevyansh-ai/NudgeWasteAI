import { apiClient } from './client';

export const disposalApi = {
  recordDisposal: async (disposalData) => {
    return apiClient.post('/disposal', disposalData);
  },

  getHistory: async (limit = 50, skip = 0) => {
    return apiClient.get('/disposal/history', {
      params: { limit, skip },
    });
  },

  getDisposalById: async (disposalId) => {
    return apiClient.get(`/disposal/${disposalId}`);
  },
};
