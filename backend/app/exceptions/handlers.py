from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from .base import BaseApplicationException

async def application_exception_handler(request: Request, exc: BaseApplicationException) -> JSONResponse:
    logger.error(f"Application exception: {exc.message}")
    content = {
        "success": False,
        "message": exc.message,
    }
    if hasattr(exc, "errors") and getattr(exc, "errors"):
        content["errors"] = exc.errors
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation Error",
            "errors": exc.errors()
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal Server Error"
        }
    )
