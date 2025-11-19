import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { message } from 'antd';
import { getApiBaseUrl } from '../config/api';
import { logger } from '../utils/logger';
import { profileApi, type UserProfileUpdatePayload } from '../api/profile';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: 'ADMIN' | 'FOUNDER' | 'MANAGER' | 'USER' | 'ACCOUNTANT' | 'REQUESTER';
  is_active: boolean;
  is_verified: boolean;
  department_id: number | null;
  position: string | null;
  phone: string | null;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  updateProfile: (updates: UserProfileUpdatePayload) => Promise<User>;
  isAuthenticated: boolean;
  hasRole: (role: string | string[]) => boolean;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  department_id?: number;
  position?: string;
  phone?: string;
  role?: 'ADMIN' | 'FOUNDER' | 'MANAGER' | 'USER' | 'ACCOUNTANT' | 'REQUESTER';
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = useCallback(async (options?: { silent?: boolean }) => {
    const savedToken = localStorage.getItem('token');

    if (!savedToken) {
      if (!options?.silent) {
        setLoading(false);
      }
      return null;
    }

    if (!options?.silent) {
      setLoading(true);
    }

    try {
      const currentUser = await profileApi.getCurrent();
      setUser(currentUser);
      setToken(savedToken);
      logger.auth('User loaded successfully', { username: currentUser.username });
      return currentUser;
    } catch (error) {
      logger.error('[Auth] Failed to load user:', error);
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      return null;
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }, []);

  // Load user on mount if token exists
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Listen for unauthorized events from API interceptor
  useEffect(() => {
    const handleUnauthorized = () => {
      logger.auth('Received unauthorized event, logging out');
      setUser(null);
      setToken(null);
      localStorage.removeItem('token');
      // Don't show message here as it's handled by the interceptor
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();

      // Save token to localStorage FIRST, before updating state
      localStorage.setItem('token', data.access_token);
      logger.auth('Token saved to localStorage');

      setToken(data.access_token);
      setUser(data.user);

      message.success('Successfully logged in!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      message.error(errorMessage);
      throw error;
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      await response.json();

      message.success('Registration successful! Please login.');

      // Auto-login after registration
      await login(userData.username, userData.password);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      message.error(errorMessage);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    message.info('Logged out successfully');
  };

  const refreshUser = async () => {
    await fetchCurrentUser({ silent: true });
  };

  const updateProfile = async (updates: UserProfileUpdatePayload) => {
    try {
      const updatedUser = await profileApi.updateProfile(updates);
      setUser(updatedUser);
      message.success('Профиль обновлен');
      return updatedUser;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Не удалось обновить профиль';
      message.error(errorMessage);
      logger.error('[Auth] Failed to update profile:', error);
      throw error;
    }
  };

  const hasRole = (role: string | string[]): boolean => {
    if (!user) return false;

    if (Array.isArray(role)) {
      return role.includes(user.role);
    }

    return user.role === role;
  };

  // Check both React state AND localStorage to handle race conditions
  // This is important when login() updates localStorage synchronously but state asynchronously
  const isAuthenticated = (!!user && !!token) || !!localStorage.getItem('token');

  logger.debug('[AuthContext] State:', { hasUser: !!user, hasToken: !!token, isAuthenticated, loading });

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
    isAuthenticated,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
