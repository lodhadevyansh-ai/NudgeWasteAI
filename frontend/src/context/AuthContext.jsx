import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('nudgewaste_token'));
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Logout handler
  const logout = useCallback(() => {
    localStorage.removeItem('nudgewaste_token');
    setToken(null);
    setUser(null);
    setAuthError(null);
  }, []);

  // Helper to fetch & update authoritative user state from backend
  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      setAuthError(null);
      return userData;
    } catch (err) {
      console.warn('Failed to restore user session:', err);
      logout();
      throw err;
    }
  }, [logout]);

  // On initial mount or token change, restore session if token exists
  useEffect(() => {
    let isMounted = true;

    const restoreSession = async () => {
      const storedToken = localStorage.getItem('nudgewaste_token');
      if (!storedToken) {
        if (isMounted) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const userData = await authApi.getCurrentUser();
        if (isMounted) {
          setUser(userData);
          setToken(storedToken);
          setAuthError(null);
        }
      } catch (err) {
        console.warn('Session restoration failed:', err);
        if (isMounted) {
          localStorage.removeItem('nudgewaste_token');
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    restoreSession();

    // Listen for custom auth expiry event from client interceptor
    const handleExpired = () => {
      if (isMounted) {
        setToken(null);
        setUser(null);
        setAuthError('Your session has expired. Please sign in again.');
      }
    };
    window.addEventListener('auth:expired', handleExpired);

    return () => {
      isMounted = false;
      window.removeEventListener('auth:expired', handleExpired);
    };
  }, []);

  // Login handler
  const login = async (email, password) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const tokenRes = await authApi.login({ email, password });
      const accessToken = tokenRes.access_token;

      localStorage.setItem('nudgewaste_token', accessToken);
      setToken(accessToken);

      // Fetch user profile from backend as single source of truth
      const userProfile = await authApi.getCurrentUser();
      setUser(userProfile);
      setIsLoading(false);
      return userProfile;
    } catch (err) {
      setIsLoading(false);
      const msg = err.message || 'Invalid email or password';
      setAuthError(msg);
      throw err;
    }
  };

  // Register handler
  const register = async (registerData) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      // 1. Create user on backend
      await authApi.register(registerData);

      // 2. Automatically log in user to get JWT token
      const tokenRes = await authApi.login({
        email: registerData.email,
        password: registerData.password,
      });

      const accessToken = tokenRes.access_token;
      localStorage.setItem('nudgewaste_token', accessToken);
      setToken(accessToken);

      // 3. Fetch user profile from backend (will contain 500 initial Swachh Credits)
      const userProfile = await authApi.getCurrentUser();
      setUser(userProfile);
      setIsLoading(false);
      return userProfile;
    } catch (err) {
      setIsLoading(false);
      const msg = err.message || 'Registration failed. Please check your inputs.';
      setAuthError(msg);
      throw err;
    }
  };

  // Delete Account handler
  const deleteAccount = async () => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const res = await authApi.deleteAccount();
      // Clear all cached tokens and session state
      localStorage.removeItem('nudgewaste_token');
      localStorage.removeItem('nudgewaste_mock_user');
      localStorage.removeItem('nudgewaste_mock_disposals');
      localStorage.removeItem('nudgewaste_mock_redemptions');
      setToken(null);
      setUser(null);
      setIsLoading(false);
      return res;
    } catch (err) {
      setIsLoading(false);
      const msg = err.message || 'Unable to delete your account. Please try again.';
      setAuthError(msg);
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        authError,
        login,
        register,
        logout,
        deleteAccount,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
