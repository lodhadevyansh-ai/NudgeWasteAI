import { apiClient } from './client';

export const userApi = {
  getProfile: async () => {
    return apiClient.get('/users/me');
  },
  deleteAccount: async () => {
    return apiClient.delete('/users/me');
  },
};
