from fastapi import APIRouter
from app.routes import auth, obras, planilhas, uploads, usuarios, auditoria, dashboard, settings, colaboradores, controle_vt, atestados

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
api_router.include_router(colaboradores.router)
api_router.include_router(controle_vt.router)
api_router.include_router(atestados.router)
