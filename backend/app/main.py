from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes.api import api_router
from app.exceptions.handler import register_exception_handlers
from app.database.session import SessionLocal, Base, engine
from app.models.role import Role
from app.models.permission import Permission

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Sistema RH - Automação de Presença",
    description="Sistema corporativo de processamento de ponto e sincronização com Google Sheets.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to match frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register consolidated API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")

# Global Exception handling mapping
register_exception_handlers(app)

@app.on_event("startup")
def setup_initial_database_fixtures():
    """Seeds default Roles into PostgreSQL upon startup if missing"""
    db = SessionLocal()
    try:
        # Create roles
        roles_to_seed = {
            "Administrador": "Acesso completo a todas as telas, configurações e gerenciamento de usuários.",
            "RH": "Permissão para importar arquivos de presença e visualizar histórico de uploads.",
            "Consulta": "Permissão de leitura para relatórios e acompanhamento de obras."
        }
        
        for name, desc in roles_to_seed.items():
            existing_role = db.query(Role).filter(Role.name == name).first()
            if not existing_role:
                db.add(Role(name=name, description=desc))
                
        db.commit()
    except Exception as e:
        print(f"Error seeding db roles: {str(e)}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "RH Presence Automation API is running. Access /docs for swagger spec."}
