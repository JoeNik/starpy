"""
文件上传处理工具类
功能：图片验证、保存、删除
对应Laravel: app/Http/Controllers/ChildController.php 的文件处理逻辑
"""
import os
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import UploadFile, HTTPException
from PIL import Image

from app.core.config import settings


class FileHandler:
    """文件处理工具类"""
    
    # 允许的图片格式
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # 最大文件大小（2MB）
    MAX_FILE_SIZE = 2 * 1024 * 1024
    
    @classmethod
    async def save_avatar(cls, file: UploadFile) -> str:
        """
        保存头像文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            str: 保存后的文件相对路径 (avatars/xxx.jpg)
            
        Raises:
            HTTPException: 文件验证失败
        """
        # 1. 验证文件
        await cls._validate_image(file)
        
        # 2. 生成唯一文件名
        ext = Path(file.filename).suffix.lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        
        # 3. 确保目录存在
        upload_dir = Path(settings.UPLOAD_DIR) / "avatars"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 保存文件
        file_path = upload_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 5. 返回相对路径（用于数据库存储）
        return f"avatars/{filename}"
    
    @classmethod
    async def save_reward_image(cls, file: UploadFile) -> str:
        """
        保存奖品图片
        
        Args:
            file: 上传的文件对象
            
        Returns:
            str: 保存后的文件相对路径 (rewards/xxx.jpg)
            
        Raises:
            HTTPException: 文件验证失败
        """
        # 1. 验证文件
        await cls._validate_image(file)
        
        # 2. 生成唯一文件名
        ext = Path(file.filename).suffix.lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        
        # 3. 确保目录存在
        upload_dir = Path(settings.UPLOAD_DIR) / "rewards"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 保存文件
        file_path = upload_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # 5. 返回相对路径
        return f"rewards/{filename}"
    
    @classmethod
    async def delete_file(cls, relative_path: Optional[str]) -> None:
        """
        删除文件
        
        Args:
            relative_path: 文件相对路径（如 avatars/xxx.jpg）
        """
        if not relative_path:
            return
        
        file_path = Path(settings.UPLOAD_DIR) / relative_path
        if file_path.exists() and file_path.is_file():
            try:
                os.remove(file_path)
            except Exception:
                # 删除失败不影响主流程，记录日志即可
                pass
    
    @classmethod
    async def _validate_image(cls, file: UploadFile) -> None:
        """
        验证图片文件
        
        Args:
            file: 上传的文件对象
            
        Raises:
            HTTPException: 验证失败
        """
        # 1. 检查文件扩展名
        ext = Path(file.filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。允许的格式: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        # 2. 检查文件大小
        content = await file.read()
        file_size = len(content)
        
        if file_size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大2MB）"
            )
        
        # 3. 验证是否为有效图片
        try:
            # 重置文件指针
            await file.seek(0)
            
            # 使用Pillow验证图片
            image = Image.open(file.file)
            image.verify()
            
            # 再次重置文件指针，供后续使用
            await file.seek(0)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="无效的图片文件"
            )
    
    @classmethod
    def get_file_url(cls, relative_path: Optional[str]) -> Optional[str]:
        """
        获取文件访问URL
        
        Args:
            relative_path: 文件相对路径（如 avatars/xxx.jpg）
            
        Returns:
            str: 完整的访问URL，如 http://localhost:8000/storage/avatars/xxx.jpg
        """
        if not relative_path:
            return None
        
        # 拼接完整的URL
        api_url = settings.API_URL.rstrip("/")  # 移除尾部斜杠
        return f"{api_url}/storage/{relative_path}"