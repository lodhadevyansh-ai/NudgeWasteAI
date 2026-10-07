import { apiClient } from './client';

export const authApi = {
  login: async (credentials) => {
    return apiClient.post('/users/login', credentials);
  },

  register: async (userData) => {
    return apiClient.post('/users/register', userData);
  },

  getCurrentUser: async () => {
    return apiClient.get('/users/me');
  },

  deleteAccount: async () => {
    return apiClient.delete('/users/me');
  },
};
