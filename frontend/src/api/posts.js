import api from './auth';

// 获取帖子列表
export const fetchPosts = async (page = 1, size = 10) => {
  try {
    const response = await api.get(`/posts/?page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching posts:', error);
    throw error;
  }
};

// 获取单个帖子详情
export const fetchPostById = async (postId) => {
  try {
    const response = await api.get(`/posts/${postId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching post ${postId}:`, error);
    throw error;
  }
};

// 创建新帖子 - 纯文本
export const createPost = async (postData) => {
  console.log('[创建帖子] payload:', JSON.stringify(postData, null, 2));
  
  try {
    const formData = new FormData();
    formData.append('content', postData.content);
    formData.append('visibility', postData.visibility || 'PUBLIC');
    
    if (postData.location) {
      formData.append('location', postData.location);
    }

    if (postData.tag_names) {
      formData.append('tag_names', postData.tag_names);
    }
    for (let pair of formData.entries()) {
      console.log(pair[0] + ': ' + pair[1]);
    }

    const response = await api.post('/posts/text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    return response.data;
  } catch (error) {
    console.error('Error creating post:', error);
    throw error;
  }
};


// 创建新帖子 - 带媒体文件
export const createMediaPost = async (postData, files) => {
  try {
    const formData = new FormData();
    
    formData.append('visibility', postData.visibility || 'PUBLIC');
    
    if (postData.location) {
      formData.append('location', postData.location);
    }
    
    if (postData.tag_names) {
      formData.append('tag_names', postData.tag_names);
    }
    
    // 添加媒体文件
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    const response = await api.post('/posts/media', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error creating media post:', error);
    throw error;
  }
};

// 更新帖子
export const updatePost = async (postId, postData) => {
  try {
    const response = await api.put(`/posts/${postId}`, postData);
    return response.data;
  } catch (error) {
    console.error(`Error updating post ${postId}:`, error);
    throw error;
  }
};

// 删除帖子
export const deletePost = async (postId) => {
  try {
    await api.delete(`/posts/${postId}`);
    return true;
  } catch (error) {
    console.error(`Error deleting post ${postId}:`, error);
    throw error;
  }
};

// 点赞/取消点赞帖子
export const likePost = async (postId) => {
  try {
    const response = await api.post('/reactions/', {
      post_id: postId,
      type: 'like'
    });
    return response.data;
  } catch (error) {
    console.error(`Error liking post ${postId}:`, error);
    throw error;
  }
};

// 获取帖子评论
export const fetchPostComments = async (postId, page = 1, size = 10) => {
  try {
    const response = await api.get(`/comments/post/${postId}?page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching comments for post ${postId}:`, error);
    throw error;
  }
};

// 创建评论
export const createComment = async (commentData) => {
  try {
    const response = await api.post('/comments/', commentData);
    return response.data;
  } catch (error) {
    console.error('Error creating comment:', error);
    throw error;
  }
};

// 搜索帖子
export const searchPosts = async (query, page = 1, size = 10) => {
  try {
    const response = await api.get(`/search/?query=${encodeURIComponent(query)}&page=${page}&size=${size}`);
    return response.data;
  } catch (error) {
    console.error('Error searching posts:', error);
    throw error;
  }
};