import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { 
  Container, 
  Typography, 
  Box, 
  Paper, 
  Divider,
  Button,
  TextField,
  Avatar,
  Grid,
  CircularProgress,
  Card,
  CardHeader,
  CardContent,
  CardActions,
  IconButton,
  Tab,
  Tabs
} from '@mui/material';
import { 
  FavoriteBorder, 
  Favorite, 
  Comment, 
  Share,
  ImageOutlined,
  Send
} from '@mui/icons-material';
import { fetchPosts, createPost, likePost } from '../api/posts';

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newPostContent, setNewPostContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  
  const { currentUser } = useContext(AuthContext);
  
  useEffect(() => {
    loadPosts();
  }, []);
  
  const loadPosts = async () => {
    setIsLoading(true);
    try {
      const data = await fetchPosts();
      setPosts(data.items);
    } catch (error) {
      console.error('Error loading posts:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNewPostChange = (e) => {
    setNewPostContent(e.target.value);
  };
  
  const handlePostSubmit = async (e) => {
    e.preventDefault();
    
    if (!newPostContent.trim()) return;
    
    setIsSubmitting(true);
    try {
      const newPost = await createPost({
        content: newPostContent,
        visibility: 'PUBLIC'
      });
      
      setPosts([newPost, ...posts]);
      setNewPostContent('');
    } catch (error) {
      console.error('Error creating post:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleLike = async (postId) => {
    try {
      await likePost(postId);
      
      // 更新点赞状态
// 更新点赞状态
setPosts(posts.map(post => {
    if (post.id === postId) {
      const isLiked = post.current_user_reaction === 'like';
      return {
        ...post,
        current_user_reaction: isLiked ? null : 'like',
        like_count: isLiked ? post.like_count - 1 : post.like_count + 1
      };
    }
    return post;
  }));
} catch (error) {
  console.error('Error liking post:', error);
}
};

const handleTabChange = (event, newValue) => {
setTabValue(newValue);
};

if (isLoading && posts.length === 0) {
return (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
    <CircularProgress />
  </Box>
);
}

return (
<Container maxWidth="md" sx={{ py: 4 }}>
  <Grid container spacing={3}>
    <Grid item xs={12} md={8}>
      {/* 创建新帖子区域 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box component="form" onSubmit={handlePostSubmit}>
          <Box display="flex" alignItems="flex-start" mb={2}>
            <Avatar 
              src={currentUser?.avatar_url} 
              alt={currentUser?.username}
              sx={{ mr: 2 }}
            >
              {currentUser?.username?.[0]?.toUpperCase()}
            </Avatar>
            <TextField
              fullWidth
              multiline
              rows={3}
              placeholder="分享你的想法..."
              variant="outlined"
              value={newPostContent}
              onChange={handleNewPostChange}
              disabled={isSubmitting}
            />
          </Box>
          <Box display="flex" justifyContent="space-between">
            <Button
              startIcon={<ImageOutlined />}
              color="primary"
            >
              添加图片
            </Button>
            <Button
              variant="contained"
              color="primary"
              endIcon={<Send />}
              disabled={!newPostContent.trim() || isSubmitting}
              type="submit"
            >
              {isSubmitting ? <CircularProgress size={24} /> : '发布'}
            </Button>
          </Box>
        </Box>
      </Paper>
      
      {/* 动态流标签页 */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="全部" />
          <Tab label="关注" />
          <Tab label="热门" />
        </Tabs>
      </Paper>
      
      {/* 动态列表 */}
      {posts.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary">
            没有找到动态，成为第一个发布动态的人吧！
          </Typography>
        </Paper>
      ) : (
        posts.map(post => (
          <Card key={post.id} sx={{ mb: 3 }}>
            <CardHeader
              avatar={
                <Avatar 
                  src={post.user?.avatar_url} 
                  alt={post.user?.username}
                >
                  {post.user?.username?.[0]?.toUpperCase()}
                </Avatar>
              }
              title={
                <Link to={`/profile/${post.user?.username}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {post.user?.full_name || post.user?.username}
                  </Typography>
                </Link>
              }
              subheader={new Date(post.created_at).toLocaleString()}
            />
            <CardContent>
              <Typography variant="body1" component="p">
                {post.content}
              </Typography>
              {post.media_type !== 'NONE' && post.media_urls && (
                <Box sx={{ mt: 2 }}>
                  {post.media_type === 'IMAGE' && (
                    <img 
                      src={post.media_urls[0]?.url} 
                      alt="Post media" 
                      style={{ maxWidth: '100%', borderRadius: '4px' }}
                    />
                  )}
                </Box>
              )}
            </CardContent>
            <Divider />
            <CardActions disableSpacing>
              <IconButton 
                aria-label="like"
                onClick={() => handleLike(post.id)}
                color={post.current_user_reaction === 'like' ? 'primary' : 'default'}
              >
                {post.current_user_reaction === 'like' ? <Favorite /> : <FavoriteBorder />}
              </IconButton>
              <Typography variant="body2" color="textSecondary">
                {post.like_count}
              </Typography>
              
              <IconButton 
                aria-label="comment"
                component={Link}
                to={`/posts/${post.id}`}
                sx={{ ml: 2 }}
              >
                <Comment />
              </IconButton>
              <Typography variant="body2" color="textSecondary">
                {post.comment_count}
              </Typography>
              
              <IconButton aria-label="share" sx={{ ml: 2 }}>
                <Share />
              </IconButton>
            </CardActions>
          </Card>
        ))
      )}
    </Grid>
    
    {/* 右侧边栏 */}
    <Grid item xs={12} md={4}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          我的个人资料
        </Typography>
        <Box display="flex" alignItems="center" mb={2}>
          <Avatar 
            src={currentUser?.avatar_url} 
            alt={currentUser?.username}
            sx={{ width: 56, height: 56, mr: 2 }}
          >
            {currentUser?.username?.[0]?.toUpperCase()}
          </Avatar>
          <Box>
            <Typography variant="subtitle1" fontWeight="bold">
              {currentUser?.full_name || currentUser?.username}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              @{currentUser?.username}
            </Typography>
          </Box>
        </Box>
        <Button 
          variant="outlined" 
          fullWidth
          component={Link}
          to={`/profile/${currentUser?.username}`}
        >
          查看个人资料
        </Button>
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          推荐关注
        </Typography>
        <Typography variant="body2" color="textSecondary">
          暂无推荐用户
        </Typography>
      </Paper>
    </Grid>
  </Grid>
</Container>
);
};

export default Home;