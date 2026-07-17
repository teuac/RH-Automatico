from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ColaboradorBase(BaseModel):
    matricula: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=2, max_length=255)
    funcao: Optional[str] = Field(None, max_length=150)
    obra_id: Optional[int] = None
    status: str = Field("ATIVO")  # 'ATIVO', 'INATIVO'


class ColaboradorCreate(ColaboradorBase):
    pass


class ColaboradorUpdate(BaseModel):
    matricula: Optional[str] = Field(None, max_length=50)
    nome: Optional[str] = Field(None, max_length=255)
    funcao: Optional[str] = Field(None, max_length=150)
    obra_id: Optional[int] = None
    status: Optional[str] = None


class ObraShortResponse(BaseModel):
    id: int
    nome: str
    codigo: str

    class Config:
        from_attributes = True


class ColaboradorResponse(ColaboradorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    obra: Optional[ObraShortResponse] = None

    class Config:
        from_attributes = True


# --- Importação em lote ---

class ColaboradorImportItem(BaseModel):
    matricula: str
    nome: str
    funcao: Optional[str] = None
    obra_codigo: Optional[str] = None  # Código da obra para lookup


class ColaboradorImportResponse(BaseModel):
    total: int
    importados: int
    ignorados: int
    erros: List[str] = []


# --- Migração de obra em massa ---

class MigrarObraRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    nova_obra_id: int
