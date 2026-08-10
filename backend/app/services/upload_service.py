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

        # 4. Determine Date & list of dates to process
        if override_date:
            dates_list = [sanitize_date_str(override_date)]
        else:
            dates_list = parsed.datas_detectadas or [sanitize_date_str(parsed.data)]

        # Fetch active colaboradores for this Obra
        from app.repositories.colaborador import colaborador_repository
        active_colaboradores = colaborador_repository.get_multi(db, limit=1000, obra_id=obra_id, status="ATIVO")
        db_colabs_by_mat = {c.matricula.strip().lstrip("0"): c for c in active_colaboradores}

        # 5. Perform lightweight pre-validation using Sheets values
        preview_rows = []
        sheets_data_by_tab = {}
        
        from app.repositories.atestado import atestado_repository

        for d in dates_list:
            # Determine dynamic tab name based on date d
            tab_name, year, month = get_dynamic_tab_name(d, planilha.nome_aba)
            
            # Ensure the sheet tab exists in Google Sheets
            _, tab_criada = google_sheets_service.ensure_tab_exists(planilha.planilha_google_id, tab_name, year, month, obra.nome)
            
            if tab_name not in sheets_data_by_tab:
                try:
                    range_name = f"'{tab_name}'!A1:AZ200"
                    sheet_rows = google_sheets_service.read_sheet_values(planilha.planilha_google_id, range_name)
                except Exception:
                    sheet_rows = None
                sheets_data_by_tab[tab_name] = sheet_rows
            else:
                sheet_rows = sheets_data_by_tab[tab_name]

            # Query active atestados for target date d
            try:
                target_dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
                active_atestados = atestado_repository.get_active_atestados_for_date(db, target_dt, obra_id=obra_id)
                atestado_colab_ids = {a.colaborador_id for a in active_atestados}
            except Exception:
                atestado_colab_ids = set()

            # Separate matching data structures for sheet
            sheet_employees_matricula = set()
            sheet_employees_name = []
            sheet_employees_list = []
            date_col_exists = False

            if sheet_rows and len(sheet_rows) > 1:
                headers = [str(cell).strip() for cell in sheet_rows[0]]
                date_parts = d.split("-")
                dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else d
                dd_mm = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else d
                date_col_exists = any(h == d or h == dd_mm_yyyy or h == dd_mm for h in headers)
                
                for r in sheet_rows[1:]:
                    if not r:
                        continue
                    mat_raw = str(r[0]).strip()
                    nome_raw = str(r[1]).strip() if len(r) > 1 else ""
                    if any("terceirizadas" in str(cell).lower() for cell in r[:2]):
                        break
                    if mat_raw or nome_raw:
                        if mat_raw.lower() in ("matricula", "matrícula", "nome", "funcionário", "funcionario"):
                            continue
                        clean_m = mat_raw.lstrip("0")
                        if clean_m:
                            sheet_employees_matricula.add(clean_m)
                        if nome_raw:
                            sheet_employees_name.append(nome_raw.lower())
                        sheet_employees_list.append({"raw_mat": mat_raw, "clean_mat": clean_m, "nome": nome_raw})

            # Filter parsed employees who belong to this date
            if override_date:
                parsed_for_date = parsed.funcionarios
            else:
                parsed_for_date = [emp for emp in parsed.funcionarios if emp.data == d]

            matched_db_mats = set()

            # 1. Process parsed employees (Present/Alimentou) for this date
            for emp in parsed_for_date:
                clean_mat = emp.matricula.strip().lstrip("0")
                db_colab = db_colabs_by_mat.get(clean_mat)
                if db_colab:
                    matched_db_mats.add(clean_mat)
                    existe_na_base = True
                else:
                    existe_na_base = False
                    for c_mat, c_obj in db_colabs_by_mat.items():
                        if emp.nome.lower() == c_obj.nome.lower():
                            db_colab = c_obj
                            matched_db_mats.add(c_mat)
                            existe_na_base = True
                            break

                found = (clean_mat in sheet_employees_matricula) or any(emp.nome.lower() in n or n in emp.nome.lower() for n in sheet_employees_name) if sheet_rows else True
                
                situation = "Pronto para importação"
                if sheet_rows:
                    if not found:
                        situation = "Funcionário não encontrado na planilha"
                    elif not date_col_exists:
                        date_parts = d.split("-")
                        dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else d
                        situation = f"Coluna de data {dd_mm_yyyy} não encontrada na planilha"

                preview_rows.append({
                    "matricula": emp.matricula,
                    "nome": emp.nome,
                    "horarios": emp.horarios,
                    "encontrado": found,
                    "existe_na_base": existe_na_base,
                    "situacao": situation,
                    "presenca": "A",
                    "date": d,
                    "data": d
                })

            # 2. Process active db colaboradores not in file for this date (Absent / Falta / Atestado)
            for c_mat, colab in db_colabs_by_mat.items():
                if c_mat not in matched_db_mats:
                    found = (c_mat in sheet_employees_matricula) or any(colab.nome.lower() in n or n in colab.nome.lower() for n in sheet_employees_name) if sheet_rows else True
                    is_atestado = colab.id in atestado_colab_ids
                    presenca_mark = "J" if is_atestado else "F"
                    
                    if is_atestado:
                        situation = "Atestado Médico Vigente (Justificado)"
                    else:
                        situation = "Falta (Não encontrado no arquivo)"
                        if sheet_rows:
                            if not found:
                                situation = "Falta (Não encontrado no arquivo e nem na planilha)"
                            elif not date_col_exists:
                                date_parts = d.split("-")
                                dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else d
                                situation = f"Falta - Coluna de data {dd_mm_yyyy} não encontrada na planilha"

                    preview_rows.append({
                        "matricula": colab.matricula,
                        "nome": colab.nome,
                        "horarios": [],
                        "encontrado": found,
                        "existe_na_base": True,
                        "situacao": situation,
                        "presenca": presenca_mark,
                        "date": d,
                        "data": d
                    })

            # 3. Process sheet employees who are in this tab but not in file or DB for this date
            if sheet_rows:
                processed_mats = {p["matricula"].strip().lstrip("0") for p in preview_rows if p.get("date") == d and p.get("matricula")}
                processed_names = {p["nome"].strip().lower() for p in preview_rows if p.get("date") == d and p.get("nome")}
                
                for s_emp in sheet_employees_list:
                    cm = s_emp["clean_mat"]
                    nm = s_emp["nome"].strip().lower()
                    if (cm and cm not in processed_mats) and (nm not in processed_names):
                        db_colab = db_colabs_by_mat.get(cm)
                        if not db_colab and nm:
                            for c_obj in db_colabs_by_mat.values():
                                if c_obj.nome.strip().lower() == nm:
                                    db_colab = c_obj
                                    break
                                    
                        is_atestado = db_colab.id in atestado_colab_ids if db_colab else False
                        presenca_mark = "J" if is_atestado else "F"
                        
                        situation = "Atestado Médico Vigente (Justificado)" if is_atestado else "Falta (Registrado na planilha, ausente no arquivo)"
                        
                        preview_rows.append({
                            "matricula": s_emp["raw_mat"],
                            "nome": s_emp["nome"],
                            "horarios": [],
                            "encontrado": True,
                            "existe_na_base": True if db_colab else False,
                            "situacao": situation,
                            "presenca": presenca_mark,
                            "date": d,
                            "data": d
                        })

        tab_name_last = None
        tab_criada_last = False
        if dates_list:
            last_date = dates_list[-1]
            tab_name_last, year, month = get_dynamic_tab_name(last_date, planilha.nome_aba)
            
        return {
            "obra_id": obra.id,
            "obra_nome": obra.nome,
            "planilha_id": planilha.id,
            "planilha_nome": planilha.nome,
            "data": dates_list[0] if dates_list else final_date,
            "datas_detectadas": dates_list,
            "planilha_google_id": planilha.planilha_google_id,
            "nome_aba": tab_name_last,
            "aba_criada": tab_criada,
            "funcionarios": preview_rows,
            "linhas_preview": preview_rows
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

        # Normalize main date_str (used as fallback for employees without individual date)
        date_str = sanitize_date_str(date_str)

        # Group employees by sheet tab name
        from collections import defaultdict
        groups_by_tab: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        tab_dates_map = defaultdict(set)
        
        for emp in funcionarios_data:
            emp_date = sanitize_date_str(emp.get("date") or emp.get("data") or date_str)
            tab_name, year, month = get_dynamic_tab_name(emp_date, planilha.nome_aba)
            groups_by_tab[tab_name].append(emp)
            tab_dates_map[tab_name].add(emp_date)

        aba_criada = False
        tab_name_last = None

        for tab_name, tab_emps in groups_by_tab.items():
            tab_name_last = tab_name
            
            # Determine month/year from first date in group to check/ensure tab exists
            dates_in_tab = sorted(list(tab_dates_map[tab_name]))
            first_date = dates_in_tab[0] if dates_in_tab else date_str
            date_parts = first_date.split("-")
            year = int(date_parts[0]) if len(date_parts) == 3 else 2026
            month = int(date_parts[1]) if len(date_parts) == 3 else 7

            _, _tab_criada = google_sheets_service.ensure_tab_exists(
                planilha.planilha_google_id, tab_name, year, month, obra.nome
            )
            if _tab_criada:
                aba_criada = True

            # Synchronize in batch via Sheets Service (1 Read + 1 Write API call per tab group)
            batch_results = google_sheets_service.batch_sync_presence(
                spreadsheet_id=planilha.planilha_google_id,
                tab_name=tab_name,
                date_str=first_date,
                employees=tab_emps
            )

            # Process results and tally statistics
            emp_map = {e.get("matricula", ""): e for e in tab_emps}

            for mat, status_result, details in batch_results:
                emp = emp_map.get(mat, {})
                nome = emp.get("nome", "Desconhecido")
                horarios = emp.get("horarios", [])
                emp_individual_date = sanitize_date_str(emp.get("date") or emp.get("data") or first_date)

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
                        "date": str(emp_individual_date)[:50],
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
        all_unique_dates = sorted(list({sanitize_date_str(emp.get("date") or emp.get("data") or date_str) for emp in funcionarios_data}))
        dates_label = ", ".join(all_unique_dates)
        audit_description = (
            f"Processamento de planilha de alimentação da obra '{obra.nome}'. "
            f"Datas: {dates_label}. "
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
            "aba_criada": aba_criada,
            "nome_aba": tab_name_last
        }

upload_service = UploadService()
