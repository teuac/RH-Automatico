import time
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.rbac import RoleChecker, get_active_user
from app.models.user import User
from app.parser.intelligent_parser import IntelligentParser
from app.google.sheets_service import google_sheets_service
from app.repositories.obra import obra_repository
from app.repositories.planilha import planilha_repository
from app.repositories.colaborador import colaborador_repository
from app.repositories.settings import system_settings_repository
from app.repositories.upload import upload_repository
from app.repositories.audit import audit_repository
from app.services.upload_service import sanitize_date_str, get_dynamic_tab_name
from app.config.logging_config import app_logger

router = APIRouter(prefix="/controle-vt", tags=["Controle VT"])
parser = IntelligentParser()

def get_default_valor_diario(db: Session) -> float:
    setting = system_settings_repository.get_by_key(db, "valor_diario_vt")
    if setting and setting.value:
        try:
            return float(setting.value.replace(",", "."))
        except ValueError:
            pass
    return 12.00

@router.post("/preview", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def preview_controle_vt(
    obra_id: int = Form(...),
    planilha_id: int = Form(...),
    valor_diario_vt: Optional[float] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    # 1. Obra & Planilha check
    obra = obra_repository.get(db, obra_id)
    if not obra or obra.status != "ATIVO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada ou inativa.")

    planilha = planilha_repository.get(db, planilha_id)
    if not planilha or planilha.status != "ATIVO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada ou inativa.")

    if not valor_diario_vt or valor_diario_vt <= 0:
        valor_diario_vt = get_default_valor_diario(db)

    # 2. Parse file content
    content = await file.read()
    filename = file.filename or "arquivo.xlsx"
    ext = filename.split(".")[-1].lower()

    if ext not in ["txt", "csv", "xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato .{ext} não suportado. Utilize TXT, CSV ou XLSX."
        )

    try:
        if ext == "txt":
            parsed = parser.parse_txt(content.decode("utf-8", errors="ignore"))
        elif ext == "csv":
            parsed = parser.parse_csv(content.decode("utf-8", errors="ignore"))
        else:
            parsed = parser.parse_xlsx(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro ao ler arquivo: {str(e)}"
        )

    if not parsed.funcionarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma marcação de ponto válida encontrada no arquivo."
        )

    # 3. Group by employee and dates
    # Build mapping: mat -> { nome, dates_set }
    emp_map: Dict[str, Dict[str, Any]] = {}
    all_dates = set()

    for func in parsed.funcionarios:
        mat_norm = func.matricula.strip().lstrip("0")
        if not mat_norm:
            continue
            
        entry_date = sanitize_date_str(func.data or parsed.data)
        all_dates.add(entry_date)

        if mat_norm not in emp_map:
            emp_map[mat_norm] = {
                "matricula": func.matricula.strip(),
                "nome": func.nome.strip(),
                "dates": set()
            }
        
        # Consider present if horarios exist or row registered
        if func.horarios or len(func.horarios) > 0 or func.data:
            emp_map[mat_norm]["dates"].add(entry_date)

    sorted_dates = sorted(list(all_dates))

    # Fetch DB active colaboradores for status match
    active_colabs = colaborador_repository.get_multi(db, limit=1000, obra_id=obra_id, status="ATIVO")
    db_mats = {c.matricula.strip().lstrip("0"): c for c in active_colabs}

    preview_rows = []
    total_presences = 0
    processed_db_mats = set()

    for mat_norm, info in emp_map.items():
        matched_c = db_mats.get(mat_norm)
        if matched_c:
            processed_db_mats.add(mat_norm)
        days_present = len(info["dates"])
        total_presences += days_present
        total_val = round(days_present * valor_diario_vt, 2)

        preview_rows.append({
            "matricula": info["matricula"],
            "nome": matched_c.nome if matched_c else info["nome"],
            "status_match": "ENCONTRADO" if matched_c else "NAO_CADASTRADO",
            "dias_presenca": days_present,
            "datas_presenca": sorted(list(info["dates"])),
            "valor_total": total_val
        })

    # Include active DB colaboradores not present in the file
    for c_mat, c_obj in db_mats.items():
        if c_mat not in processed_db_mats:
            preview_rows.append({
                "matricula": c_obj.matricula,
                "nome": c_obj.nome,
                "status_match": "ENCONTRADO",
                "dias_presenca": 0,
                "datas_presenca": [],
                "valor_total": 0.00
            })

    estimated_total = round(total_presences * valor_diario_vt, 2)
    processing_time = round((time.time() - start_time) * 1000, 2)

    return {
        "obra": {"id": obra.id, "nome": obra.nome, "codigo": obra.codigo},
        "planilha": {"id": planilha.id, "nome": planilha.nome},
        "valor_diario_vt": valor_diario_vt,
        "datas_encontradas": sorted_dates,
        "total_colaboradores": len(preview_rows),
        "total_presencas": total_presences,
        "valor_total_estimado": estimated_total,
        "tempo_processamento_ms": processing_time,
        "linhas_preview": preview_rows
    }

