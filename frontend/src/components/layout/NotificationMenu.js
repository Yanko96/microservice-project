import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Menu, 
  MenuItem, 
  Typography, 
  Box, 
  IconButton,
  Avatar,
  Button,
  Divider,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress
} from '@mui/material';
import { 
  CheckCircle as ReadIcon, 
  MoreVert as MoreIcon 
} from '@mui/icons-material';
import { NotificationContext } from '../../context/NotificationContext';

const NotificationMenu = ({ anchorEl, open, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, isConnected } = useContext(NotificationContext);
  const navigate = useNavigate();
  
  // 处理通知点击
  const handleNotificationClick = (notification) => {
    // 标记为已读
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    
    // 根据通知类型导航
    if (notification.resource_type === 'post' && notification.resource_id) {
      navigate(`/posts/${notification.resource_id}`);
    } else if (notification.resource_type === 'comment' && notification.resource_id) {
      navigate(`/posts/${notification.meta_data?.post_id || ''}`);
    } else if (notification.type === 'FOLLOW' && notification.sender_id) {
      navigate(`/profile/${notification.sender_name}`);
    }
    
    onClose();
  };
  
  // 格式化通知时间
  const formatNotificationTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) {
      return '刚刚';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}分钟前`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}小时前`;
    } else {
      return `${Math.floor(diffInMinutes / 1440)}天前`;
    }
  };
  
  // 获取通知图标
  const getNotificationIcon = (notification) => {
    // 这里可以根据通知类型返回不同的图标
    return (
      <Avatar 
        src={notification.sender_avatar} 
        alt={notification.sender_name}
      >
        {notification.sender_name?.[0]?.toUpperCase()}
      </Avatar>
    );
  };
  
  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { 
          width: 360,
          maxHeight: 450
        }
      }}
      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
    >
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">通知</Typography>
        <Box display="flex" alignItems="center">
          {isConnected ? (
            <Box 
              component="span" 
              sx={{ 
                width: 8, 
                height: 8, 
                bgcolor: 'success.main', 
                borderRadius: '50%', 
                display: 'inline-block',
                mr: 1
              }} 
            />
          ) : (
            <CircularProgress size={12} sx={{ mr: 1 }} />
          )}
          <Typography variant="caption" color={isConnected ? 'success.main' : 'text.secondary'}>
            {isConnected ? '已连接' : '连接中...'}
          </Typography>
        </Box>
      </Box>
      
      <Divider />
      
      {unreadCount > 0 && (
        <Box sx={{ p: 1 }}>
          <Button 
            variant="text" 
            size="small" 
            onClick={markAllAsRead}
            fullWidth
          >
            全部标为已读
          </Button>
        </Box>
      )}
      
      {notifications.length === 0 ? (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="textSecondary">
            暂无通知
          </Typography>
        </Box>
      ) : (
        notifications.map((notification) => (
          <MenuItem 
            key={notification.id} 
            onClick={() => handleNotificationClick(notification)}
            sx={{ 
              py: 1,
              backgroundColor: notification.is_read ? 'transparent' : 'action.hover'
            }}
          >
            <ListItemAvatar>
              {getNotificationIcon(notification)}
            </ListItemAvatar>
            <ListItemText 
              primary={notification.title}
              secondary={
                <React.Fragment>
                  <Typography
                    component="span"
                    variant="body2"
                    color="textPrimary"
                    sx={{ display: 'inline' }}
                  >
                    {notification.body}
                  </Typography>
                  <br />
                  <Typography component="span" variant="caption" color="textSecondary">
                    {formatNotificationTime(notification.created_at)}
                  </Typography>
                </React.Fragment>
              }
            />
            <ListItemSecondaryAction>
              {!notification.is_read && (
                <IconButton 
                  edge="end" 
                  aria-label="mark as read"
                  onClick={(e) => {
                    e.stopPropagation();
                    markAsRead(notification.id);
                  }}
                  size="small"
                >
                  <ReadIcon fontSize="small" />
                </IconButton>
              )}
            </ListItemSecondaryAction>
          </MenuItem>
        ))
      )}
      
      <Divider />
      
      <Box sx={{ p: 1 }}>
        <Button 
          variant="text" 
          size="small" 
          onClick={() => {
            navigate('/notifications');
            onClose();
          }}
          fullWidth
        >
          查看所有通知
        </Button>
      </Box>
    </Menu>
  );
};

export default NotificationMenu;