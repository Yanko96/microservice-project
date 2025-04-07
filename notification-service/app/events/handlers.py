import logging
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)

async def handle_notification(data: Dict[str, Any], db: Session) -> Optional[Notification]:
    """
    处理通知消息，保存到数据库
    
    参数:
        data: 通知数据
        db: 数据库会话
    
    返回:
        创建的通知对象，如果失败则返回None
    """
    try:
        if data.get("type") == "follow" and "user_id" not in data:
            # 将 followee_id 作为 user_id（接收者），follower_id 作为 sender
            data["user_id"] = data["followee_id"]
            data["sender_id"] = data["follower_id"]
            data["title"] = "你有一个新粉丝"
            data["body"] = f"用户 {data['follower_id']} 关注了你"
            # 可选添加 sender_name/sender_avatar：如果后续优化
            data["resource_type"] = "user"
            data["resource_id"] = data["follower_id"]

        # 创建通知
        notification_data = NotificationCreate(
            user_id=data["user_id"],
            type=data["type"],
            title=data["title"],
            body=data.get("body"),
            sender_id=data.get("sender_id"),
            sender_name=data.get("sender_name"),
            sender_avatar=data.get("sender_avatar"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            meta_data=data.get("data")  # 兼容旧格式
        )
        
        # 创建通知记录
        notification = Notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            title=notification_data.title,
            body=notification_data.body,
            sender_id=notification_data.sender_id,
            sender_name=notification_data.sender_name,
            sender_avatar=notification_data.sender_avatar,
            resource_type=notification_data.resource_type,
            resource_id=notification_data.resource_id,
            meta_data=notification_data.meta_data,
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"成功创建通知: ID={notification.id}, 用户={notification.user_id}, 类型={notification.type}")
        
        return notification
    except Exception as e:
        db.rollback()
        logger.error(f"创建通知失败: {str(e)}")
        return None

async def handle_post_event(event_type: str, post_data: Dict[str, Any], db: Session) -> None:
    """
    处理帖子事件，生成相关通知
    
    参数:
        event_type: 事件类型 (created, updated, deleted)
        post_data: 帖子数据
        db: 数据库会话
    """
    # 目前只处理创建事件，可以根据需要扩展
    if event_type != "created":
        return
    
    # 获取帖子作者ID
    user_id = post_data.get("user_id")
    if not user_id:
        logger.error(f"帖子数据缺少用户ID: {post_data}")
        return
    
    # 这里可以添加根据帖子内容生成通知的逻辑
    # 例如，检查帖子内容中是否有@用户，如果有则发送通知
    
    # 假设我们有一个提取提及用户的函数
    mentioned_users = extract_mentions(post_data.get("content", ""))
    
    # 为每个被提及的用户创建通知
    for mentioned_user_id in mentioned_users:
        if int(mentioned_user_id) == int(user_id):
            continue  # 跳过帖子作者自己
            
        notification = Notification(
            user_id=mentioned_user_id,
            type=NotificationType.MENTION,
            title="有人在帖子中提到了你",
            body=f"{post_data.get('user', {}).get('username', '有人')}在帖子中提到了你",
            sender_id=user_id,
            sender_name=post_data.get("user", {}).get("username"),
            sender_avatar=post_data.get("user", {}).get("avatar_url"),
            resource_type="post",
            resource_id=post_data.get("id"),
            is_read=False
        )
        
        db.add(notification)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"创建提及通知失败: {str(e)}")

async def handle_comment_event(event_type: str, comment_data: Dict[str, Any], db: Session) -> None:
    """
    处理评论事件，生成相关通知
    
    参数:
        event_type: 事件类型 (created, updated, deleted)
        comment_data: 评论数据
        db: 数据库会话
    """
    # 目前只处理创建事件，可以根据需要扩展
    if event_type != "created":
        return
    
    # 获取评论作者ID和帖子ID
    user_id = comment_data.get("user_id")
    post_id = comment_data.get("post_id")
    parent_id = comment_data.get("parent_id")
    
    if not user_id or not post_id:
        logger.error(f"评论数据缺少必要字段: {comment_data}")
        return
    
    try:
        # 获取帖子信息
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_BASE_URL}/posts/{post_id}")
            if response.status_code != 200:
                logger.error(f"获取帖子信息失败: {response.text}")
                return
                
            post_info = response.json()
            post_author_id = post_info.get("user_id")
            
            # 如果是回复其他评论
            if parent_id:
                # 获取父评论信息
                parent_response = await client.get(f"{settings.USER_SERVICE_BASE_URL}/comments/{parent_id}")
                if parent_response.status_code != 200:
                    logger.error(f"获取父评论信息失败: {parent_response.text}")
                else:
                    parent_comment = parent_response.json()
                    parent_author_id = parent_comment.get("user_id")
                    
                    # 如果回复的不是自己的评论，发送通知
                    if int(parent_author_id) != int(user_id):
                        reply_notification = Notification(
                            user_id=parent_author_id,
                            type=NotificationType.COMMENT_REPLY,
                            title="有人回复了你的评论",
                            body=truncate_text(comment_data.get("content", ""), 100),
                            sender_id=user_id,
                            sender_name=comment_data.get("user", {}).get("username"),
                            sender_avatar=comment_data.get("user", {}).get("avatar_url"),
                            resource_type="comment",
                            resource_id=comment_data.get("id"),
                            meta_data={
                                "post_id": post_id,
                                "parent_id": parent_id
                            },
                            is_read=False
                        )
                        
                        db.add(reply_notification)
            
            # 如果评论者不是帖子作者，发送通知给帖子作者
            if int(post_author_id) != int(user_id):
                post_notification = Notification(
                    user_id=post_author_id,
                    type=NotificationType.POST_COMMENT,
                    title="有人评论了你的帖子",
                    body=truncate_text(comment_data.get("content", ""), 100),
                    sender_id=user_id,
                    sender_name=comment_data.get("user", {}).get("username"),
                    sender_avatar=comment_data.get("user", {}).get("avatar_url"),
                    resource_type="post",
                    resource_id=post_id,
                    meta_data={
                        "comment_id": comment_data.get("id")
                    },
                    is_read=False
                )
                
                db.add(post_notification)
            
            # 处理评论中的提及
            mentioned_users = extract_mentions(comment_data.get("content", ""))
            for mentioned_user_id in mentioned_users:
                if (int(mentioned_user_id) == int(user_id) or 
                    int(mentioned_user_id) == int(post_author_id) or 
                    (parent_id and int(mentioned_user_id) == int(parent_author_id))):
                    continue  # 跳过已通知的用户
                    
                mention_notification = Notification(
                    user_id=mentioned_user_id,
                    type=NotificationType.MENTION,
                    title="有人在评论中提到了你",
                    body=truncate_text(comment_data.get("content", ""), 100),
                    sender_id=user_id,
                    sender_name=comment_data.get("user", {}).get("username"),
                    sender_avatar=comment_data.get("user", {}).get("avatar_url"),
                    resource_type="comment",
                    resource_id=comment_data.get("id"),
                    meta_data={
                        "post_id": post_id
                    },
                    is_read=False
                )
                
                db.add(mention_notification)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"处理评论事件失败: {str(e)}")

