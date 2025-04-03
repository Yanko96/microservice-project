from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx

from app.api.deps import get_current_user, get_user_service_client
from app.db.session import get_db
from app.models.post import Post
from app.models.comment import Comment
from app.models.reaction import Reaction, ReactionType
from app.schemas.reaction import (
    ReactionCreate, ReactionUpdate, Reaction as ReactionSchema,
    ReactionSummary, ReactionCount
)
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=ReactionSchema)
async def create_or_update_reaction(
    *,
    db: Session = Depends(get_db),
    reaction_in: ReactionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    创建或更新反应（点赞、喜欢等）
    """
    # 验证目标存在（帖子或评论）
    if reaction_in.post_id:
        target = db.query(Post).filter(Post.id == reaction_in.post_id).first()
        if not target:
            raise HTTPException(
                status_code=404,
                detail="帖子不存在"
            )
        target_type = "post"
    elif reaction_in.comment_id:
        target = db.query(Comment).filter(Comment.id == reaction_in.comment_id).first()
        if not target:
            raise HTTPException(
                status_code=404,
                detail="评论不存在"
            )
        target_type = "comment"
    else:
        raise HTTPException(
            status_code=400,
            detail="必须指定帖子ID或评论ID"
        )
    
    # 检查是否已存在反应
    if target_type == "post":
        existing_reaction = db.query(Reaction).filter(
            Reaction.post_id == reaction_in.post_id,
            Reaction.user_id == current_user["id"]
        ).first()
    else:
        existing_reaction = db.query(Reaction).filter(
            Reaction.comment_id == reaction_in.comment_id,
            Reaction.user_id == current_user["id"]
        ).first()
    
    # 如果已存在且类型相同，则删除（取消反应）
    if existing_reaction and existing_reaction.type == reaction_in.type:
        db.delete(existing_reaction)
        
        # 更新目标的点赞数
        if target_type == "post":
            target.like_count = max(0, target.like_count - 1)
        else:
            target.like_count = max(0, target.like_count - 1)
            
        db.add(target)
        db.commit()
        
        # 返回删除后的空反应
        return None
    
    # 如果已存在但类型不同，则更新类型
    if existing_reaction:
        existing_reaction.type = reaction_in.type
        db.add(existing_reaction)
        db.commit()
        db.refresh(existing_reaction)
        return existing_reaction
    
    # 否则创建新反应
    reaction = Reaction(
        user_id=current_user["id"],
        type=reaction_in.type,
        post_id=reaction_in.post_id,
        comment_id=reaction_in.comment_id
    )
    
    db.add(reaction)
    
    # 更新目标的点赞数
    if target_type == "post":
        target.like_count += 1
    else:
        target.like_count += 1
        
    db.add(target)
    db.commit()
    db.refresh(reaction)
    
    return reaction

@router.get("/post/{post_id}/summary", response_model=ReactionSummary)
async def get_post_reaction_summary(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    获取帖子的反应（点赞等）统计
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 获取反应统计
    reactions_count = db.query(
        Reaction.type, 
        func.count(Reaction.id).label("count")
    ).filter(
        Reaction.post_id == post_id
    ).group_by(Reaction.type).all()
    
    # 获取当前用户的反应
    user_reaction = db.query(Reaction).filter(
        Reaction.post_id == post_id,
        Reaction.user_id == current_user["id"]
    ).first()
    
    # 构建返回结果
    counts = [
        {"type": reaction_type, "count": count}
        for reaction_type, count in reactions_count
    ]
    
    total = sum(item["count"] for item in counts)
    
    return {
        "total": total,
        "counts": counts,
        "has_reacted": user_reaction is not None,
        "current_user_reaction": user_reaction.type if user_reaction else None
    }

@router.get("/comment/{comment_id}/summary", response_model=ReactionSummary)
async def get_comment_reaction_summary(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    获取评论的反应（点赞等）统计
    """
    # 验证评论是否存在
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="评论不存在"
        )
    
    # 获取反应统计
    reactions_count = db.query(
        Reaction.type, 
        func.count(Reaction.id).label("count")
    ).filter(
        Reaction.comment_id == comment_id
    ).group_by(Reaction.type).all()
    
    # 获取当前用户的反应
    user_reaction = db.query(Reaction).filter(
        Reaction.comment_id == comment_id,
        Reaction.user_id == current_user["id"]
    ).first()
    
    # 构建返回结果
    counts = [
        {"type": reaction_type, "count": count}
        for reaction_type, count in reactions_count
    ]
    
    total = sum(item["count"] for item in counts)
    
    return {
        "total": total,
        "counts": counts,
        "has_reacted": user_reaction is not None,
        "current_user_reaction": user_reaction.type if user_reaction else None
    }

@router.get("/post/{post_id}/users", response_model=List[Dict[str, Any]])
async def get_post_reaction_users(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    reaction_type: Optional[ReactionType] = Query(None, description="筛选特定类型的反应"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    获取对帖子做出反应的用户列表
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 构建查询
    query = db.query(Reaction).filter(Reaction.post_id == post_id)
    
    # 如果指定了反应类型，应用筛选
    if reaction_type:
        query = query.filter(Reaction.type == reaction_type)
    
    # 按时间排序并应用分页
    reactions = query.order_by(Reaction.created_at.desc()).offset(skip).limit(limit).all()
    
    # 获取用户ID列表
    user_ids = [reaction.user_id for reaction in reactions]
    
    # 如果没有反应，返回空列表
    if not user_ids:
        return []
    
    # 批量获取用户信息
    try:
        response = await user_client.get("/users/batch", params={"ids": ",".join(map(str, user_ids))})
        if response.status_code != 200:
            # 如果批量获取失败，尝试单个获取
            users = []
            for user_id in user_ids:
                try:
                    user_response = await user_client.get(f"/users/id/{user_id}")
                    if user_response.status_code == 200:
                        users.append(user_response.json())
                except httpx.RequestError:
                    continue
        else:
            users = response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="无法连接到用户服务"
        )
    
    # 构建用户和反应类型的映射
    user_reactions = {}
    for reaction in reactions:
        user_reactions[reaction.user_id] = reaction.type
    
    # 添加反应类型到用户信息
    for user in users:
        user["reaction_type"] = user_reactions.get(user["id"])
    
    return users

@router.delete("/{reaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(
    *,
    db: Session = Depends(get_db),
    reaction_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """
    删除反应（取消点赞等）
    """
    # 获取反应
    reaction = db.query(Reaction).filter(Reaction.id == reaction_id).first()
    if not reaction:
        raise HTTPException(
            status_code=404,
            detail="反应不存在"
        )
    
    # 检查权限（只能删除自己的反应）
    if reaction.user_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="无权删除该反应"
        )
    
    # 更新目标的点赞数
    if reaction.post_id:
        post = db.query(Post).filter(Post.id == reaction.post_id).first()
        if post:
            post.like_count = max(0, post.like_count - 1)
            db.add(post)
    elif reaction.comment_id:
        comment = db.query(Comment).filter(Comment.id == reaction.comment_id).first()
        if comment:
            comment.like_count = max(0, comment.like_count - 1)
            db.add(comment)
    
    # 删除反应
    db.delete(reaction)
    db.commit()
    