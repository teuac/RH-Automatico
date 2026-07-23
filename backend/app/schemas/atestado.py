from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.schemas.colaborador import ColaboradorResponse

class AtestadoBase(BaseModel):
    colaborador_id: int
    data_inicio: date
    data_fim: date
    dias: Optional[int] = None
    cid: Optional[str] = None
    motivo: Optional[str] = None
    status: str = Field("HOMOLOGADO")  # 'HOMOLOGADO', 'PENDENTE', 'CANCELADO'
    observacoes: Optional[str] = None
    documento_url: Optional[str] = None

class AtestadoCreate(AtestadoBase):
    pass

class AtestadoUpdate(BaseModel):
    colaborador_id: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    dias: Optional[int] = None
    cid: Optional[str] = None
    motivo: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None
    documento_url: Optional[str] = None

class AtestadoResponse(AtestadoBase):
    id: int
    dias: int
    created_at: datetime
    updated_at: datetime
    colaborador: Optional[ColaboradorResponse] = None

    class Config:
        from_attributes = True
