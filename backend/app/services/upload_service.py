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

class UploadService:
    """
    Business logic layer for handling presence file uploads, previewing parsed entries,
    and synchronizing presence marks with Google Sheets.
    """

    def __init__(self):
        self.parser = IntelligentParser()

    def _parse_file(self, content: bytes, filename: str, content_type: str) -> ParsedData:
        filename_lower = filename.lower()
        try:
            if filename_lower.endswith(".txt"):
                text_content = content.decode("utf-8", errors="ignore")
                return self.parser.parse_txt(text_content)
            elif filename_lower.endswith(".csv"):
                text_content = content.decode("utf-8", errors="ignore")
                return self.parser.parse_csv(text_content)
            elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls") or "spreadsheet" in content_type:
                return self.parser.parse_xlsx(content)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de arquivo não suportado. Envie TXT, CSV ou XLSX."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro ao processar o arquivo: {str(e)}"
            )

    def preview_upload(
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
        final_date = override_date or parsed.data
        if not final_date:
            # Fallback to today's date formatted as YYYY-MM-DD
            final_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        # 5. Perform lightweight pre-validation using Sheets values
        # Load sheets values to check employee existence locally before sync
        preview_rows = []
        try:
            range_name = f"'{planilha.nome_aba}'!A1:AZ200"
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

            for emp in parsed.funcionarios:
                clean_mat = emp.matricula.strip().lstrip("0")
                
                # Check match criteria
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
                    "situacao": situation
                })
        else:
            # Fallback when Sheets connection fails/mocked
            for emp in parsed.funcionarios:
                preview_rows.append({
                    "matricula": emp.matricula,
                    "nome": emp.nome,
                    "horarios": emp.horarios,
                    "encontrado": True,
                    "situacao": "Pronto para importação (Planilha não pôde ser pré-validada)"
                })

        return {
            "obra_id": obra.id,
            "obra_nome": obra.nome,
            "planilha_id": planilha.id,
            "planilha_nome": planilha.nome,
            "data": final_date,
            "planilha_google_id": planilha.planilha_google_id,
            "nome_aba": planilha.nome_aba,
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

        # 3. Iterate and sync via Sheets Service
        for emp in funcionarios_data:
            matricula = emp.get("matricula", "")
            nome = emp.get("nome", "")
            horarios = emp.get("horarios", [])
            
            status_result, details = google_sheets_service.sync_presence(
                spreadsheet_id=planilha.planilha_google_id,
                tab_name=planilha.nome_aba,
                date_str=date_str,
                matricula=matricula,
                employee_name=nome
            )

            if status_result == "ATUALIZADO":
                updated_count += 1
            elif status_result == "IGNORADO":
                ignored_count += 1
            else:  # PENDENTE / ERRO
                pending_count += 1
                # Save details of pending synchronization to Database
                pending_records_to_create.append({
                    "upload_id": db_upload.id,
                    "employee_id": matricula,
                    "employee_name": nome,
                    "date": date_str,
                    "times": " ".join(horarios),
                    "status": "PENDENTE",
                    "reason": details
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
            "processing_time_ms": processing_time_ms
        }

upload_service = UploadService()
