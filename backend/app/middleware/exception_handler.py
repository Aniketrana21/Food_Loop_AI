"""
FoodLoop AI - Centralized Exception Handling
Transforms all application exceptions, validation errors, and database exceptions
into the standardized enterprise JSON envelope without leaking internal stack traces.
"""
import logging
from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.utils.exceptions import AppException
from app.utils.response import error_response

logger = logging.getLogger("foodloop.exceptions")


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.warning(f"[{req_id}] AppException ({exc.code}): {exc.message}")
        content = error_response(
            code=exc.code,
            message=exc.message,
            request_id=req_id,
            details=exc.details if exc.details else None
        )
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        
        # Determine code based on HTTP status
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        if isinstance(exc.detail, dict):
            details_dict = exc.detail
            detail_msg = details_dict.get("message", str(exc.detail))
        else:
            details_dict = None
            detail_msg = str(exc.detail)
        
        logger.warning(f"[{req_id}] HTTPException ({code} - {exc.status_code}): {detail_msg}")
        content = error_response(
            code=code,
            message=detail_msg,
            request_id=req_id,
            details=details_dict
        )
        content["detail"] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        
        # Build human-friendly message
        fields = [f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors[:3]]
        friendly_message = f"Request validation failed: {'; '.join(fields)}"

        logger.warning(f"[{req_id}] RequestValidationError: {friendly_message}")
        content = error_response(
            code="VALIDATION_ERROR",
            message=friendly_message,
            request_id=req_id,
            details={"validation_errors": errors}
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.error(f"[{req_id}] Database IntegrityError: {str(exc.orig)}")
        content = error_response(
            code="DATABASE_CONFLICT_ERROR",
            message="A database integrity constraint violation occurred (e.g. duplicate key or foreign key violation).",
            request_id=req_id
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=content)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.error(f"[{req_id}] Database SQLAlchemyError: {str(exc)}")
        content = error_response(
            code="DATABASE_ERROR",
            message="An unexpected database error occurred while processing the transaction.",
            request_id=req_id
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.error(f"[{req_id}] Unhandled Exception: {str(exc)}", exc_info=True)
        content = error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred. Please contact support.",
            request_id=req_id
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
