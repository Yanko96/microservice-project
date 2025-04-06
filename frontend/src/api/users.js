import api from './auth';

// 获取用户资料
export const fetchUserProfile = async (username) => {
  try {
    const response = await api.get(`/users/${username}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching user profile for ${username}:`, error);
    throw error;
  }
};

// 获取当前用户资料
export const fetchCurrentUserProfile = async () => {
  try {
    const response = await api.get('/users/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching current user profile:', error);
    throw error;
  }
};

// 更新用户资料
export const updateUserProfile = async (userData) => {
  try {
    const response = await api.put('/users/me', userData);
    return response.data;
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

// 上传头像
export const uploadAvatar = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/users/me/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading avatar:', error);
    throw error;
  }
};

// 关注用户
export const followUser = async (userId) => {
  try {
    const response = await api.post(`/users/follow/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error following user ${userId}:`, error);
    throw error;
  }
};

// 取消关注用户
export const unfollowUser = async (userId) => {
  try {
    const response = await api.delete(`/users/follow/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error unfollowing user ${userId}:`, error);
    throw error;
  }
};

// 获取用户的关注者
export const fetchUserFollowers = async (username, page = 1, size = 10) => {
  try {
    const response = await api.get(`/users/${username}/followers?page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching followers for ${username}:`, error);
    throw error;
  }
};

// 获取用户关注的人
export const fetchUserFollowing = async (username, page = 1, size = 10) => {
  try {
    const response = await api.get(`/users/${username}/following?page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching following for ${username}:`, error);
    throw error;
  }
};

// 获取用户的帖子
export const fetchUserPosts = async (username, page = 1, size = 10) => {
  try {
    const response = await api.get(`/posts/?user_id=${username}&page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching posts for ${username}:`, error);
    throw error;
  }
};