from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContratacaoCreate(BaseModel):
    nome_candidato: str = Field(..., min_length=2, max_length=255)
    cargo: str = Field(..., min_length=2, max_length=150)
    telefone: str = Field(..., min_length=10, max_length=50)


class ContratacaoUpdate(BaseModel):
    status: Optional[str] = None
    current_step: Optional[int] = None
    possui_dependentes_14: Optional[str] = None
    optante_vt: Optional[str] = None
    dados_bancarios: Optional[str] = None


class ContratacaoDocumentResponse(BaseModel):
    id: int
    tipo_documento: str
    file_path: Optional[str] = None
    qualidade_valida: Optional[bool] = None
    validade_valida: Optional[bool] = None
    legitimidade_valida: Optional[bool] = None
    ocr_status: str
    feedback_recusa: Optional[str] = None
    extracted_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContratacaoMessageResponse(BaseModel):
    id: int
    sender: str
    text: Optional[str] = None
    type: str
    media_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContratacaoResponse(BaseModel):
    id: int
    nome_candidato: str
    cargo: str
    telefone: str
    status: str
    motivo_rejeicao: Optional[str] = None
    current_step: int
    possui_dependentes_14: Optional[str] = None
    optante_vt: Optional[str] = None
    dados_bancarios: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    documentos: List[ContratacaoDocumentResponse] = []
    mensagens: List[ContratacaoMessageResponse] = []

    class Config:
        from_attributes = True
