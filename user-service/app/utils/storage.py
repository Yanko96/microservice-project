import io
import uuid
from datetime import timedelta
from typing import Optional, BinaryIO

from fastapi import UploadFile
from minio import Minio
from minio.commonconfig import Tags
from minio.error import S3Error

from app.core.config import settings

class StorageService:
    """对象存储服务封装，使用MinIO作为后端"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """确保所需的存储桶存在"""
        if not self.client.bucket_exists(settings.MINIO_USER_BUCKET):
            self.client.make_bucket(settings.MINIO_USER_BUCKET)
            # 设置为公共可读
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{settings.MINIO_USER_BUCKET}/*"]
                    }
                ]
            }
            self.client.set_bucket_policy(settings.MINIO_USER_BUCKET, policy)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: str = "uploads", 
        object_name: Optional[str] = None,
        tags: Optional[dict] = None,
    ) -> str:
        """
        上传文件到对象存储
        
        参数:
            file: 要上传的文件
            folder: 存储的子文件夹
            object_name: 对象名称，如果不提供将生成唯一名称
            tags: 对象标签
        
        返回:
            对象的访问URL
        """
        # 生成唯一文件名
        if not object_name:
            file_ext = file.filename.split(".")[-1] if "." in file.filename else ""
            object_name = f"{uuid.uuid4().hex}"
            if file_ext:
                object_name = f"{object_name}.{file_ext}"
        
        # 构建完整路径
        path = f"{folder}/{object_name}" if folder else object_name
        
        # 将文件内容读入内存
        content = await file.read()
        file_size = len(content)
        content_stream = io.BytesIO(content)
        
        # 上传文件
        try:
            result = self.client.put_object(
                bucket_name=settings.MINIO_USER_BUCKET,
                object_name=path,
                data=content_stream,
                length=file_size,
                content_type=file.content_type or "application/octet-stream",
            )
            
            # 如果有标签，设置对象标签
            if tags:
                self.client.set_object_tags(
                    bucket_name=settings.MINIO_USER_BUCKET,
                    object_name=path,
                    tags=Tags(tags),
                )
            
            # 返回对象URL
            # 对于公开可读的存储桶，可以使用以下URL格式
            if settings.MINIO_SECURE:
                protocol = "https"
            else:
                protocol = "http"
            
            return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_USER_BUCKET}/{path}"
        
        except S3Error as err:
            raise Exception(f"文件上传失败: {err}")
        finally:
            # 确保文件指针回到开始位置，以便后续可能的读取
            await file.seek(0)
            content_stream.close()
    
    def get_presigned_url(
        self, 
        object_name: str, 
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        生成预签名URL用于访问私有对象
        
        参数:
            object_name: 对象名称
            expires: URL有效期
        
        返回:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=settings.MINIO_USER_BUCKET,
                object_name=object_name,
                expires=expires,
            )
            return url
        except S3Error as err:
            raise Exception(f"无法生成预签名URL: {err}")
    
    def delete_file(self, object_name: str) -> bool:
        """
        从对象存储中删除文件
        
        参数:
            object_name: 对象名称
        
        返回:
            是否成功删除
        """
        try:
            self.client.remove_object(
                bucket_name=settings.MINIO_USER_BUCKET,
                object_name=object_name,
            )
            return True
        except S3Error:
            return False

# 创建存储服务单例
storage = StorageService()