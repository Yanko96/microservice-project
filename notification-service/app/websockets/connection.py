import asyncio
import json
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from jose import JWTError

from app.core.security import verify_token

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器，管理活跃的用户连接"""
    
    def __init__(self):
        """初始化连接管理器"""
        # 用户ID到活跃连接的映射
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """
        连接新的WebSocket
        
        参数:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        # 初始化用户的连接集
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        # 添加连接
        self.active_connections[user_id].add(websocket)
        logger.info(f"用户[{user_id}]建立了新的WebSocket连接，当前连接数: {len(self.active_connections[user_id])}")
    
    async def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """
        断开WebSocket连接
        
        参数:
            websocket: WebSocket连接
            user_id: 用户ID
        """
        # 从用户的连接集中移除
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # 如果用户没有活跃连接，移除用户
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
            logger.info(f"用户[{user_id}]断开了WebSocket连接")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int) -> bool:
        """
        向特定用户发送消息
        
        参数:
            message: 要发送的消息
            user_id: 接收消息的用户ID
            
        返回:
            是否成功发送消息
        """
        if user_id not in self.active_connections:
            return False
            
        # 添加时间戳
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # 发送消息到用户的所有连接
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"发送消息到用户[{user_id}]失败: {str(e)}")
                disconnected.add(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.active_connections[user_id].discard(connection)
        
        # 如果用户没有活跃连接，移除用户
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
            return False
            
        return True
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        广播消息给所有连接的用户
        
        参数:
            message: 要发送的消息
        """
        # 添加时间戳
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # 保存需要移除的用户和连接
        to_remove_users = []
        disconnected_connections = {}
        
        # 向所有用户发送消息
        for user_id, connections in self.active_connections.items():
            disconnected = set()
            
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息到用户[{user_id}]失败: {str(e)}")
                    disconnected.add(connection)
            
            # 记录断开的连接
            if disconnected:
                disconnected_connections[user_id] = disconnected
            
            # 如果所有连接都断开，标记删除用户
            if len(disconnected) == len(connections):
                to_remove_users.append(user_id)
        
        # 清理断开的连接
        for user_id, connections in disconnected_connections.items():
            self.active_connections[user_id] -= connections
        
        # 移除没有活跃连接的用户
        for user_id in to_remove_users:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
    
    def get_active_users_count(self) -> int:
        """获取活跃用户数量"""
        return len(self.active_connections)
    
    def get_user_connections_count(self, user_id: int) -> int:
        """获取特定用户的连接数量"""
        if user_id not in self.active_connections:
            return 0
            
        return len(self.active_connections[user_id])

# 创建连接管理器实例
connection_manager = ConnectionManager()

# WebSocket认证依赖
async def get_token_from_query(websocket: WebSocket) -> Optional[str]:
    """从查询参数中获取令牌"""
    token = websocket.query_params.get("token")
    return token

async def get_user_from_token(token: str) -> int:
    """从令牌中获取用户ID"""
    try:
        payload = verify_token(token)
        user_id = int(payload["sub"])
        return user_id
    except (JWTError, ValueError) as e:
        raise ValueError(f"无效的令牌: {str(e)}")

async def authenticate_websocket(websocket: WebSocket) -> int:
    """认证WebSocket连接，返回用户ID"""
    token = await get_token_from_query(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise ValueError("缺少认证令牌")
    
    try:
        user_id = await get_user_from_token(token)
        return user_id
    except ValueError as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise ValueError(f"认证失败: {str(e)}")