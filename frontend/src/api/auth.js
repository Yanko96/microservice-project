import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost/api/v1';

// 设置 axios 实例
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器添加认证 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 登录用户
export const loginUser = async (credentials) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return {
      token: response.data.access_token,
      user: response.data.user
    };
  } catch (error) {
    throw handleApiError(error);
  }
};

// 注册用户
export const registerUser = async (userData) => {
  try {
    const response = await api.post('/auth/register', userData);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// 获取当前用户信息
export const getCurrentUser = async () => {
  try {
    const response = await api.get('/users/me');
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// 处理 API 错误
const handleApiError = (error) => {
  if (error.response) {
    // 服务器返回了错误状态码
    const message = error.response.data.detail || error.response.data.message || '请求失败';
    return new Error(message);
  } else if (error.request) {
    // 请求发送了，但没有收到响应
    return new Error('无法连接到服务器，请检查网络连接');
  } else {
    // 请求设置时发生错误
    return new Error('请求出错');
  }
};

export default api;