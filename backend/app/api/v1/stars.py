"""
Star操作API路由
对应Laravel: routes/api.php中的stars相关路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.response import success_response
from app.schemas.star import StarAdd, StarSubtract
from app.services.star_service import StarService

router = APIRouter()


@router.post("/{child_id}/stars/add", response_model=dict)
async def add_stars(
    child_id: int,
    data: StarAdd,
    db: AsyncSession = Depends(get_db)
):
    """
    给小朋友加星
    
    对应API: POST /api/children/{id}/stars/add
    对应Laravel: StarController@add
    
    验证规则:
    - amount: 1-50之间
    - reason: 可选,最多255字符
    
    事务操作:
    1. 创建star_records记录(type='add')
    2. 更新children.star_count += amount
    """
    service = StarService(db)
    result = await service.add_stars(child_id, data)
    
    return success_response(
        data={
            "child_id": result["child"].id,
            "name": result["child"].name,
            "star_count": result["child"].star_count,
            "record": {
                "id": result["record"].id,
                "type": result["record"].type,
                "amount": result["record"].amount,
                "reason": result["record"].reason,
                "created_at": result["record"].created_at.isoformat()
            }
        },
        message=f"成功添加 {data.amount} 颗星星"
    )


@router.post("/{child_id}/stars/subtract", response_model=dict)
async def subtract_stars(
    child_id: int,
    data: StarSubtract,
    db: AsyncSession = Depends(get_db)
):
    """
    给小朋友减星
    
    对应API: POST /api/children/{id}/stars/subtract
    对应Laravel: StarController@subtract
    
    验证规则:
    - amount: 1-50之间
    - reason: 可选,最多255字符
    - 余额验证: 当前星星数必须 >= amount
    
    事务操作:
    1. 创建star_records记录(type='subtract')
    2. 更新children.star_count -= amount
    """
    service = StarService(db)
    result = await service.subtract_stars(child_id, data)
    
    return success_response(
        data={
            "child_id": result["child"].id,
            "name": result["child"].name,
            "star_count": result["child"].star_count,
            "record": {
                "id": result["record"].id,
                "type": result["record"].type,
                "amount": result["record"].amount,
                "reason": result["record"].reason,
                "created_at": result["record"].created_at.isoformat()
            }
        },
        message=f"成功扣除 {data.amount} 颗星星"
    )


@router.get("/{child_id}/stars", response_model=dict)
async def get_star_records(
    child_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取小朋友的星星记录
    
    业务逻辑:
    1. 验证小朋友存在
    2. 查询星星记录列表
    3. 按创建时间降序排序
    
    Returns:
        成功: {"code": 200, "data": [records], "message": "获取成功"}
        失败: {"code": 404, "message": "小朋友不存在"}
    """
    service = StarService(db)
    records = await service.get_records(child_id)
    
    return success_response(
        data=[{
            "id": record.id,
            "type": record.type,
            "amount": record.amount,
            "reason": record.reason,
            "reward_id": record.reward_id,
            "created_at": record.created_at.isoformat()
        } for record in records],
        message="获取星星记录成功"
    )