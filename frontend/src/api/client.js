import axios from 'axios';
import { handleMockRequest } from './mockService';

// Get API base URL from Vite environment variable with safe localhost fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30s timeout for ML model prediction calls
});

// Request Interceptor: Attach JWT Bearer Token if available in localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('nudgewaste_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Ensure API prefix /api/v1 is handled if required, or keep relative URL clean
    if (!config.url.startsWith('/api/v1') && !config.url.startsWith('/health')) {
      config.url = `/api/v1${config.url.startsWith('/') ? config.url : '/' + config.url}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Unified Error Handling
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const status = error.response?.status;

    // Detect if backend is offline/unreachable (network error, refused connection, timeout, 502/503/504)
    if (
      !error.response ||
      error.message === 'Network Error' ||
      error.code === 'ERR_NETWORK' ||
      error.code === 'ECONNREFUSED' ||
      error.code === 'ECONNABORTED' ||
      status === 502 ||
      status === 503 ||
      status === 504
    ) {
      return Promise.reject({
        status: 503,
        message: 'Unable to connect to NudgeWasteAI services. Please ensure the backend server is running.',
        raw: error,
      });
    }

    let message = 'An unexpected error occurred. Please try again.';

    if (error.response?.data) {
      const data = error.response.data;
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (data.error?.message) {
        message = data.error.message;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((err) => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
      }
    }

    if (status === 401) {
      // Clear token on 401 Unauthorized if token expired
      const token = localStorage.getItem('nudgewaste_token');
      if (token) {
        localStorage.removeItem('nudgewaste_token');
        // Dispatch event so AuthContext can handle logout/session expiry
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }
    }

    return Promise.reject({
      status: status || 500,
      message,
      raw: error,
    });
  }
);

