import time
import datetime
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status

from app.parser.intelligent_parser import IntelligentParser, ParsedData
from app.google.sheets_service import google_sheets_service
from app.repositories.obra import obra_repository
from app.repositories.planilha import planilha_repository
from app.repositories.upload import upload_repository
from app.repositories.pending_record import pending_record_repository
from app.repositories.audit import audit_repository
from app.models.user import User
from app.config.logging_config import app_logger

def get_portuguese_month_name(month: int) -> str:
    months = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
    }
    return months.get(month, "Desconhecido")

def sanitize_date_str(date_input: Optional[str]) -> str:
    if not date_input or str(date_input).strip() in ("NaT", "nan", "NaN", "None", ""):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")
    
    val = str(date_input).strip()
    if len(val) == 10 and val.count("-") == 2:
        parts = val.split("-")
        if len(parts[0]) == 4 and parts[1].isdigit() and parts[2].isdigit():
            return val
            
    if " " in val:
        first_part = val.split()[0]
        if len(first_part) == 10 and first_part.count("-") == 2:
            return first_part
            
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")

def get_dynamic_tab_name(final_date: str, fallback_tab_name: str) -> tuple[str, int, int]:
    date_parts = final_date.split("-")
    if len(date_parts) == 3:
        try:
            year = int(date_parts[0])
            month = int(date_parts[1])
            month_name = get_portuguese_month_name(month)
            return f"{month_name} {year}", year, month
        except ValueError:
            pass
            
    if not fallback_tab_name or fallback_tab_name.upper() == "AUTO":
        now = datetime.datetime.utcnow()
        month_name = get_portuguese_month_name(now.month)
        return f"{month_name} {now.year}", now.year, now.month
        
    return fallback_tab_name, 2026, 7

