import { apiClient } from './client';

export const rewardsApi = {
  getCatalog: async () => {
    return apiClient.get('/rewards');
  },

  redeemReward: async (rewardId) => {
    return apiClient.post(`/rewards/redeem/${rewardId}`);
  },

  getMyRedemptions: async () => {
    return apiClient.get('/rewards/my-redemptions');
  },
};
