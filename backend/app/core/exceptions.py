from fastapi import HTTPException, status
from typing import Optional


class StarSavingsException(HTTPException):
    """Base exception for Star Savings application."""
    
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class AppException(Exception):
    """自定义应用异常基类 - 兼容main.py中的异常处理"""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """资源未找到异常 - 兼容main.py中的404处理"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ResourceNotFoundError(StarSavingsException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found"
        )


class InsufficientStarsError(StarSavingsException):
    """Raised when a child doesn't have enough stars for an operation."""
    
    def __init__(self, child_name: str, current: int, required: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{child_name} has insufficient stars (current: {current}, required: {required})"
        )


class RewardAlreadyRedeemedError(StarSavingsException):
    """Raised when attempting to modify or redeem an already redeemed reward."""
    
    def __init__(self, reward_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reward '{reward_name}' has already been redeemed"
        )


class ValidationError(StarSavingsException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class FileUploadError(StarSavingsException):
    """Raised when file upload fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )