from fastapi import APIRouter
from app.routes import auth, obras, planilhas, uploads, usuarios, auditoria, dashboard, settings

api_router = APIRouter()

# Register sub-routers
api_router.include_router(auth.router)
api_router.include_router(obras.router)
api_router.include_router(planilhas.router)
api_router.include_router(uploads.router)
api_router.include_router(usuarios.router)
api_router.include_router(auditoria.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
