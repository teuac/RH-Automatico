import io
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User
from app.services.upload_service import upload_service
from app.repositories.settings import system_settings_repository
from app.repositories.audit import audit_repository

router = APIRouter(prefix="/controle-vt", tags=["Controle VT"])

def get_default_valor_diario(db: Session) -> float:
    setting = system_settings_repository.get_by_key(db, "valor_diario_vt")
    if setting and setting.value:
        try:
            return float(setting.value.replace(",", "."))
        except ValueError:
            pass
    return 12.00

@router.post("/process-pdf", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def process_pdf_mirror(
    request: Request,
    file: UploadFile = File(...),
    valor_diario_vt: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    content = await file.read()
    
    if not valor_diario_vt or valor_diario_vt <= 0:
        valor_diario_vt = get_default_valor_diario(db)
        
    try:
        # We pass db so process_pdf_mirror can auto-detect the Obra and fetch active colaboradores
        xlsx_bytes, det_obra_id, det_obra_nome = upload_service.process_pdf_mirror(
            pdf_bytes=content,
            valor_diario_vt=valor_diario_vt,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro ao processar PDF: {str(e)}"
        )
        
    # Log Audit Trail
    audit_repository.log(
        db=db,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        module="ControleVT",
        screen="ControleVT",
        action="GENERATE_REPORT",
        description=f"Gerou Relatório de Vale Transporte para Obra '{det_obra_nome}' (R$ {valor_diario_vt:.2f} diários)",
        object_changed="uploads",
        object_id=str(det_obra_id),
        result="SUCESSO"
    )
        
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=relatorio_vale_transporte.xlsx"}
    )
