from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ObraBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    codigo: str = Field(..., min_length=2, max_length=50)
    status: str = Field("ATIVO")  # 'ATIVO', 'INATIVO'
    observacoes: Optional[str] = None

class ObraCreate(ObraBase):
    pass

class ObraUpdate(BaseModel):
    nome: Optional[str] = None
    codigo: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

class ObraResponse(ObraBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
