from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PlanilhaBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    planilha_google_id: str = Field(..., min_length=5)
    nome_aba: str = Field(..., min_length=1)
    automacao: str = Field("ALIMENTACAO")  # 'ALIMENTACAO', 'CONTROLE_VT'
    obra_id: Optional[int] = None
    status: str = Field("ATIVO")  # 'ATIVO', 'INATIVO'
    observacoes: Optional[str] = None

class PlanilhaCreate(PlanilhaBase):
    pass

class PlanilhaUpdate(BaseModel):
    nome: Optional[str] = None
    planilha_google_id: Optional[str] = None
    nome_aba: Optional[str] = None
    automacao: Optional[str] = None
    obra_id: Optional[int] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

class ObraShortResponse(BaseModel):
    id: int
    nome: str
    codigo: str

    class Config:
        from_attributes = True

class PlanilhaResponse(PlanilhaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    obra: Optional[ObraShortResponse] = None

    class Config:
        from_attributes = True
