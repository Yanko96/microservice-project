import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
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
  List,
  ListItem,
  ListItemAvatar,
  ListItemText
} from '@mui/material';
import { 
  FavoriteBorder, 
  Favorite, 
  Comment as CommentIcon, 
  Share,
  Send
} from '@mui/icons-material';
import { fetchPostById, likePost, fetchPostComments, createComment } from '../api/posts';

const PostDetail = () => {
  const { postId } = useParams();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentContent, setCommentContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCommentsLoading, setIsCommentsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { currentUser } = useContext(AuthContext);
  
  useEffect(() => {
    loadPost();
  }, [postId]);
  
  const loadPost = async () => {
    setIsLoading(true);
    try {
      const postData = await fetchPostById(postId);
      setPost(postData);
      loadComments();
    } catch (error) {
      console.error('Error loading post:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadComments = async () => {
    setIsCommentsLoading(true);
    try {
      const commentsData = await fetchPostComments(postId);
      setComments(commentsData.items);
    } catch (error) {
      console.error('Error loading comments:', error);
    } finally {
      setIsCommentsLoading(false);
    }
  };
  
  const handleLike = async () => {
    try {
      await likePost(postId);
      
      // 更新点赞状态
      setPost(prevPost => {
        const isLiked = prevPost.current_user_reaction === 'like';
        return {
          ...prevPost,
          current_user_reaction: isLiked ? null : 'like',
          like_count: isLiked ? prevPost.like_count - 1 : prevPost.like_count + 1
        };
      });
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };
  
  const handleCommentChange = (e) => {
    setCommentContent(e.target.value);
  };
  
  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!commentContent.trim()) return;
    
    setIsSubmitting(true);
    try {
      const newComment = await createComment({
        content: commentContent,
        post_id: parseInt(postId)
      });
      
      setComments([newComment, ...comments]);
      setCommentContent('');
      
      // 更新帖子评论计数
      setPost(prevPost => ({
        ...prevPost,
        comment_count: prevPost.comment_count + 1
      }));
    } catch (error) {
      console.error('Error creating comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (!post) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="error">
            帖子不存在或已被删除
          </Typography>
          <Button 
            component={Link} 
            to="/" 
            variant="contained" 
            color="primary" 
            sx={{ mt: 2 }}
          >
            返回首页
          </Button>
        </Paper>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ mb: 3 }}>
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
            onClick={handleLike}
            color={post.current_user_reaction === 'like' ? 'primary' : 'default'}
          >
            {post.current_user_reaction === 'like' ? <Favorite /> : <FavoriteBorder />}
          </IconButton>
          <Typography variant="body2" color="textSecondary">
            {post.like_count}
          </Typography>
          
          <IconButton 
            aria-label="comment"
            sx={{ ml: 2 }}
          >
            <CommentIcon />
          </IconButton>
          <Typography variant="body2" color="textSecondary">
            {post.comment_count}
          </Typography>
          
          <IconButton aria-label="share" sx={{ ml: 2 }}>
            <Share />
          </IconButton>
        </CardActions>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          评论
        </Typography>
        <Box component="form" onSubmit={handleCommentSubmit}>
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
              rows={2}
              placeholder="写下你的评论..."
              variant="outlined"
              value={commentContent}
              onChange={handleCommentChange}
              disabled={isSubmitting}
            />
          </Box>
          <Box display="flex" justifyContent="flex-end">
            <Button
              variant="contained"
              color="primary"
              endIcon={<Send />}
              disabled={!commentContent.trim() || isSubmitting}
              type="submit"
            >
              {isSubmitting ? <CircularProgress size={24} /> : '发布评论'}
            </Button>
          </Box>
        </Box>
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          全部评论 ({post.comment_count})
        </Typography>
        
        {isCommentsLoading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : comments.length === 0 ? (
          <Typography variant="body2" color="textSecondary" align="center" sx={{ py: 2 }}>
            暂无评论，成为第一个评论的人吧！
          </Typography>
        ) : (
          <List>
            {comments.map((comment) => (
              <React.Fragment key={comment.id}>
                <ListItem alignItems="flex-start">
                  <ListItemAvatar>
                    <Avatar 
                      src={comment.user?.avatar_url} 
                      alt={comment.user?.username}
                    >
                      {comment.user?.username?.[0]?.toUpperCase()}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Link 
                          to={`/profile/${comment.user?.username}`} 
                          style={{ textDecoration: 'none', color: 'inherit' }}
                        >
                          <Typography variant="subtitle2" fontWeight="bold">
                            {comment.user?.full_name || comment.user?.username}
                          </Typography>
                        </Link>
                        <Typography variant="caption" color="textSecondary">
                          {new Date(comment.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <React.Fragment>
                        <Typography
                          component="span"
                          variant="body2"
                          color="textPrimary"
                          sx={{ display: 'block', mt: 1 }}
                        >
                          {comment.content}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                          <IconButton 
                            aria-label="like" 
                            size="small"
                            color={comment.current_user_reaction === 'like' ? 'primary' : 'default'}
                          >
                            {comment.current_user_reaction === 'like' ? 
                              <Favorite fontSize="small" /> : 
                              <FavoriteBorder fontSize="small" />
                            }
                          </IconButton>
                          <Typography variant="caption" color="textSecondary">
                            {comment.like_count}
                          </Typography>
                          <Button 
                            size="small" 
                            sx={{ ml: 2 }}
                            color="primary"
                          >
                            回复
                          </Button>
                        </Box>
                      </React.Fragment>
                    }
                  />
                </ListItem>
                <Divider variant="inset" component="li" />
              </React.Fragment>
            ))}
          </List>
        )}
        
        {comments.length > 0 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Button variant="outlined" color="primary">
              加载更多评论
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default PostDetail;