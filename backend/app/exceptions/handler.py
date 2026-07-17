import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config.logging_config import error_logger
from app.database.session import SessionLocal
from app.models.system_log import SystemLog

def register_exception_handlers(app):
    """
    Registers global exception interceptors for unified error responses
    and internal system log persistence.
    """
    
    def log_to_database(level: str, message: str, exception: Exception):
        """Helper to save critical application errors into system_logs table"""
        db = SessionLocal()
        try:
            trace = traceback.format_exc()
            db_log = SystemLog(
                level=level,
                message=message,
                module=exception.__class__.__name__,
                exception_trace=trace
            )
            db.add(db_log)
            db.commit()
        except Exception as db_err:
            error_logger.error(f"Failed to log error to DB: {str(db_err)}")
        finally:
            db.close()

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        error_logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        error_logger.warning(f"Validation error on {request.url.path}: {str(exc.errors())}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Os dados enviados são inválidos.",
                "errors": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Full stack trace is written to rotating error log files on the host
        error_logger.exception(f"Unhandled Exception on {request.url.path}: {str(exc)}")
        
        # Persistent database log
        log_to_database("ERROR", f"Unhandled Exception: {str(exc)}", exc)
        
        # User gets a general friendly error message - NO trace leakage!
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Ocorreu um erro interno no servidor. Por favor, tente novamente mais tarde."}
        )
