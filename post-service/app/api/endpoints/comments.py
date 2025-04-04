from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_current_user, check_ownership, get_pagination_params, get_user_service_client
from app.db.session import get_db
from app.models.post import Post
from app.models.comment import Comment
from app.models.reaction import Reaction
from app.schemas.comment import (
    CommentCreate, CommentUpdate, Comment as CommentSchema, 
    CommentDetail, CommentPage, CommentFilter
)
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=CommentSchema)
async def create_comment(
    *,
    db: Session = Depends(get_db),
    comment_in: CommentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    创建评论
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.id == comment_in.post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 如果是回复，验证父评论是否存在
    if comment_in.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_in.parent_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=404,
                detail="父评论不存在"
            )
        # 确保父评论属于同一帖子
        if parent_comment.post_id != comment_in.post_id:
            raise HTTPException(
                status_code=400,
                detail="父评论不属于指定帖子"
            )
        # 更新父评论的回复计数
        parent_comment.reply_count += 1
        db.add(parent_comment)
    
    # 创建评论
    comment = Comment(
        content=comment_in.content,
        user_id=current_user["id"],
        post_id=comment_in.post_id,
        parent_id=comment_in.parent_id
    )
    
    db.add(comment)
    
    # 更新帖子评论计数
    post.comment_count += 1
    db.add(post)
    
    db.commit()
    db.refresh(comment)
    
    # 返回评论，包含用户信息
    result = CommentSchema.from_orm(comment)
    result.user = {
        "id": current_user["id"],
        "username": current_user["username"],
        "full_name": current_user.get("full_name"),
        "avatar_url": current_user.get("avatar_url")
    }
    
    return result

@router.get("/post/{post_id}", response_model=CommentPage)
async def read_post_comments(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    parent_id: Optional[int] = Query(None, description="获取特定评论的回复，如果不提供则获取顶级评论"),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    获取帖子的评论列表
    """
    # 验证帖子是否存在
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 计算分页参数
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size
    
    # 构建查询
    query = db.query(Comment).filter(Comment.post_id == post_id, Comment.is_deleted == False)
    
    # 如果指定了父评论ID，获取其回复
    if parent_id is not None:
        query = query.filter(Comment.parent_id == parent_id)
    else:
        # 否则获取顶级评论（无父评论）
        query = query.filter(Comment.parent_id == None)
    
    # 按创建时间排序
    query = query.order_by(Comment.created_at.desc())
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    comments = query.offset(skip).limit(size).all()
    
    # 获取需要查询的用户ID列表
    user_ids = list(set(comment.user_id for comment in comments))
    
    # 批量获取用户信息
    users = {}
    if user_ids:
        try:
            response = await user_client.get("/users/batch", params={"ids": ",".join(map(str, user_ids))})
            if response.status_code == 200:
                user_list = response.json()
                users = {user["id"]: user for user in user_list}
        except httpx.RequestError:
            # 如果用户服务不可用，继续处理但不包含用户信息
            pass
    
    # 构建返回结果
    items = []
    for comment in comments:
        comment_dict = CommentSchema.from_orm(comment)
        
        # 添加用户信息
        if comment.user_id in users:
            comment_dict.user = users[comment.user_id]
            
        # 检查当前用户的反应
        reaction = db.query(Reaction).filter(
            Reaction.comment_id == comment.id,
            Reaction.user_id == current_user["id"]
        ).first()
        
        if reaction:
            comment_dict.current_user_reaction = reaction.type.value
            
        items.append(comment_dict)
    
    # 计算总页数
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{comment_id}", response_model=CommentDetail)
async def read_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., gt=0),
    with_replies: bool = Query(False, description="是否包含回复"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    获取评论详情
    """
    # 获取评论
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.is_deleted == False).first()
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="评论不存在"
        )
    
    # 获取用户信息
    user_info = None
    try:
        response = await user_client.get(f"/users/id/{comment.user_id}")
        if response.status_code == 200:
            user_info = response.json()
    except httpx.RequestError:
        pass
    
    # 获取当前用户的反应
    reaction = db.query(Reaction).filter(
        Reaction.comment_id == comment.id,
        Reaction.user_id == current_user["id"]
    ).first()
    
    comment_detail = CommentDetail.from_orm(comment)
    
    # 添加用户信息
    if user_info:
        comment_detail.user = user_info
        
    # 添加当前用户的反应
    if reaction:
        comment_detail.current_user_reaction = reaction.type.value
    
    # 如果请求包含回复，获取评论的回复
    if with_replies and comment.reply_count > 0:
        replies_query = db.query(Comment).filter(
            Comment.parent_id == comment.id,
            Comment.is_deleted == False
        ).order_by(Comment.created_at.asc())
        
        replies = replies_query.all()
        
        # 获取回复作者的信息
        reply_user_ids = list(set(reply.user_id for reply in replies))
        reply_users = {}
        
        if reply_user_ids:
            try:
                response = await user_client.get("/users/batch", params={"ids": ",".join(map(str, reply_user_ids))})
                if response.status_code == 200:
                    user_list = response.json()
                    reply_users = {user["id"]: user for user in user_list}
            except httpx.RequestError:
                pass
        
        # 构建回复列表
        reply_items = []
        for reply in replies:
            reply_dict = CommentDetail.from_orm(reply)
            
            # 添加用户信息
            if reply.user_id in reply_users:
                reply_dict.user = reply_users[reply.user_id]
                
            # 检查当前用户的反应
            reply_reaction = db.query(Reaction).filter(
                Reaction.comment_id == reply.id,
                Reaction.user_id == current_user["id"]
            ).first()
            
            if reply_reaction:
                reply_dict.current_user_reaction = reply_reaction.type.value
                
            reply_items.append(reply_dict)
        
        comment_detail.replies = reply_items
    
    return comment_detail

