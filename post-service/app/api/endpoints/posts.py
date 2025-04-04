from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File, Form, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import httpx
import json

from app.api.deps import get_current_user, check_ownership, get_pagination_params, get_user_service_client
from app.db.session import get_db
from app.models.post import Post, Tag, MediaType, Visibility
from app.models.reaction import Reaction, ReactionType
from app.schemas.post import (
    PostCreate, PostUpdate, Post as PostSchema, PostDetail, PostPage, PostFilter, 
    TagCreate, TagInDB, PostMedia
)
from app.utils.storage import storage
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=PostSchema)
async def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: PostCreate = None,
    content: str = Form(None),
    visibility: Visibility = Form(Visibility.PUBLIC),
    location: str = Form(None),
    tag_names: str = Form(""),
    files: List[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    """
    创建新帖子
    
    可以通过JSON正文或表单数据提交
    如果是表单提交，可以同时上传文件
    """
    # 如果是JSON提交，使用post_in
    if post_in:
        post_data = post_in.dict()
    else:
        # 处理表单提交
        post_data = {
            "content": content,
            "visibility": visibility,
            "location": location,
            "tag_names": tag_names.split(",") if tag_names else []
        }
    
    # 验证内容或文件至少有一个
    if not post_data.get("content") and not files:
        raise HTTPException(
            status_code=400,
            detail="必须提供内容或媒体文件"
        )
    
    # 创建帖子基础信息
    post = Post(
        user_id=current_user["id"],
        content=post_data.get("content"),
        visibility=post_data.get("visibility", Visibility.PUBLIC),
        location=post_data.get("location"),
        media_type=MediaType.NONE,
        media_urls=[]
    )
    
    # 处理上传文件
    if files and any(file.filename for file in files):
        file_list = []
        media_type = None
        
        for file in files:
            if not file.filename:
                continue
                
            # 验证文件类型
            if file.content_type in settings.ALLOWED_IMAGE_TYPES:
                if media_type and media_type != MediaType.IMAGE:
                    raise HTTPException(
                        status_code=400,
                        detail="不能混合上传不同类型的媒体文件"
                    )
                media_type = MediaType.IMAGE
            elif file.content_type in settings.ALLOWED_VIDEO_TYPES:
                if media_type and media_type != MediaType.VIDEO:
                    raise HTTPException(
                        status_code=400,
                        detail="不能混合上传不同类型的媒体文件"
                    )
                media_type = MediaType.VIDEO
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file.content_type}"
                )
            
            # 上传到存储服务
            object_name = f"user_{current_user['id']}/post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(file_list)}"
            file_url = await storage.upload_file(
                file=file,
                folder="posts",
                object_name=object_name,
                tags={"user_id": str(current_user["id"])}
            )
            
            # 添加到文件列表
            file_info = {
                "url": file_url,
                "type": media_type.value,
            }
            file_list.append(file_info)
        
        # 更新帖子媒体信息
        if file_list:
            post.media_type = media_type
            post.media_urls = file_list
    
    # 处理标签
    if "tag_names" in post_data and post_data["tag_names"]:
        for tag_name in post_data["tag_names"]:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
                
            # 检查标签是否存在
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, post_count=1)
                db.add(tag)
            else:
                tag.post_count += 1
            
            # 关联标签和帖子
            post.tags.append(tag)
    
    # 保存帖子
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # 返回带有用户信息的帖子
    result = PostSchema.from_orm(post)
    result.user = {
        "id": current_user["id"],
        "username": current_user["username"],
        "full_name": current_user.get("full_name"),
        "avatar_url": current_user.get("avatar_url")
    }
    
    return result

@router.get("/", response_model=PostPage)
async def read_posts(
    db: Session = Depends(get_db),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    visibility: Optional[Visibility] = Query(None, description="按可见性筛选"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client),
) -> Any:
    """
    获取帖子列表，支持分页和筛选
    """
    # 计算分页参数
    page = pagination["page"]
    size = pagination["size"]
    skip = (page - 1) * size
    
    # 构建查询
    query = db.query(Post)
    
    # 应用筛选条件
    if user_id:
        query = query.filter(Post.user_id == user_id)
        
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag)
    
    # 可见性筛选
    if visibility:
        # 如果要查看私有帖子，检查权限
        if visibility == Visibility.PRIVATE and not (current_user["id"] == user_id or current_user.get("is_superuser")):
            raise HTTPException(
                status_code=403,
                detail="无权查看私有帖子"
            )
        query = query.filter(Post.visibility == visibility)
    else:
        # 默认筛选条件：公开帖子或当前用户的帖子
        query = query.filter(
            (Post.visibility == Visibility.PUBLIC) | 
            (Post.user_id == current_user["id"])
        )
    
    # 按创建时间倒序排序
    query = query.order_by(Post.created_at.desc())
    
    # 获取总数
    total = query.count()
    
    # 应用分页
    posts = query.offset(skip).limit(size).all()
    
    # 获取需要查询的用户ID列表
    user_ids = list(set(post.user_id for post in posts))
    
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
    for post in posts:
        post_dict = PostSchema.from_orm(post)
        
        # 添加用户信息
        if post.user_id in users:
            post_dict.user = users[post.user_id]
            
        # 检查当前用户的反应
        reaction = db.query(Reaction).filter(
            Reaction.post_id == post.id,
            Reaction.user_id == current_user["id"]
        ).first()
        
        if reaction:
            post_dict.current_user_reaction = reaction.type.value
            
        items.append(post_dict)
    
    # 计算总页数
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{post_id}", response_model=PostDetail)
async def read_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client),
) -> Any:
    """
    获取特定帖子的详情
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 检查访问权限
    if post.visibility != Visibility.PUBLIC and post.user_id != current_user["id"] and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="无权查看该帖子"
        )
    
    # 增加浏览次数
    post.view_count += 1
    db.commit()
    
    # 获取用户信息
    user_info = None
    try:
        response = await user_client.get(f"/users/id/{post.user_id}")
        if response.status_code == 200:
            user_info = response.json()
    except httpx.RequestError:
        pass
    
    # 获取当前用户的反应
    reaction = db.query(Reaction).filter(
        Reaction.post_id == post.id,
        Reaction.user_id == current_user["id"]
    ).first()
    
    post_detail = PostDetail.from_orm(post)
    
    # 添加用户信息
    if user_info:
        post_detail.user = user_info
        
    # 添加当前用户的反应
    if reaction:
        post_detail.current_user_reaction = reaction.type.value
    
    # 获取热门评论（可以在这里添加获取热门评论的逻辑）
    # post_detail.top_comments = ...
    
    return post_detail

@router.put("/{post_id}", response_model=PostSchema)
async def update_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    post_in: PostUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    """
    更新帖子内容
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 检查权限
    if not await check_ownership(post.user_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权修改该帖子"
        )
    
    # 更新帖子字段
    update_data = post_in.dict(exclude_unset=True)
    
    # 特殊处理标签
    if "tag_names" in update_data:
        # 清除现有标签关联并更新标签计数
        for tag in post.tags:
            tag.post_count -= 1
            if tag.post_count <= 0:
                db.delete(tag)
        
        post.tags = []
        
        # 添加新标签
        for tag_name in update_data["tag_names"]:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
                
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, post_count=1)
                db.add(tag)
            else:
                tag.post_count += 1
            
            post.tags.append(tag)
        
        del update_data["tag_names"]
    
    # 更新其他字段
    for field, value in update_data.items():
        setattr(post, field, value)
    
    # 标记为已编辑
    post.is_edited = True
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return post

@router.delete("/{post_id}")
async def delete_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """
    删除帖子
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 检查权限
    if not await check_ownership(post.user_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权删除该帖子"
        )
    
    # 更新标签计数
    for tag in post.tags:
        tag.post_count -= 1
        if tag.post_count <= 0:
            db.delete(tag)
    
    # 删除帖子
    db.delete(post)
    db.commit()
    
    return {"message": "帖子已删除"}

@router.get("/tags/", response_model=List[TagInDB])
def read_tags(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    query: Optional[str] = None,
) -> Any:
    """
    获取标签列表
    """
    tags_query = db.query(Tag)
    
    if query:
        tags_query = tags_query.filter(Tag.name.ilike(f"%{query}%"))
    
    # 按帖子数量倒序排序
    tags = tags_query.order_by(Tag.post_count.desc()).offset(skip).limit(limit).all()
    
    return tags

@router.post("/{post_id}/pin", response_model=PostSchema)
async def pin_post(
    *,
    db: Session = Depends(get_db),
    post_id: int = Path(..., gt=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    """
    置顶/取消置顶帖子
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404,
            detail="帖子不存在"
        )
    
    # 检查权限（只有帖子作者或管理员可以置顶）
    if not await check_ownership(post.user_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="无权置顶该帖子"
        )
    
    # 切换置顶状态
    post.is_pinned = not post.is_pinned
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return post

@router.get("/user/{user_id}/posts", response_model=PostPage)
async def read_user_posts(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client),
) -> Any:
    """
    获取特定用户的帖子列表
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
    
    # 确定可见性过滤条件
    if user_id == current_user["id"] or current_user.get("is_superuser"):
        # 如果是本人或管理员，可以看到所有帖子
        visibility_filter = None
    else:
        # 否则只能看到公开帖子
        visibility_filter = Visibility.PUBLIC
    
    # 复用列表接口
    return await read_posts(
        db=db,
        pagination=pagination,
        user_id=user_id,
        tag=None,
        visibility=visibility_filter,
        current_user=current_user,
        user_client=user_client
    )