import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext';

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const { currentUser } = useContext(AuthContext);
  
  // 初始化WebSocket连接
  useEffect(() => {
    if (currentUser && !socket) {
      connectWebSocket();
    }
    
    // 清理函数
    return () => {
      if (socket) {
        socket.close();
        setSocket(null);
        setIsConnected(false);
      }
    };
  }, [currentUser]);
  
  // 连接WebSocket
  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const wsUrl = `${process.env.REACT_APP_WS_URL}?token=${token}`;
    const newSocket = new WebSocket(wsUrl);
    
    newSocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setSocket(newSocket);
      
      // 连接成功后立即加载通知
      fetchNotifications();
    };
    
    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'notification') {
          // 新通知
          handleNewNotification(data.data);
        } else if (data.type === 'notification_updated') {
          // 通知状态更新
          handleNotificationUpdate(data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    newSocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setSocket(null);
      
      // 重新连接逻辑
      setTimeout(() => {
        if (currentUser) {
          connectWebSocket();
        }
      }, 3000);
    };
    
    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      newSocket.close();
    };
  };
  
  // 处理新通知
  const handleNewNotification = (notification) => {
    setNotifications(prevNotifications => [notification, ...prevNotifications]);
    setUnreadCount(prevCount => prevCount + 1);
  };
  
  // 处理通知状态更新
  const handleNotificationUpdate = (data) => {
    const { notification_id, is_read } = data;
    
    setNotifications(prevNotifications => 
      prevNotifications.map(notification => 
        notification.id === notification_id 
          ? { ...notification, is_read } 
          : notification
      )
    );
    
    if (is_read) {
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
    }
  };
  
  // 获取通知列表
  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/notifications/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }
      
      const data = await response.json();
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };
  
  // 标记通知为已读
  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      // 如果WebSocket连接存在，通过WebSocket发送标记已读消息
      if (socket && isConnected) {
        socket.send(JSON.stringify({
          type: 'mark_read',
          notification_id: notificationId
        }));
        return;
      }
      
      // 否则通过REST API标记已读
      const response = await fetch(`${process.env.REACT_APP_API_URL}/notifications/${notificationId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_read: true })
      });
      
      if (!response.ok) {
        throw new Error('Failed to mark notification as read');
      }
      
      // 更新本地通知状态
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => 
          notification.id === notificationId 
            ? { ...notification, is_read: true } 
            : notification
        )
      );
      
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };
  
  // 标记所有通知为已读
  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${process.env.REACT_APP_API_URL}/notifications/mark-all-read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to mark all notifications as read');
      }
      
      // 更新本地通知状态
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => ({ ...notification, is_read: true }))
      );
      
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };
  
  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      isConnected,
      markAsRead,
      markAllAsRead,
      fetchNotifications
    }}>
      {children}
    </NotificationContext.Provider>
  );
};