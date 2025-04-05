import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.session import get_db
from app.models.notification import Notification, NotificationType
from app.schemas.notification import (
    Notification as NotificationSchema,
    NotificationCreate,
    NotificationUpdate,
    NotificationBulkUpdate,
    NotificationFilter,
    NotificationCount,
    NotificationPage
)
from app.api.deps import get_current_user, get_pagination_params
from app.core.config import settings
from app.websockets.connection import connection_manager, authenticate_websocket
from app.websockets.broadcaster import broadcast_to_user

router = APIRouter()

@router.get("/", response_model=NotificationPage)
async def get_notifications(
    db: Session = Depends(get_db),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    type: Optional[NotificationType] = None,
    is_read: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    获取当前用户的通知列表
    """
    # 分页参数
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size
    
    # 查询条件
    query = db.query(Notification).filter(Notification.user_id == current_user["id"])
    
    # 应用筛选
    if type:
        query = query.filter(Notification.type == type)
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    # 获取总数
    total = query.count()
    
    # 获取未读通知数量
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user["id"],
        Notification.is_read == False
    ).count()
    
    # 应用排序和分页
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(size).all()
    
    # 计算总页数
    pages = (total + size - 1) // size if total > 0 else 1
    
    return {
        "items": notifications,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "unread_count": unread_count
    }

@router.get("/unread/count", response_model=NotificationCount)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    获取未读通知数量
    """
    # 获取总通知数量
    total = db.query(Notification).filter(
        Notification.user_id == current_user["id"]
    ).count()
    
    # 获取未读通知数量
    unread = db.query(Notification).filter(
        Notification.user_id == current_user["id"],
        Notification.is_read == False
    ).count()
    
    return {
        "total": total,
        "unread": unread
    }

@router.get("/{notification_id}", response_model=NotificationSchema)
async def get_notification(
    notification_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    获取特定通知的详情
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="通知不存在"
        )
    
    return notification

@router.put("/{notification_id}", response_model=NotificationSchema)
async def update_notification(
    *,
    notification_id: int = Path(..., gt=0),
    notification_in: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    更新通知状态
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="通知不存在"
        )
    
    # 更新是否已读状态
    if notification_in.is_read is not None:
        notification.is_read = notification_in.is_read
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification

@router.put("/mark-all-read", response_model=Dict[str, Any])
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    将所有通知标记为已读
    """
    # 更新所有未读通知
    result = db.query(Notification).filter(
        Notification.user_id == current_user["id"],
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {
        "message": "所有通知已标记为已读",
        "updated_count": result
    }

@router.put("/batch", response_model=Dict[str, Any])
async def batch_update_notifications(
    *,
    update_data: NotificationBulkUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    批量更新通知状态
    """
    # 验证通知ID列表
    if not update_data.notification_ids:
        raise HTTPException(
            status_code=400,
            detail="通知ID列表不能为空"
        )
    
    # 更新通知
    result = db.query(Notification).filter(
        Notification.id.in_(update_data.notification_ids),
        Notification.user_id == current_user["id"]
    ).update({"is_read": update_data.is_read})
    
    db.commit()
    
    return {
        "message": f"已更新{result}条通知",
        "updated_count": result
    }

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    *,
    notification_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    删除特定通知
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="通知不存在"
        )
    
    db.delete(notification)
    db.commit()

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_notifications(
    *,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    删除所有通知
    """
    db.query(Notification).filter(
        Notification.user_id == current_user["id"]
    ).delete()
    
    db.commit()

@router.post("/test", response_model=NotificationSchema)
async def create_test_notification(
    *,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    创建测试通知
    """
    # 创建通知
    notification = Notification(
        user_id=current_user["id"],
        type=NotificationType.SYSTEM,
        title="测试通知",
        body="这是一条测试通知",
        sender_id=None,
        sender_name="系统",
        sender_avatar=None,
        resource_type=None,
        resource_id=None,
        is_read=False
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # 通过WebSocket发送通知
    await broadcast_to_user(
        user_id=current_user["id"],
        message={
            "type": "notification",
            "data": {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "body": notification.body,
                "created_at": notification.created_at.isoformat()
            }
        }
    )
    
    return notification

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    通知WebSocket端点
    允许客户端建立WebSocket连接以接收实时通知
    """
    # 认证用户
    try:
        user_id = await authenticate_websocket(websocket)
    except ValueError as e:
        # 认证失败，连接已关闭
        return
    
    # 接受WebSocket连接
    await websocket.accept()
    
    # 将连接添加到管理器
    await connection_manager.connect(websocket, user_id)
    
    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": "已连接到通知服务",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 监听来自客户端的消息
        while True:
            # 等待客户端消息
            message = await websocket.receive_text()
            
            try:
                # 解析消息
                data = json.loads(message)
                
                # 处理消息（例如标记通知为已读）
                if data.get("type") == "mark_read" and "notification_id" in data:
                    # 创建数据库会话
                    db = next(get_db())
                    try:
                        # 更新通知状态
                        notification = db.query(Notification).filter(
                            Notification.id == data["notification_id"],
                            Notification.user_id == user_id
                        ).first()
                        
                        if notification:
                            notification.is_read = True
                            db.add(notification)
                            db.commit()
                            
                            # 发送确认消息
                            await websocket.send_json({
                                "type": "notification_updated",
                                "notification_id": notification.id,
                                "is_read": True,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    finally:
                        db.close()
            except json.JSONDecodeError:
                # 忽略无效的JSON
                pass
            except Exception as e:
                # 发送错误消息
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        # 客户端断开连接
        await connection_manager.disconnect(websocket, user_id)
    except Exception as e:
        # 其他异常
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass
        finally:
            await connection_manager.disconnect(websocket, user_id)