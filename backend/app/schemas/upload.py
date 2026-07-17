from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmployeeSyncData(BaseModel):
    matricula: str
    nome: str
    horarios: List[str]
    presenca: Optional[str] = "A"  # "A" = alimentou, "F" = falta

class UploadCommitRequest(BaseModel):
    obra_id: int
    planilha_id: int
    date: str  # YYYY-MM-DD
    filename: str
    funcionarios: List[EmployeeSyncData]

class ObraShortResponse(BaseModel):
    id: int
    nome: str
    codigo: str

    class Config:
        from_attributes = True

class PlanilhaShortResponse(BaseModel):
    id: int
    nome: str
    planilha_google_id: str
    nome_aba: str

    class Config:
        from_attributes = True

class UserShortResponse(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    id: int
    filename: str
    total_employees: int
    updated_count: int
    ignored_count: int
    pending_count: int
    processing_time_ms: float
    created_at: datetime
    obra: ObraShortResponse
    planilha: PlanilhaShortResponse
    user: Optional[UserShortResponse] = None

    class Config:
        from_attributes = True
