import { apiClient } from './client';

export const analyticsApi = {
  getUserSummary: async () => {
    return apiClient.get('/analytics/user');
  },

  getPlatformSummary: async () => {
    return apiClient.get('/analytics/summary');
  },

  getWasteDistribution: async () => {
    return apiClient.get('/analytics/waste-distribution');
  },

  getTrends: async (days = 30) => {
    return apiClient.get('/analytics/trends', {
      params: { days },
    });
  },

  getCreditsAnalytics: async () => {
    return apiClient.get('/analytics/credits');
  },
};
