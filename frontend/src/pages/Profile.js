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
  Avatar,
  Grid,
  CircularProgress,
  Card,
  CardContent,
  Tabs,
  Tab
} from '@mui/material';
import {
  LocationOn,
  Link as LinkIcon,
  CalendarToday,
  Edit
} from '@mui/icons-material';
import { fetchUserProfile, fetchUserPosts, followUser } from '../api/users';

// 需要创建这个 API 函数
const getUserProfile = async (username) => {
  // 临时实现，使用模拟数据
  return {
    id: 1,
    username: username,
    full_name: "测试用户",
    bio: "这是一个测试用户资料",
    location: "北京",
    website: "https://example.com",
    avatar_url: null,
    is_private: false,
    created_at: new Date().toISOString(),
    follower_count: 100,
    following_count: 50,
    post_count: 25,
    is_following: false
  };
};

// 资料页标签组件
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Profile = () => {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [isFollowing, setIsFollowing] = useState(false);
  
  const { currentUser } = useContext(AuthContext);
  
  const isOwnProfile = currentUser?.username === username;
  
  useEffect(() => {
    loadProfile();
  }, [username]);
  
  const loadProfile = async () => {
    setIsLoading(true);
    try {
      // 应该通过 API 获取用户资料
      const profileData = await getUserProfile(username);
      setProfile(profileData);
      setIsFollowing(profileData.is_following);
      
      // 加载用户的帖子
      loadUserPosts();
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const loadUserPosts = async () => {
    try {
      // 临时实现，使用模拟数据
      setPosts([]);
    } catch (error) {
      console.error('Error loading user posts:', error);
    }
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handleFollow = async () => {
    try {
      // 应该通过 API 关注或取消关注用户
      setIsFollowing(!isFollowing);
      
      // 更新关注者计数
      setProfile(prev => ({
        ...prev,
        follower_count: isFollowing ? prev.follower_count - 1 : prev.follower_count + 1
      }));
    } catch (error) {
      console.error('Error following user:', error);
    }
  };
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (!profile) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="error">
            用户不存在
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
      {/* 用户基本信息 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4} sx={{ display: 'flex', justifyContent: 'center' }}>
            <Avatar 
              src={profile.avatar_url} 
              alt={profile.username}
              sx={{ width: 150, height: 150 }}
            >
              {profile.username[0].toUpperCase()}
            </Avatar>
          </Grid>
          <Grid item xs={12} sm={8}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Typography variant="h5" fontWeight="bold">
                {profile.full_name || profile.username}
              </Typography>
              {isOwnProfile ? (
                <Button 
                  variant="outlined" 
                  startIcon={<Edit />}
                  component={Link}
                  to="/settings"
                >
                  编辑资料
                </Button>
              ) : (
                <Button 
                  variant={isFollowing ? "outlined" : "contained"} 
                  color="primary"
                  onClick={handleFollow}
                >
                  {isFollowing ? '已关注' : '关注'}
                </Button>
              )}
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              @{profile.username}
            </Typography>
            
            <Typography variant="body1" sx={{ mb: 2 }}>
              {profile.bio || '这个人很懒，什么都没留下。'}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <LocationOn fontSize="small" color="action" sx={{ mr: 1 }} />
              <Typography variant="body2" color="textSecondary">
                {profile.location || '未知位置'}
              </Typography>
            </Box>
            
            {profile.website && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <LinkIcon fontSize="small" color="action" sx={{ mr: 1 }} />
                <Typography variant="body2" color="primary" component="a" href={profile.website} target="_blank">
                  {profile.website.replace(/^https?:\/\//, '')}
                </Typography>
              </Box>
            )}
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CalendarToday fontSize="small" color="action" sx={{ mr: 1 }} />
              <Typography variant="body2" color="textSecondary">
                {`加入于 ${new Date(profile.created_at).toLocaleDateString()}`}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="h6" fontWeight="bold">
                  {profile.post_count}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  帖子
                </Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="h6" fontWeight="bold">
                  {profile.follower_count}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  粉丝
                </Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="h6" fontWeight="bold">
                  {profile.following_count}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  关注
                </Typography>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>
      
      {/* 标签页 */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="帖子" />
          <Tab label="媒体" />
          <Tab label="喜欢" />
        </Tabs>
        
        {/* 帖子标签内容 */}
        <TabPanel value={tabValue} index={0}>
          {posts.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">
                暂无帖子
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {posts.map(post => (
                <Grid item xs={12} key={post.id}>
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="body1">
                        {post.content}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>
        
        {/* 媒体标签内容 */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="textSecondary">
              暂无媒体内容
            </Typography>
          </Box>
        </TabPanel>
        
        {/* 喜欢标签内容 */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="textSecondary">
              暂无喜欢的内容
            </Typography>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default Profile;