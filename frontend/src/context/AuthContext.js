import React, { createContext, useState, useEffect } from 'react';
import { loginUser, registerUser, getCurrentUser } from '../api/auth';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // 页面加载时检查本地存储的令牌
    const token = localStorage.getItem('token');
    if (token) {
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, []);
  
  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const user = await getCurrentUser();
      setCurrentUser(user);
      setError(null);
    } catch (err) {
      console.error('Auth check failed:', err);
      setError(err.message);
      // 如果验证失败，清除本地令牌
      localStorage.removeItem('token');
      setCurrentUser(null);
    } finally {
      setLoading(false);
    }
  };
  
  const login = async (credentials) => {
    try {
      setLoading(true);
      const { token, user } = await loginUser(credentials);
      // 保存令牌到本地存储
      localStorage.setItem('token', token);
      setCurrentUser(user);
      setError(null);
      return user;
    } catch (err) {
      setError(err.message || '登录失败');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const register = async (userData) => {
    try {
      setLoading(true);
      const newUser = await registerUser(userData);
      return newUser;
    } catch (err) {
      setError(err.message || '注册失败');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };
  
  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    checkAuthStatus
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};