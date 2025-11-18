from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    """
    便捷函数:返回成功响应的字典格式
    用于路由函数直接返回,FastAPI会自动转换为JSON
    """
    response = {
        "success": True,
        "data": data
    }
    if message:
        response["message"] = message
    return response


def error_response(message: str, errors: Optional[Dict[str, Any]] = None) -> dict:
    """
    便捷函数:返回错误响应的字典格式
    用于异常处理器中
    """
    response = {
        "success": False,
        "message": message
    }
    if errors:
        response["errors"] = errors
    return response


class APIResponse:
    """Unified API response format matching Laravel structure."""
    
    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200
    ) -> JSONResponse:
        """
        Return a successful response.
        
        Args:
            data: Response data (dict, list, or None)
            message: Optional success message
            status_code: HTTP status code (default: 200)
        
        Returns:
            JSONResponse with format:
            {
                "success": true,
                "data": {...},
                "message": "Optional message"
            }
        """
        response = {
            "success": True,
            "data": data
        }
        if message:
            response["message"] = message
        
        return JSONResponse(
            content=response,
            status_code=status_code
        )
    
    @staticmethod
    def error(
        message: str,
        errors: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> JSONResponse:
        """
        Return an error response.
        
        Args:
            message: Error message
            errors: Optional validation errors dict
            status_code: HTTP status code (default: 400)
        
        Returns:
            JSONResponse with format:
            {
                "success": false,
                "message": "Error description",
                "errors": {...}  // Only for 422 validation errors
            }
        """
        response = {
            "success": False,
            "message": message
        }
        if errors:
            response["errors"] = errors
        
        return JSONResponse(
            content=response,
            status_code=status_code
        )
    
    @staticmethod
    def created(data: Any, message: str = "Resource created successfully") -> JSONResponse:
        """Return a 201 Created response."""
        return APIResponse.success(data=data, message=message, status_code=201)
    
    @staticmethod
    def not_found(resource: str, id: int) -> JSONResponse:
        """Return a 404 Not Found response."""
        return APIResponse.error(
            message=f"{resource} with id {id} not found",
            status_code=404
        )
    
    @staticmethod
    def validation_error(errors: Dict[str, Any]) -> JSONResponse:
        """Return a 422 Validation Error response."""
        return APIResponse.error(
            message="Validation failed",
            errors=errors,
            status_code=422
        )