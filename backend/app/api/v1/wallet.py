"""
钱包管理API路由
提供存钱罐和零花钱的RESTful API接口
"""
from typing import List
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.response import success_response
from app.schemas.wallet import (
    TransactionCreate,
    SavingsBoxResponse,
    PocketMoneyResponse,
    WalletTransactionResponse,
    WalletOverview
)
from app.services.wallet_service import WalletService

router = APIRouter()


@router.get("/{child_id}/overview", response_model=dict)
async def get_wallet_overview(
    child_id: int = Path(..., description="小朋友ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定小朋友的钱包总览
    
    返回信息包括:
    - 存钱罐信息（余额、利息等）
    - 零花钱信息（余额）
    - 最近10条交易记录
    
    对应API: GET /api/v1/wallet/{child_id}/overview
    """
    service = WalletService(db)
    overview = await service.get_wallet_overview(child_id)
    
    return success_response(
        data=overview,
        message="获取钱包总览成功"
    )


# ============ 存钱罐相关接口 ============

@router.post("/{child_id}/savings-box/deposit", response_model=dict)
async def savings_box_deposit(
    child_id: int = Path(..., description="小朋友ID"),
    data: TransactionCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    存钱罐存款
    
    业务逻辑:
    1. 验证小朋友存在
    2. 更新存钱罐余额
    3. 记录交易明细
    
    对应API: POST /api/wallet/{child_id}/savings-box/deposit
    
    请求体:
    - amount: 存款金额（必须大于0）
    - remark: 交易备注（可选）
    """
    service = WalletService(db)
    result = await service.savings_box_deposit(
        child_id=child_id,
        amount=data.amount,
        remark=data.remark
    )
    
    return success_response(
        data=result,
        message=f"存钱罐存款成功，金额: ¥{data.amount}"
    )


@router.post("/{child_id}/savings-box/withdraw", response_model=dict)
async def savings_box_withdraw(
    child_id: int = Path(..., description="小朋友ID"),
    data: TransactionCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    存钱罐取款
    
    业务逻辑:
    1. 验证小朋友存在
    2. 验证余额是否充足
    3. 更新存钱罐余额
    4. 记录交易明细
    
    对应API: POST /api/wallet/{child_id}/savings-box/withdraw
    
    请求体:
    - amount: 取款金额（必须大于0）
    - remark: 交易备注（可选）
    
    注意: 余额不足时会返回400错误
    """
    service = WalletService(db)
    result = await service.savings_box_withdraw(
        child_id=child_id,
        amount=data.amount,
        remark=data.remark
    )
    
    return success_response(
        data=result,
        message=f"存钱罐取款成功，金额: ¥{data.amount}"
    )


@router.get("/{child_id}/savings-box", response_model=dict)
async def get_savings_box(
    child_id: int = Path(..., description="小朋友ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取存钱罐信息
    
    返回信息包括:
    - 当前余额
    - 累计利息
    - 利率
    - 最后计息日期
    - 当日待结算利息（计算属性）
    
    对应API: GET /api/wallet/{child_id}/savings-box
    """
    service = WalletService(db)
    result = await service.get_savings_box(child_id)
    
    return success_response(
        data=result,
        message="获取存钱罐信息成功"
    )


@router.get("/{child_id}/savings-box/transactions", response_model=dict)
async def get_savings_box_transactions(
    child_id: int = Path(..., description="小朋友ID"),
    limit: int = Query(10, description="返回记录数", ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    获取存钱罐交易明细
    
    返回指定数量的交易记录，按时间倒序排列
    
    对应API: GET /api/wallet/{child_id}/savings-box/transactions
    
    查询参数:
    - limit: 返回记录数（默认10，最大100）
    """
    service = WalletService(db)
    transactions = await service.get_savings_box_transactions(
        child_id=child_id,
        limit=limit
    )
    
    return success_response(
        data=transactions,
        message=f"获取存钱罐交易明细成功，共 {len(transactions)} 条记录"
    )


# ============ 零花钱相关接口 ============

@router.post("/{child_id}/pocket-money/deposit", response_model=dict)
async def pocket_money_deposit(
    child_id: int = Path(..., description="小朋友ID"),
    data: TransactionCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    零花钱存款
    
    业务逻辑:
    1. 验证小朋友存在
    2. 更新零花钱余额
    3. 记录交易明细
    
    对应API: POST /api/wallet/{child_id}/pocket-money/deposit
    
    请求体:
    - amount: 存款金额（必须大于0）
    - remark: 交易备注（可选）
    """
    service = WalletService(db)
    result = await service.pocket_money_deposit(
        child_id=child_id,
        amount=data.amount,
        remark=data.remark
    )
    
    return success_response(
        data=result,
        message=f"零花钱存款成功，金额: ¥{data.amount}"
    )


@router.post("/{child_id}/pocket-money/withdraw", response_model=dict)
async def pocket_money_withdraw(
    child_id: int = Path(..., description="小朋友ID"),
    data: TransactionCreate = ...,
    db: AsyncSession = Depends(get_db)
):
    """
    零花钱取款
    
    业务逻辑:
    1. 验证小朋友存在
    2. 验证余额是否充足
    3. 更新零花钱余额
    4. 记录交易明细
    
    对应API: POST /api/wallet/{child_id}/pocket-money/withdraw
    
    请求体:
    - amount: 取款金额（必须大于0）
    - remark: 交易备注（可选）
    
    注意: 余额不足时会返回400错误
    """
    service = WalletService(db)
    result = await service.pocket_money_withdraw(
        child_id=child_id,
        amount=data.amount,
        remark=data.remark
    )
    
    return success_response(
        data=result,
        message=f"零花钱取款成功，金额: ¥{data.amount}"
    )


@router.get("/{child_id}/pocket-money", response_model=dict)
async def get_pocket_money(
    child_id: int = Path(..., description="小朋友ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取零花钱信息
    
    返回信息包括:
    - 当前余额
    - 创建时间
    - 更新时间
    
    对应API: GET /api/wallet/{child_id}/pocket-money
    """
    service = WalletService(db)
    result = await service.get_pocket_money(child_id)
    
    return success_response(
        data=result,
        message="获取零花钱信息成功"
    )


@router.get("/{child_id}/pocket-money/transactions", response_model=dict)
async def get_pocket_money_transactions(
    child_id: int = Path(..., description="小朋友ID"),
    limit: int = Query(10, description="返回记录数", ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    获取零花钱交易明细
    
    返回指定数量的交易记录，按时间倒序排列
    
    对应API: GET /api/wallet/{child_id}/pocket-money/transactions
    
    查询参数:
    - limit: 返回记录数（默认10，最大100）
    """
    service = WalletService(db)
    transactions = await service.get_pocket_money_transactions(
        child_id=child_id,
        limit=limit
    )
    
    return success_response(
        data=transactions,
        message=f"获取零花钱交易明细成功，共 {len(transactions)} 条记录"
    )