async def handle_reaction_event(event_type: str, reaction_data: Dict[str, Any], db: Session) -> None:
    """
    处理反应事件，生成相关通知
    
    参数:
        event_type: 事件类型 (created, updated, deleted)
        reaction_data: 反应数据
        db: 数据库会话
    """
    # 只处理创建事件
    if event_type != "created":
        return
    
    user_id = reaction_data.get("user_id")
    post_id = reaction_data.get("post_id")
    comment_id = reaction_data.get("comment_id")
    reaction_type = reaction_data.get("type", "like")
    
    if not user_id or (not post_id and not comment_id):
        logger.error(f"反应数据缺少必要字段: {reaction_data}")
        return
    
    try:
        if post_id:
            # 获取帖子信息
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.USER_SERVICE_BASE_URL}/posts/{post_id}")
                if response.status_code != 200:
                    logger.error(f"获取帖子信息失败: {response.text}")
                    return
                    
                post_info = response.json()
                post_author_id = post_info.get("user_id")
                
                # 如果点赞者不是帖子作者，发送通知
                if int(post_author_id) != int(user_id):
                    like_notification = Notification(
                        user_id=post_author_id,
                        type=NotificationType.POST_LIKE,
                        title="有人喜欢你的帖子",
                        body=f"{reaction_data.get('user', {}).get('username', '有人')}对你的帖子表示了{get_reaction_text(reaction_type)}",
                        sender_id=user_id,
                        sender_name=reaction_data.get("user", {}).get("username"),
                        sender_avatar=reaction_data.get("user", {}).get("avatar_url"),
                        resource_type="post",
                        resource_id=post_id,
                        is_read=False
                    )
                    
                    db.add(like_notification)
        
        elif comment_id:
            # 获取评论信息
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.USER_SERVICE_BASE_URL}/comments/{comment_id}")
                if response.status_code != 200:
                    logger.error(f"获取评论信息失败: {response.text}")
                    return
                    
                comment_info = response.json()
                comment_author_id = comment_info.get("user_id")
                
                # 如果点赞者不是评论作者，发送通知
                if int(comment_author_id) != int(user_id):
                    like_notification = Notification(
                        user_id=comment_author_id,
                        type=NotificationType.COMMENT_LIKE,
                        title="有人喜欢你的评论",
                        body=f"{reaction_data.get('user', {}).get('username', '有人')}对你的评论表示了{get_reaction_text(reaction_type)}",
                        sender_id=user_id,
                        sender_name=reaction_data.get("user", {}).get("username"),
                        sender_avatar=reaction_data.get("user", {}).get("avatar_url"),
                        resource_type="comment",
                        resource_id=comment_id,
                        meta_data={
                            "post_id": comment_info.get("post_id")
                        },
                        is_read=False
                    )
                    
                    db.add(like_notification)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"处理反应事件失败: {str(e)}")

# 辅助函数

def extract_mentions(text: str) -> list:
    """
    从文本中提取被提及的用户ID
    简单实现，实际应用中可能需要更复杂的解析
    
    格式: @userId:userName
    """
    import re
    
    # 匹配格式 @123:username
    mentions = re.findall(r'@(\d+):[a-zA-Z0-9_]+', text)
    return mentions

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    截断文本，确保不超过最大长度
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    return text[:max_length] + "..."

def get_reaction_text(reaction_type: str) -> str:
    """
    获取反应类型的中文描述
    """
    reaction_texts = {
        "like": "赞",
        "love": "喜爱",
        "haha": "大笑",
        "wow": "惊讶",
        "sad": "难过",
        "angry": "生气"
    }
    
    return reaction_texts.get(reaction_type, "喜欢")