from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.controllers.upload_controller import upload_controller
from app.schemas.upload import UploadResponse
from app.auth.rbac import RoleChecker
from app.services.upload_service import upload_service

router = APIRouter(prefix="/uploads", tags=["Uploads & Sincronização"])

@router.get("/history", response_model=List[UploadResponse], dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_upload_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return upload_controller.get_history(skip, limit, db)

@router.get("/pending", dependencies=[Depends(RoleChecker(["Administrador", "RH", "Consulta"]))])
def get_pending_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return upload_controller.get_pending_records(skip, limit, db)

@router.put("/pending/{record_id}/resolve", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
def resolve_pending_entry(
    record_id: int,
    status_action: str = Form(...),  # 'RESOLVIDO' or 'IGNORADO'
    db: Session = Depends(get_db)
):
    return upload_controller.resolve_pending(record_id, status_action, db)


from fastapi.responses import StreamingResponse
from app.auth.rbac import get_active_user
from app.repositories.audit import audit_repository
from app.repositories.obra import obra_repository
from app.repositories.planilha import planilha_repository
import io

@router.post("/process-pdf-alimentation", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def process_pdf_alimentation_route(
    request: Request,
    tipo_refeicao: str = Form(...), # 'almoco' or 'jantar'
    file: UploadFile = File(...),
    obra_id: Optional[int] = Form(None),
    planilha_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    content = await file.read()
    if tipo_refeicao not in ["almoco", "jantar"]:
        raise HTTPException(
            status_code=400,
            detail="Tipo de refeição inválido. Deve ser 'almoco' ou 'jantar'."
        )

    try:
        xlsx_bytes, det_obra_id, det_plan_id, det_obra_nome, det_plan_nome = upload_service.process_pdf_alimentation(
            pdf_bytes=content,
            tipo_refeicao=tipo_refeicao,
            db=db,
            obra_id=obra_id,
            planilha_id=planilha_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Erro ao processar PDF: {str(e)}"
        )
        
    # Log Audit Trail
    auto_desc = " (Auto-detectado)" if not obra_id else ""
    audit_repository.log(
        db=db,
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        module="Alimentacao",
        screen="Alimentacao",
        action="GENERATE_REPORT",
        description=f"Gerou Relatório de Alimentação ({tipo_refeicao.upper()}) para Obra '{det_obra_nome}' e Planilha '{det_plan_nome}'{auto_desc}",
        object_changed="uploads",
        object_id=str(det_plan_id),
        result="SUCESSO"
    )

    refeicao_filename = "almoco" if tipo_refeicao == "almoco" else "jantar"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=relatorio_alimentacao_{refeicao_filename}.xlsx"}
    )

