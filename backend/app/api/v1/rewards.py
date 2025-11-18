"""
Rewards API路由
对应Laravel: routes/api.php中的rewards相关路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.response import success_response
from app.schemas.reward import RewardCreate, RewardUpdate, RewardRedeem, RewardResponse
from app.services.reward_service import RewardService
from app.utils.file_handler import FileHandler

router = APIRouter()


@router.get("", response_model=dict)
async def get_rewards(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有奖品列表
    
    对应API: GET /api/rewards
    对应Laravel: RewardController@index
    
    排序规则:
    1. 未兑换的在前(is_redeemed=False)
    2. 已兑换的在后(is_redeemed=True)
    3. 同状态内按created_at降序
    
    包含每个奖品的:
    - 关联的小朋友列表
    - 进度计算(total_stars/is_achieved)
    """
    service = RewardService(db)
    rewards = await service.get_all_rewards()
    
    # 转换图片路径为完整URL
    rewards_data = []
    for reward in rewards:
        reward_response = RewardResponse.model_validate(reward, from_attributes=True)
        if reward_response.image:
            reward_response.image = FileHandler.get_file_url(reward_response.image)
        
        # 转换嵌套children中的头像路径
        for child in reward_response.children:
            if child.avatar:
                child.avatar = FileHandler.get_file_url(child.avatar)
        
        rewards_data.append(reward_response)
    
    return success_response(data=rewards_data)


@router.get("/{reward_id}", response_model=dict)
async def get_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个奖品详情
    
    对应API: GET /api/rewards/{id}
    对应Laravel: RewardController@show
    
    返回包含:
    - 奖品基本信息
    - 关联的小朋友列表及进度
    - 计算属性(total_stars/is_achieved)
    """
    service = RewardService(db)
    reward = await service.get_reward(reward_id)
    
    if not reward:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Reward", reward_id)
    
    reward_data = RewardResponse.model_validate(reward, from_attributes=True)
    if reward_data.image:
        reward_data.image = FileHandler.get_file_url(reward_data.image)
    
    # 转换嵌套children中的头像路径
    for child in reward_data.children:
        if child.avatar:
            child.avatar = FileHandler.get_file_url(child.avatar)
    
    return success_response(data=reward_data)


@router.post("", response_model=dict)
async def create_reward(
    name: str = Form(...),
    star_cost: int = Form(...),
    description: Optional[str] = Form(None),
    child_ids: List[int] = Form(...),  # 支持多个同名字段
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    创建奖品
    
    对应API: POST /api/rewards
    对应Laravel: RewardController@store
    
    参数:
    - name: 奖品名称
    - star_cost: 所需星星数(>0)
    - description: 奖品描述(可选)
    - child_ids: 关联的小朋友ID数组(FormData多个同名字段)
    - image: 奖品图片(可选,2MB限制)
    """
    # 处理图片上传
    image_path = None
    if image:
        image_path = await FileHandler.save_reward_image(image)
    
    # 构造RewardCreate数据
    reward_data = RewardCreate(
        name=name,
        star_cost=star_cost,
        description=description,
        image=image_path,
        child_ids=child_ids
    )
    
    service = RewardService(db)
    reward = await service.create_reward(reward_data)
    
    # 重新查询以加载所有关系和计算属性
    reward = await service.get_reward(reward.id)
    
    reward_data = RewardResponse.model_validate(reward, from_attributes=True)
    if reward_data.image:
        reward_data.image = FileHandler.get_file_url(reward_data.image)
    
    # 转换嵌套children中的头像路径
    for child in reward_data.children:
        if child.avatar:
            child.avatar = FileHandler.get_file_url(child.avatar)
    
    return success_response(
        data=reward_data,
        message="创建成功"
    )


@router.post("/{reward_id}", response_model=dict)
@router.put("/{reward_id}", response_model=dict)
async def update_reward(
    reward_id: int,
    name: Optional[str] = Form(None),
    star_cost: Optional[int] = Form(None),
    child_ids: Optional[List[int]] = Form(None),  # 支持多个同名字段
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    更新奖品信息
    
    对应API: PUT /api/rewards/{id} 或 POST /api/rewards/{id} (带_method=PUT)
    对应Laravel: RewardController@update
    
    限制:
    - 已兑换的奖品不允许编辑(is_redeemed=True)
    
    注意:
    - 如果上传新图片,会自动删除旧图片
    - 所有字段都是可选的,只更新提供的字段
    - child_ids支持FormData中的多个同名字段
    """
    # 处理图片上传(在API层)
    image_path = None
    if image:
        image_path = await FileHandler.save_reward_image(image)
    
    # 构造RewardUpdate数据(只包含提供的字段)
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if star_cost is not None:
        update_data['star_cost'] = star_cost
    if image_path is not None:
        update_data['image'] = image_path
    if child_ids is not None:
        update_data['child_ids'] = child_ids
    
    reward_data = RewardUpdate(**update_data)
    
    service = RewardService(db)
    reward = await service.update_reward(reward_id, reward_data)
    
    # 重新查询以加载所有关系和计算属性
    reward = await service.get_reward(reward.id)
    
    reward_data = RewardResponse.model_validate(reward, from_attributes=True)
    if reward_data.image:
        reward_data.image = FileHandler.get_file_url(reward_data.image)
    
    # 转换嵌套children中的头像路径
    for child in reward_data.children:
        if child.avatar:
            child.avatar = FileHandler.get_file_url(child.avatar)
    
    return success_response(
        data=reward_data,
        message="更新成功"
    )


@router.delete("/{reward_id}", response_model=dict)
async def delete_reward(
    reward_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除奖品
    
    对应API: DELETE /api/rewards/{id}
    对应Laravel: RewardController@destroy
    
    限制:
    - 已兑换的奖品不允许删除(is_redeemed=True)
    
    级联删除:
    - 奖品关联(reward_children)
    - 图片文件
    """
    service = RewardService(db)
    await service.delete_reward(reward_id)
    
    return success_response(message="删除成功")


@router.post("/{reward_id}/redeem", response_model=dict)
async def redeem_reward(
    reward_id: int,
    redeem_data: RewardRedeem,
    db: AsyncSession = Depends(get_db)
):
    """
    兑换奖品
    
    对应API: POST /api/rewards/{id}/redeem
    对应Laravel: RewardController@redeem
    
    参数 (JSON Body):
    - deductions: 扣除分配方案
      格式: {"deductions": [{"child_id": 1, "amount": 5}, {"child_id": 2, "amount": 3}]}
    
    4层验证:
    1. 验证奖品存在且未兑换
    2. 验证deductions中的child_ids都在奖品关联中
    3. 验证总扣除数量等于star_cost
    4. 验证每个小朋友的星星余额充足
    
    复杂事务操作:
    1. 更新reward_children.deduction_amount
    2. 更新children.star_count(批量扣除)
    3. 创建star_records记录(type='redeem')
    4. 更新rewards.is_redeemed=True
    """
    service = RewardService(db)
    reward = await service.redeem_reward(reward_id, redeem_data)
    
    return success_response(
        data=RewardResponse.model_validate(reward),
        message="兑换成功"
    )