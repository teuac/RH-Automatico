from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmployeeSyncData(BaseModel):
    matricula: Optional[str] = ""
    nome: Optional[str] = ""
    horarios: Optional[List[str]] = []
    presenca: Optional[str] = "A"

class UploadCommitRequest(BaseModel):
    obra_id: int
    planilha_id: int
    date: Optional[str] = None
    date_str: Optional[str] = None
    filename: Optional[str] = "upload.txt"
    funcionarios: Optional[List[EmployeeSyncData]] = []
    linhas_preview: Optional[List[EmployeeSyncData]] = []

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