class UploadService:
    """
    Business logic layer for handling presence file uploads, previewing parsed entries,
    and synchronizing presence marks with Google Sheets.
    """

    def __init__(self):
        self.parser = IntelligentParser()

    def _parse_file(self, content: bytes, filename: str, content_type: str) -> ParsedData:
        # Check standard formats
        ext = filename.split(".")[-1].lower()
        if ext not in ["txt", "csv", "xlsx"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão de arquivo não suportada: .{ext}. Formatos suportados: TXT, CSV, XLSX"
            )
        
        try:
            if ext == "txt":
                text = content.decode("utf-8", errors="ignore")
                return self.parser.parse_txt(text)
            elif ext == "csv":
                text = content.decode("utf-8", errors="ignore")
                return self.parser.parse_csv(text)
            else: # xlsx
                return self.parser.parse_xlsx(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro ao processar conteúdo do arquivo {filename}: {str(e)}"
            )

    def generate_preview(
        self,
        db: Session,
        obra_id: int,
        planilha_id: int,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        override_date: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Fetch Obra
        obra = obra_repository.get(db, obra_id)
        if not obra or obra.status != "ATIVO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Obra não encontrada ou inativa."
            )

        # 2. Fetch Planilha
        planilha = planilha_repository.get(db, planilha_id)
        if not planilha or planilha.status != "ATIVO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planilha de destino não encontrada ou inativa."
            )

        # 3. Parse file contents
        parsed = self._parse_file(file_bytes, filename, content_type)

        # 4. Determine Date
        final_date = sanitize_date_str(override_date or parsed.data)

        # Determine dynamic tab name based on final_date
        tab_name, year, month = get_dynamic_tab_name(final_date, planilha.nome_aba)

        # Ensure the sheet tab exists in Google Sheets before fetching
        _, tab_criada = google_sheets_service.ensure_tab_exists(planilha.planilha_google_id, tab_name, year, month, obra.nome)

        # Fetch active colaboradores for this Obra
        from app.repositories.colaborador import colaborador_repository
        active_colaboradores = colaborador_repository.get_multi(db, limit=1000, obra_id=obra_id, status="ATIVO")
        db_colabs_by_mat = {c.matricula.strip().lstrip("0"): c for c in active_colaboradores}
        matched_db_mats = set()

        # 5. Perform lightweight pre-validation using Sheets values
        # Load sheets values to check employee existence locally before sync
        preview_rows = []
        try:
            range_name = f"'{tab_name}'!A1:AZ200"
            sheet_rows = google_sheets_service.read_sheet_values(planilha.planilha_google_id, range_name)
        except Exception as e:
            sheet_rows = None

        if sheet_rows and len(sheet_rows) > 1:
            headers = [str(cell).strip() for cell in sheet_rows[0]]
            
            # Check if date column exists
            date_parts = final_date.split("-")
            dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else final_date
            dd_mm = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else final_date

            date_col_exists = any(h == final_date or h == dd_mm_yyyy or h == dd_mm for h in headers)
            
            # Index of employees
            sheet_employees_matricula = set()
            sheet_employees_name = []
            
            for r in sheet_rows[1:]:
                if not r:
                    continue
                mat = str(r[0]).strip().lstrip("0")
                if mat:
                    sheet_employees_matricula.add(mat)
                
                name_cell = str(r[1]).strip() if len(r) > 1 else str(r[0]).strip()
                if name_cell:
                    sheet_employees_name.append(name_cell.lower())

            # 1. Process parsed employees (Present/Alimentou)
            for emp in parsed.funcionarios:
                clean_mat = emp.matricula.strip().lstrip("0")
                
                # Check matching db colaborador
                db_colab = db_colabs_by_mat.get(clean_mat)
                if db_colab:
                    matched_db_mats.add(clean_mat)
                    existe_na_base = True
                else:
                    # try matching by name
                    existe_na_base = False
                    for c_mat, c_obj in db_colabs_by_mat.items():
                        if emp.nome.lower() == c_obj.nome.lower():
                            db_colab = c_obj
                            matched_db_mats.add(c_mat)
                            existe_na_base = True
                            break

                # Check match criteria in Sheet
                mat_match = clean_mat in sheet_employees_matricula
                name_match = any(emp.nome.lower() in n or n in emp.nome.lower() for n in sheet_employees_name)
                
                found = mat_match or name_match
                
                situation = "Pronto para importação"
                if not found:
                    situation = "Funcionário não encontrado na planilha"
                elif not date_col_exists:
                    situation = f"Coluna de data {dd_mm_yyyy} não encontrada na planilha"

                preview_rows.append({
                    "matricula": emp.matricula,
                    "nome": emp.nome,
                    "horarios": emp.horarios,
                    "encontrado": found,
                    "existe_na_base": existe_na_base,
                    "situacao": situation,
                    "presenca": "A"  # Alimentação
                })

            # 2. Process active db colaboradores not in file (Absent / Falta)
            for c_mat, colab in db_colabs_by_mat.items():
                if c_mat not in matched_db_mats:
                    mat_match = c_mat in sheet_employees_matricula
                    name_match = any(colab.nome.lower() in n or n in colab.nome.lower() for n in sheet_employees_name)
                    found = mat_match or name_match
                    
                    situation = "Falta (Não encontrado no arquivo)"
                    if not found:
                        situation = "Falta (Não encontrado no arquivo e nem na planilha)"
                    elif not date_col_exists:
                        situation = f"Falta - Coluna de data {dd_mm_yyyy} não encontrada na planilha"

                    preview_rows.append({
                        "matricula": colab.matricula,
                        "nome": colab.nome,
                        "horarios": [],
                        "encontrado": found,
                        "existe_na_base": True,
                        "situacao": situation,
                        "presenca": "F"  # Falta
                    })
        else:
            # Fallback when Sheets connection fails/mocked
            for emp in parsed.funcionarios:
                clean_mat = emp.matricula.strip().lstrip("0")
                existe_na_base = False
                if clean_mat in db_colabs_by_mat:
                    matched_db_mats.add(clean_mat)
                    existe_na_base = True
                else:
                    for c_mat, c_obj in db_colabs_by_mat.items():
                        if emp.nome.lower() == c_obj.nome.lower():
                            matched_db_mats.add(c_mat)
                            existe_na_base = True
                            break

                preview_rows.append({
                    "matricula": emp.matricula,
                    "nome": emp.nome,
                    "horarios": emp.horarios,
                    "encontrado": True,
                    "existe_na_base": existe_na_base,
                    "situacao": "Pronto para importação (Planilha não pôde ser pré-validada)",
                    "presenca": "A"
                })

            for c_mat, colab in db_colabs_by_mat.items():
                if c_mat not in matched_db_mats:
                    preview_rows.append({
                        "matricula": colab.matricula,
                        "nome": colab.nome,
                        "horarios": [],
                        "encontrado": True,
                        "existe_na_base": True,
                        "situacao": "Falta (Não encontrado no arquivo - Planilha não pôde ser pré-validada)",
                        "presenca": "F"
                    })

        return {
            "obra_id": obra.id,
            "obra_nome": obra.nome,
            "planilha_id": planilha.id,
            "planilha_nome": planilha.nome,
            "data": final_date,
            "planilha_google_id": planilha.planilha_google_id,
            "nome_aba": tab_name,
            "aba_criada": tab_criada,
            "funcionarios": preview_rows
        }

    def commit_sync(
        self,
        db: Session,
        user: User,
        ip_address: str,
        user_agent: str,
        obra_id: int,
        planilha_id: int,
        date_str: str,
        filename: str,
        funcionarios_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # 1. Fetch Obra
        obra = obra_repository.get(db, obra_id)
        if not obra or obra.status != "ATIVO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Obra não encontrada ou inativa."
            )

        # 2. Fetch Planilha
        planilha = planilha_repository.get(db, planilha_id)
        if not planilha or planilha.status != "ATIVO":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Planilha de destino não encontrada ou inativa."
            )

        start_time = time.time()
        
        updated_count = 0
        ignored_count = 0
        pending_count = 0
        total_employees = len(funcionarios_data)

        # Create Upload Record
        db_upload = upload_repository.create(db, {
            "user_id": user.id,
            "obra_id": obra.id,
            "planilha_id": planilha.id,
            "filename": filename,
            "total_employees": total_employees,
            "updated_count": 0,
            "ignored_count": 0,
            "pending_count": 0,
            "processing_time_ms": 0.0
        })

        pending_records_to_create = []

        # Normalize date_str
        date_str = sanitize_date_str(date_str)

        # Determine dynamic tab name based on date_str
        tab_name, year, month = get_dynamic_tab_name(date_str, planilha.nome_aba)

        _, tab_criada = google_sheets_service.ensure_tab_exists(planilha.planilha_google_id, tab_name, year, month, obra.nome)
        # 4. Synchronize in batch via Sheets Service (1 Read + 1 Write API call)
        batch_results = google_sheets_service.batch_sync_presence(
            spreadsheet_id=planilha.planilha_google_id,
            tab_name=tab_name,
            date_str=date_str,
            employees=funcionarios_data
        )

        # 5. Process results and tally statistics
        emp_map = {e.get("matricula", ""): e for e in funcionarios_data}

        for mat, status_result, details in batch_results:
            emp = emp_map.get(mat, {})
            nome = emp.get("nome", "Desconhecido")
            horarios = emp.get("horarios", [])

            if status_result == "ATUALIZADO":
                updated_count += 1
            elif status_result == "IGNORADO":
                ignored_count += 1
            else:  # PENDENTE / ERRO
                pending_count += 1
                pending_records_to_create.append({
                    "upload_id": db_upload.id,
                    "employee_id": str(mat)[:50] if mat else None,
                    "employee_name": str(nome)[:255] if nome else "Desconhecido",
                    "date": str(date_str)[:50],
                    "times": " ".join(horarios)[:255] if horarios else "",
                    "status": "PENDENTE",
                    "reason": str(details)[:255] if details else None
                })

        # Insert pending records if any
        for pending_data in pending_records_to_create:
            pending_record_repository.create(db, pending_data)

        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        # Update Upload statistics
        upload_repository.update(db, db_upload, {
            "updated_count": updated_count,
            "ignored_count": ignored_count,
            "pending_count": pending_count,
            "processing_time_ms": processing_time_ms
        })

        # Log Audit Trail
        audit_description = (
            f"Processamento de planilha de alimentação da obra '{obra.nome}'. "
            f"Total: {total_employees}, Importados: {updated_count}, "
            f"Ignorados: {ignored_count}, Pendentes: {pending_count}."
        )
        audit_repository.log(
            db=db,
            user_id=user.id,
            user_name=user.full_name,
            user_email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            module="Alimentacao",
            screen="Alimentacao",
            action="IMPORT",
            description=audit_description,
            object_changed="uploads",
            object_id=str(db_upload.id),
            result="SUCESSO" if pending_count == 0 else "SUCESSO_COM_PENDENCIAS"
        )

        return {
            "upload_id": db_upload.id,
            "total_employees": total_employees,
            "updated": updated_count,
            "ignored": ignored_count,
            "pending": pending_count,
            "processing_time_ms": processing_time_ms,
            "aba_criada": tab_criada,
            "nome_aba": tab_name
        }

upload_service = UploadService()
