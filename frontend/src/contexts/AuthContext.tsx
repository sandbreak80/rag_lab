/**
 * Authentication Context
 * Fast Track Phase 7 - Week 9 Day 6-7
 *
 * Manages user authentication state, tokens, and auth operations
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

// Auth service base URL
const AUTH_SERVICE_URL = '/api/auth';  // Proxied through API Gateway

interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  created_at: string;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token storage keys
const ACCESS_TOKEN_KEY = 'rag_access_token';
const REFRESH_TOKEN_KEY = 'rag_refresh_token';
const USER_KEY = 'rag_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load auth state from localStorage on mount
  useEffect(() => {
    const storedAccessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedAccessToken && storedUser) {
      setAccessToken(storedAccessToken);
      setRefreshToken(storedRefreshToken);
      setUser(JSON.parse(storedUser));
    }

    setIsLoading(false);
  }, []);

  // Save auth state to localStorage
  const saveAuthState = (access: string, refresh: string | null, userData: User) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    if (refresh) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    }
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
    setAccessToken(access);
    setRefreshToken(refresh);
    setUser(userData);
  };

  // Clear auth state
  const clearAuthState = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  };

  // Login
  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post(`${AUTH_SERVICE_URL}/login`, {
        username,
        password,
      });

      const { access_token, refresh_token, user: userData } = response.data;

      saveAuthState(access_token, refresh_token, userData);

      console.log('✅ Login successful:', userData.username);
    } catch (error: any) {
      console.error('❌ Login failed:', error.response?.data?.error || error.message);
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  };

  // Register
  const register = async (username: string, email: string, password: string) => {
    try {
      const response = await axios.post(`${AUTH_SERVICE_URL}/register`, {
        username,
        email,
        password,
      });

      console.log('✅ Registration successful:', response.data.user.username);

      // Auto-login after registration
      await login(username, password);
    } catch (error: any) {
      console.error('❌ Registration failed:', error.response?.data?.error || error.message);
      throw new Error(error.response?.data?.error || 'Registration failed');
    }
  };

  // Logout
  const logout = () => {
    clearAuthState();
    console.log('✅ Logged out');
  };

  // Refresh access token
  const refreshAccessToken = async () => {
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(
        `${AUTH_SERVICE_URL}/refresh`,
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        }
      );

      const { access_token } = response.data;

      localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
      setAccessToken(access_token);

      console.log('✅ Access token refreshed');
    } catch (error: any) {
      console.error('❌ Token refresh failed:', error);
      // If refresh fails, logout user
      logout();
      throw new Error('Session expired. Please login again.');
    }
  };

  // Update profile
  const updateProfile = async (data: Partial<User>) => {
    if (!accessToken) {
      throw new Error('Not authenticated');
    }

    try {
      const response = await axios.put(
        `${AUTH_SERVICE_URL}/profile`,
        data,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      const updatedUser = response.data.user;

      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
      setUser(updatedUser);

      console.log('✅ Profile updated');
    } catch (error: any) {
      console.error('❌ Profile update failed:', error);
      throw new Error(error.response?.data?.error || 'Profile update failed');
    }
  };

  // Change password
  const changePassword = async (oldPassword: string, newPassword: string) => {
    if (!accessToken) {
      throw new Error('Not authenticated');
    }

    try {
      await axios.post(
        `${AUTH_SERVICE_URL}/change_password`,
        {
          old_password: oldPassword,
          new_password: newPassword,
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        }
      );

      console.log('✅ Password changed');
    } catch (error: any) {
      console.error('❌ Password change failed:', error);
      throw new Error(error.response?.data?.error || 'Password change failed');
    }
  };

  const value: AuthContextType = {
    user,
    accessToken,
    refreshToken,
    isAuthenticated: !!user && !!accessToken,
    isLoading,
    login,
    register,
    logout,
    refreshAccessToken,
    updateProfile,
    changePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

// Axios interceptor to add auth token to requests
export function setupAxiosInterceptors() {
  axios.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem(ACCESS_TOKEN_KEY);

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle token expiration
  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // If 401 and not already retried, try to refresh token
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

          if (refreshToken) {
            const response = await axios.post(
              `${AUTH_SERVICE_URL}/refresh`,
              {},
              {
                headers: {
                  Authorization: `Bearer ${refreshToken}`,
                },
              }
            );

            const { access_token } = response.data;

            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);

            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return axios(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, clear auth state
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          localStorage.removeItem(USER_KEY);

          // Redirect to login
          window.location.href = '/login';
        }
      }

      return Promise.reject(error);
    }
  );
}

