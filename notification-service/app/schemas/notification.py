from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.notification import NotificationType

# 通知创建Schema
class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    body: Optional[str] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None

# 通知更新Schema
class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

# 通知响应Schema
class Notification(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    title: str
    body: Optional[str] = None
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    sender_avatar: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 批量更新通知Schema
class NotificationBulkUpdate(BaseModel):
    notification_ids: List[int]
    is_read: bool

# 通知过滤器Schema
class NotificationFilter(BaseModel):
    type: Optional[NotificationType] = None
    is_read: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# 通知统计Schema
class NotificationCount(BaseModel):
    total: int
    unread: int

# 通知分页响应Schema
class NotificationPage(BaseModel):
    items: List[Notification]
    total: int
    page: int
    size: int
    pages: int
    unread_count: int