@router.post("/process", dependencies=[Depends(RoleChecker(["Administrador", "RH"]))])
async def process_controle_vt(
    request: Request,
    obra_id: int = Form(...),
    planilha_id: int = Form(...),
    valor_diario_vt: Optional[float] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    start_time = time.time()

    obra = obra_repository.get(db, obra_id)
    if not obra or obra.status != "ATIVO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra não encontrada.")

    planilha = planilha_repository.get(db, planilha_id)
    if not planilha or planilha.status != "ATIVO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")

    if not valor_diario_vt or valor_diario_vt <= 0:
        valor_diario_vt = get_default_valor_diario(db)

    content = await file.read()
    filename = file.filename or "arquivo.xlsx"
    ext = filename.split(".")[-1].lower()

    if ext not in ["txt", "csv", "xlsx"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de arquivo inválido.")

    try:
        if ext == "txt":
            parsed = parser.parse_txt(content.decode("utf-8", errors="ignore"))
        elif ext == "csv":
            parsed = parser.parse_csv(content.decode("utf-8", errors="ignore"))
        else:
            parsed = parser.parse_xlsx(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Erro no parser: {str(e)}")

    if not parsed.funcionarios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma marcação encontrada.")

    # Group by date -> list of employee presences
    # map: date_str -> list of { "matricula": ..., "nome": ..., "status": "A" }
    by_date: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for func in parsed.funcionarios:
        entry_date = sanitize_date_str(func.data or parsed.data)
        mat_clean = func.matricula.strip()
        if not mat_clean:
            continue

        if entry_date not in by_date:
            by_date[entry_date] = {}

        by_date[entry_date][mat_clean] = {
            "matricula": mat_clean,
            "nome": func.nome.strip(),
            "status": "A"
        }

    total_updated = 0
    total_ignored = 0
    total_pending = 0
    synced_dates = []

    from app.repositories.atestado import atestado_repository

    for date_str, emp_dict in by_date.items():
        tab_name, year, month = get_dynamic_tab_name(date_str, planilha.nome_aba)
        google_sheets_service.ensure_tab_exists(planilha.planilha_google_id, tab_name, year, month, obra.nome, valor_diario_vt=valor_diario_vt)

        # Check for active atestados on this date
        try:
            target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            active_atestados = atestado_repository.get_active_atestados_for_date(db, target_dt, obra_id=obra_id)
            for at in active_atestados:
                if at.colaborador and at.colaborador.matricula:
                    mat_c = at.colaborador.matricula.strip()
                    if mat_c not in emp_dict:
                        emp_dict[mat_c] = {
                            "matricula": mat_c,
                            "nome": at.colaborador.nome.strip(),
                            "status": "J"  # Justificativa / Atestado
                        }
        except Exception:
            pass

        emp_list = list(emp_dict.values())
        sync_results = google_sheets_service.batch_sync_presence(
            spreadsheet_id=planilha.planilha_google_id,
            tab_name=tab_name,
            date_str=date_str,
            employees=emp_list,
            valor_diario_vt=valor_diario_vt
        )

        synced_dates.append(date_str)

        for _, result_status, _ in sync_results:
            if result_status == "ATUALIZADO":
                total_updated += 1
            elif result_status == "IGNORADO":
                total_ignored += 1
            elif result_status == "PENDENTE":
                total_pending += 1

    processing_time_ms = round((time.time() - start_time) * 1000, 2)
    total_vt_val = round(total_updated * valor_diario_vt, 2)

    # Save Upload Record
    upload_rec = upload_repository.create(db, {
        "user_id": current_user.id,
        "obra_id": obra.id,
        "planilha_id": planilha.id,
        "filename": filename,
        "total_employees": len(parsed.funcionarios),
        "updated_count": total_updated,
        "ignored_count": total_ignored,
        "pending_count": total_pending,
        "processing_time_ms": processing_time_ms
    })

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
        action="SYNC_VT",
        description=f"Sincronizou Controle VT para Obra '{obra.nome}' ({len(synced_dates)} datas, Total VT R$ {total_vt_val:.2f})",
        object_changed="uploads",
        object_id=str(upload_rec.id),
        result="SUCESSO"
    )

    return {
        "message": f"Controle VT sincronizado com sucesso ({len(synced_dates)} datas processadas).",
        "upload_id": upload_rec.id,
        "total_colaboradores": len(parsed.funcionarios),
        "total_atualizados": total_updated,
        "total_ignorados": total_ignored,
        "total_pendentes": total_pending,
        "datas_processadas": synced_dates,
        "valor_diario_vt": valor_diario_vt,
        "valor_total_vt": total_vt_val,
        "tempo_processamento_ms": processing_time_ms
    }