@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., gt=0),
    comment_in: CommentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    更新评论内容
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="评论不存在"
        )
    
    # 检查权限
    if not await check_ownership(comment.user_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权修改该评论"
        )
    
    # 如果评论已被删除，不允许修改
    if comment.is_deleted:
        raise HTTPException(
            status_code=400,
            detail="评论已被删除，无法修改"
        )
    
    # 更新评论内容
    update_data = comment_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    
    # 标记为已编辑
    comment.is_edited = True
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment

@router.delete("/{comment_id}")
async def delete_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    删除评论（软删除）
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404,
            detail="评论不存在"
        )
    
    # 检查权限（作者或管理员可以删除）
    if not await check_ownership(comment.user_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权删除该评论"
        )
    
    # 如果已经删除，直接返回成功
    if comment.is_deleted:
        return None
    
    # 软删除评论（保留记录但标记为已删除）
    comment.is_deleted = True
    comment.content = "[已删除]"
    
    # 更新帖子评论计数
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if post:
        post.comment_count -= 1
        db.add(post)
    
    # 如果有父评论，更新父评论的回复计数
    if comment.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if parent:
            parent.reply_count -= 1
            db.add(parent)
    
    db.add(comment)
    db.commit()
    
    return {"message": "评论已删除"}

@router.get("/user/{user_id}", response_model=CommentPage)
async def read_user_comments(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    获取用户的评论列表
    """
    # 验证用户是否存在
    try:
        response = await user_client.get(f"/users/id/{user_id}")
        if response.status_code != 200:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        user_info = response.json()
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="无法连接到用户服务"
        )
    
    # 计算分页参数
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size
    
    # 构建查询
    query = db.query(Comment).filter(
        Comment.user_id == user_id,
        Comment.is_deleted == False
    )
    
    # 如果不是本人或管理员，只能看到公开帖子的评论
    if user_id != current_user["id"] and not current_user.get("is_superuser"):
        # 子查询获取公开帖子的ID
        from sqlalchemy import select
        from app.models.post import Post, Visibility
        
        public_post_ids = select(Post.id).where(
            (Post.visibility == Visibility.PUBLIC)
        ).scalar_subquery()
        
        query = query.filter(Comment.post_id.in_(public_post_ids))
    
    # 按创建时间倒序排序
    query = query.order_by(Comment.created_at.desc())
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    comments = query.offset(skip).limit(size).all()
    
    # 获取帖子信息
    post_ids = list(set(comment.post_id for comment in comments))
    posts = {}
    if post_ids:
        post_query = db.query(Post).filter(Post.id.in_(post_ids))
        posts = {post.id: post for post in post_query.all()}
    
    # 构建返回结果
    items = []
    for comment in comments:
        comment_dict = CommentSchema.from_orm(comment)
        
        # 添加用户信息
        comment_dict.user = user_info
            
        # 检查当前用户的反应
        reaction = db.query(Reaction).filter(
            Reaction.comment_id == comment.id,
            Reaction.user_id == current_user["id"]
        ).first()
        
        if reaction:
            comment_dict.current_user_reaction = reaction.type.value
            
        items.append(comment_dict)
    
    # 计算总页数
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }