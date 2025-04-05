# app/api/endpoints/search.py

from typing import Any, Dict, List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_current_user, get_pagination_params, get_user_service_client
from app.db.session import get_db
from app.utils.elasticsearch import es_service
from app.schemas.search import SearchResponse, SearchRequest

router = APIRouter()

@router.get("/", response_model=SearchResponse)
async def search_posts(
    query: str = Query(None, description="搜索关键词"),
    tags: List[str] = Query(None, description="按标签筛选"),
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    from_date: Optional[date] = Query(None, description="起始日期"),
    to_date: Optional[date] = Query(None, description="结束日期"),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    搜索帖子
    """
    # 计算分页参数
    page = pagination["page"]
    size = pagination["size"]
    
    # 转换日期格式
    from_date_str = None
    to_date_str = None
    
    if from_date:
        from_date_str = from_date.isoformat()
    
    if to_date:
        to_date_str = to_date.isoformat()
    
    # 执行搜索
    search_results = await es_service.search_posts(
        query=query,
        tags=tags,
        user_id=user_id,
        from_date=from_date_str,
        to_date=to_date_str,
        page=page,
        size=size
    )
    
    # 如果需要，获取用户信息
    if search_results["items"]:
        try:
            # 收集所有用户ID
            user_ids = set()
            for item in search_results["items"]:
                if "user_id" in item and item["user_id"]:
                    user_ids.add(item["user_id"])
            
            if user_ids:
                # 批量获取用户信息
                user_id_list = ",".join(map(str, user_ids))
                response = await user_client.get("/users/batch", params={"ids": user_id_list})
                
                if response.status_code == 200:
                    users = response.json()
                    users_dict = {user["id"]: user for user in users}
                    
                    # 为搜索结果添加完整的用户信息
                    for item in search_results["items"]:
                        user_id = item.get("user_id")
                        if user_id in users_dict:
                            item["user"] = users_dict[user_id]
        
        except Exception as e:
            # 记录错误但继续处理
            print(f"获取用户信息失败: {str(e)}")
    
    return search_results

@router.post("/", response_model=SearchResponse)
async def search_posts_advanced(
    search_request: SearchRequest,
    pagination: Dict[str, int] = Depends(get_pagination_params),
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_client: httpx.AsyncClient = Depends(get_user_service_client)
) -> Any:
    """
    高级搜索帖子（POST请求，支持更复杂的搜索条件）
    """
    # 计算分页参数
    page = pagination["page"]
    size = pagination["size"]
    
    # 转换日期格式
    from_date_str = None
    to_date_str = None
    
    if search_request.from_date:
        from_date_str = search_request.from_date.isoformat()
    
    if search_request.to_date:
        to_date_str = search_request.to_date.isoformat()
    
    # 执行搜索
    search_results = await es_service.search_posts(
        query=search_request.query,
        tags=search_request.tags,
        user_id=search_request.user_id,
        from_date=from_date_str,
        to_date=to_date_str,
        page=page,
        size=size
    )
    
    # 如果需要，获取用户信息
    if search_results["items"]:
        try:
            # 收集所有用户ID
            user_ids = set()
            for item in search_results["items"]:
                if "user_id" in item and item["user_id"]:
                    user_ids.add(item["user_id"])
            
            if user_ids:
                # 批量获取用户信息
                user_id_list = ",".join(map(str, user_ids))
                response = await user_client.get("/users/batch", params={"ids": user_id_list})
                
                if response.status_code == 200:
                    users = response.json()
                    users_dict = {user["id"]: user for user in users}
                    
                    # 为搜索结果添加完整的用户信息
                    for item in search_results["items"]:
                        user_id = item.get("user_id")
                        if user_id in users_dict:
                            item["user"] = users_dict[user_id]
        
        except Exception as e:
            # 记录错误但继续处理
            print(f"获取用户信息失败: {str(e)}")
    
    return search_results