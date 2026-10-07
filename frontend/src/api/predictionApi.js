import { apiClient } from './client';

export const predictionApi = {
  predictPayload: async (payload) => {
    return apiClient.post('/prediction', payload);
  },

  predictUpload: async (file, itemLabel = '', minConfidence = 0.60) => {
    const formData = new FormData();
    formData.append('file', file);
    if (itemLabel) {
      formData.append('item_label', itemLabel);
    }
    formData.append('min_confidence', minConfidence);

    return apiClient.post('/prediction/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};
