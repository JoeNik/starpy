"""
Children API路由
对应Laravel: routes/api.php中的children相关路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.file_handler import FileHandler

from app.api.deps import get_db
from app.core.response import success_response
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.services.child_service import ChildService

router = APIRouter()


@router.get("", response_model=dict)
async def get_children(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有小朋友列表
    
    对应API: GET /api/children
    对应Laravel: ChildController@index
    
    Returns:
        按created_at降序排列的小朋友列表
    """
    service = ChildService(db)
    children = await service.get_all(order_by="created_at_desc")
    
    # 构造包含完整头像URL的响应数据
    child_list = []
    for child in children:
        child_data = ChildResponse.model_validate(child)
        if child_data.avatar:
            child_data.avatar = FileHandler.get_file_url(child_data.avatar)
        child_list.append(child_data)
    
    return success_response(data=child_list)


@router.get("/{child_id}", response_model=dict)
async def get_child_detail(
    child_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取小朋友详情
    
    对应API: GET /api/children/{id}
    对应Laravel: ChildController@show
    
    包含:
    - 基本信息
    - 最近20条星星记录
    - 关联的奖品列表
    """
    service = ChildService(db)
    child = await service.get_child_detail(child_id)
    
    # 构造包含完整头像URL的响应数据
    child_data = ChildResponse.model_validate(child)
    if child_data.avatar:
        child_data.avatar = FileHandler.get_file_url(child_data.avatar)
    
    return success_response(data=child_data)


@router.post("", response_model=dict)
async def create_child(
    name: str = Form(...),
    birthday: str = Form(...),
    gender: str = Form(...),
    avatar: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    创建小朋友
    
    对应API: POST /api/children
    对应Laravel: ChildController@store
    
    支持头像上传(multipart/form-data):
    - 允许格式: jpg, jpeg, png, gif, webp
    - 文件大小限制: 2MB
    """
    # 构造ChildCreate数据
    child_data = ChildCreate(
        name=name,
        birthday=birthday,
        gender=gender
    )
    
    service = ChildService(db)
    child = await service.create_child(child_data, avatar)
    
    return success_response(
        data=ChildResponse.model_validate(child),
        message="创建成功"
    )


@router.post("/{child_id}", response_model=dict)
@router.put("/{child_id}", response_model=dict)
async def update_child(
    child_id: int,
    name: Optional[str] = Form(None),
    birthday: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    更新小朋友信息
    
    对应API: PUT /api/children/{id} 或 POST /api/children/{id} (带_method=PUT)
    对应Laravel: ChildController@update
    
    注意:
    - 如果上传新头像,会自动删除旧头像
    - 所有字段都是可选的,只更新提供的字段
    - 支持Laravel风格的表单方法伪造(_method=PUT)
    """
    # 构造ChildUpdate数据(只包含提供的字段)
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if birthday is not None:
        update_data['birthday'] = birthday
    if gender is not None:
        update_data['gender'] = gender
    
    child_data = ChildUpdate(**update_data)
    
    service = ChildService(db)
    child = await service.update_child(child_id, child_data, avatar)
    
    return success_response(
        data=ChildResponse.model_validate(child),
        message="更新成功"
    )


@router.delete("/{child_id}", response_model=dict)
async def delete_child(
    child_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除小朋友
    
    对应API: DELETE /api/children/{id}
    对应Laravel: ChildController@destroy
    
    级联删除:
    - 星星记录(star_records)
    - 奖品关联(reward_children)
    - 头像文件
    """
    service = ChildService(db)
    await service.delete_child(child_id)
    
    return success_response(message="删除成功")