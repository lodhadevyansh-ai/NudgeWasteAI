import { apiClient } from './client';

export const creditsApi = {
  getBalance: async () => {
    return apiClient.get('/credits');
  },

  getHistory: async (limit = 50, skip = 0) => {
    return apiClient.get('/credits/history', {
      params: { limit, skip },
    });
  },
};
