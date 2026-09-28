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
        
        year = int(date_parts[0])
        month = int(date_parts[1])
    else:
        year = 2026
        month = 7
        
    m_name = get_portuguese_month_name(month)
    y_short = str(year)[-2:]
    
    tab_name = f"{m_name} {y_short}"
    return tab_name, year, month

def sanitize_date_str(date_input: Any) -> str:
    if not date_input:
        return ""
    if isinstance(date_input, (datetime.date, datetime.datetime)):
        return date_input.strftime("%Y-%m-%d")
    d_str = str(date_input).strip()
    if "/" in d_str:
        parts = d_str.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str

class UploadService:
    def __init__(self):
        self.parser = IntelligentParser()

    def _parse_file(self, content: bytes, filename: str, content_type: str) -> ParsedData:
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

    def process_pdf_mirror(self, pdf_bytes: bytes, valor_diario_vt: float, db: Session) -> tuple[bytes, int, str]:
        import pypdf
        import io
        import re
        import datetime
        from collections import Counter
        
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        # Debugging: write extracted text to a log file
        try:
            with open("logs/extracted_pdf_text.txt", "w", encoding="utf-8") as f_debug:
                for p_idx in range(len(reader.pages)):
                    p_text = reader.pages[p_idx].extract_text()
                    f_debug.write(f"--- PAGE {p_idx + 1} ---\n")
                    f_debug.write(p_text or "[No text extracted]\n")
                    f_debug.write("\n")
        except Exception as e_debug:
            print(f"Error writing debug PDF text: {str(e_debug)}")

        collaborators_data = []
        
        # Robust day lines pattern matching day/date and weekday, even if squished with previous word/time
        day_weekday_pattern = re.compile(
            r"(\d{1,2})(?:/\d{2}(?:/\d{2,4})?)?\s*(?:-\s*|/\s*|\s+)\(?(Seg|Ter|Qua|Qui|Sex|Sáb|Sab|Dom|Segunda|Terça|Terca|Quarta|Quinta|Sexta|Sábado|Sabado|Domingo)\b",
            re.IGNORECASE
        )
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
                
            # Parse page text
            # 1. Period
            period_match = re.search(r"Espelho\s+de\s+Ponto\s+de\s+(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"Espelho\s+de\s+Ponto\s+de\s+(\d{2}/\d{2}/\d{4})\s+ate\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+ate\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
                
            start_date_str = period_match.group(1) if period_match else None
            end_date_str = period_match.group(2) if period_match else None
            
            # 2. Collaborator Name and Matricula (Structured Layout Parser)
            matricula = None
            nome = None
            local_trab = None
            
            lines_clean = [l.strip() for l in text.split('\n') if l.strip()]
            colab_idx = -1
            for idx, line in enumerate(lines_clean):
                if "Dados do Colaborador" in line:
                    colab_idx = idx
                    break
                    
            if colab_idx != -1:
                val_line = None
                for i in range(colab_idx + 1, min(colab_idx + 8, len(lines_clean))):
                    # Match pattern of "<alphanumeric matricula> - <name>"
                    if re.match(r"^[A-Z0-9]+?\s*-\s*[A-Za-zÀ-ÿ\s\.\-\(\)]+$", lines_clean[i], re.IGNORECASE):
                        val_line = lines_clean[i]
                        if i + 1 < len(lines_clean):
                            local_trab = lines_clean[i+1]
                        break
                
                if val_line:
                    match_val = re.match(r"^([A-Z0-9]+?)\s*-\s*(.+)$", val_line)
                    if match_val:
                        matricula = match_val.group(1).strip()
                        nome = match_val.group(2).strip()
            
            # Fallback regexes if not found by structural parser
            if not nome:
                combined_match = re.search(
                    r"(?:Nome|Colaborador|Funcionario|Funcionário|Empregado|Trabalhador)\s*:?\s*([A-Z0-9]+)\s*-\s*([^\n\r]+)",
                    text, re.IGNORECASE
                )
                if combined_match:
                    matricula = combined_match.group(1).strip()
                    nome_raw = combined_match.group(2).strip()
                    nome_cleaned = re.split(
                        r"\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)",
                        nome_raw, flags=re.IGNORECASE
                    )[0]
                    nome = nome_cleaned.strip()
                else:
                    name_match = re.search(
                        r"(?:Nome|Colaborador|Funcionario|Funcionário|Empregado|Trabalhador|Nome\s+do\s+Trabalhador)\s*:?\s*([^\n\r\t]+?)(?:\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)|\r|\n|$)",
                        text, re.IGNORECASE
                    )
                    if name_match:
                        nome = name_match.group(1).strip()
                    
                    mat_match = re.search(
                        r"(?:Matrícula|Matricula|Cadastro|Registro|Chapa|Cód\.?\s+Folha|Código|Codigo)\s*:?\s*([A-Z0-9]+)",
                        text, re.IGNORECASE
                    )
                    if mat_match:
                        matricula = mat_match.group(1).strip()
            
            # Final Fallbacks
            if not nome:
                nome = f"Colaborador {page_num + 1}"
            if not matricula:
                matricula = "Desconhecido"
                
            # 3. Local Trab
            if not local_trab or local_trab == "Desconhecido":
                local_match = re.search(
                    r"(?:Local\s+Trab|Centro\s+de\s+Custo|CC|Departamento|Setor|Seção|Secao)\s*:?\s*([^\n\r\t]+?)(?:\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)|\r|\n|$)",
                    text, re.IGNORECASE
                )
                local_trab = local_match.group(1).strip() if local_match else "Desconhecido"
            
            # 4. Day lines matching
            lines = text.split('\n')
            day_lines = []
            for line in lines:
                if day_weekday_pattern.search(line):
                    day_lines.append(line.strip())
                    
            # 5. Extract all Jornada times to identify the scheduled shift
            jornada_times_list = []
            for line in day_lines:
                jornada_match = re.search(r"\b(?:Jornada|Horário|Horario|Escala)\s*:?\s*(.*)$", line, re.IGNORECASE)
                if jornada_match:
                    jornada_part = jornada_match.group(1)
                    # Use \b\d{2}:\d{2} to find times even if squished with day number at the end
                    times = re.findall(r"\b\d{2}:\d{2}", jornada_part)
                    if times:
                        jornada_times_list.append(times)
                        
            # Longest common prefix of jornada_times_list
            scheduled_shift = []
            if jornada_times_list:
                min_len = min(len(lst) for lst in jornada_times_list)
                for i in range(min_len):
                    val = jornada_times_list[0][i]
                    if all(len(lst) > i and lst[i] == val for lst in jornada_times_list):
                        scheduled_shift.append(val)
                    else:
                        break
                        
            # 6. Parse presences for each day number
            presences = {}
            for line in day_lines:
                match = day_weekday_pattern.search(line)
                if not match:
                    continue
                day_num = int(match.group(1))
                
                # Find all timestamps on this line (without trailing word boundary \b to support squished strings like 17:0922)
                all_times = re.findall(r"\b\d{2}:\d{2}", line)
                
                # Check for Jornada part
                jornada_match = re.search(r"\b(?:Jornada|Horário|Horario|Escala)\s*:?\s*(.*)$", line, re.IGNORECASE)
                has_jornada_keyword = False
                jornada_part_str = ""
                if jornada_match:
                    has_jornada_keyword = True
                    jornada_part_str = jornada_match.group(1)
                    
                actual_markings = []
                if has_jornada_keyword:
                    times_after_jornada = re.findall(r"\b\d{2}:\d{2}", jornada_part_str)
                    num_scheduled = len(scheduled_shift)
                    if len(times_after_jornada) > num_scheduled:
                        actual_markings = times_after_jornada[num_scheduled:]
                    else:
                        actual_markings = []
                else:
                    actual_markings = all_times
                    
                weekday_str = match.group(2).lower()
                is_weekend = weekday_str in ("sab", "sáb", "sabado", "sábado", "dom", "domingo")
                
                if is_weekend:
                    presence = 1 if len(actual_markings) > 0 else 0
                else:
                    # Monday to Friday
                    line_lower = line.lower()
                    has_falta = "falta" in line_lower
                    has_exame = "exame periodico" in line_lower or "exame periódico" in line_lower
                    
                    presence = 0 if (has_falta and not has_exame) else 1
                    
                presences[day_num] = presence
                
            if presences or (nome and matricula and matricula != "Desconhecido"):
                collaborators_data.append({
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "matricula": matricula,
                    "nome": nome,
                    "local_trab": local_trab,
                    "presences": presences
                })
            
        if not collaborators_data:
            raise ValueError("Nenhum dado de colaborador pôde ser extraído do PDF.")
            
        # Sort collaborators alphabetically by name
        collaborators_data.sort(key=lambda x: x["nome"].lower())
            
        # Find most common period
        periods = [(c["start_date"], c["end_date"]) for c in collaborators_data if c["start_date"] and c["end_date"]]
        if periods:
            master_start, master_end = Counter(periods).most_common(1)[0][0]
        else:
            raise ValueError("Não foi possível detectar o período do espelho de ponto no PDF.")
            
        # Generate all dates in range
        start_date = datetime.datetime.strptime(master_start, "%d/%m/%Y").date()
        end_date = datetime.datetime.strptime(master_end, "%d/%m/%Y").date()
        
        dates_list = []
        curr = start_date
        while curr <= end_date:
            dates_list.append(curr)
            curr += datetime.timedelta(days=1)
            
        # Generate Styled Excel Spreadsheet
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Relatorio VT"
        
        ws.views.sheetView[0].showGridLines = True
        
        font_family = "Segoe UI"
        title_font = Font(name=font_family, size=16, bold=True, color="1B365D")
        subtitle_font = Font(name=font_family, size=10, italic=True, color="555555")
        header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
        data_font = Font(name=font_family, size=10)
        bold_data_font = Font(name=font_family, size=10, bold=True)
        
        header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
        zebra_fill = PatternFill(start_color="F2F4F8", end_color="F2F4F8", fill_type="solid")
        white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        summary_fill = PatternFill(start_color="E9EEF4", end_color="E9EEF4", fill_type="solid")
        
        presence_1_fill = PatternFill(start_color="E6F4EA", end_color="E6F4EA", fill_type="solid")
        presence_1_font = Font(name=font_family, size=10, color="137333", bold=True)
        
        presence_0_fill = PatternFill(start_color="FCE8E6", end_color="FCE8E6", fill_type="solid")
        presence_0_font = Font(name=font_family, size=10, color="C5221F")
        
        thin_border_side = Side(border_style="thin", color="D9D9D9")
        thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
        
        # Title Block
        ws.merge_cells("A1:G1")
        ws["A1"] = "RELATÓRIO DE VALE TRANSPORTE E PRESENÇAS"
        ws["A1"].font = title_font
        
        ws.merge_cells("A2:G2")
        ws["A2"] = f"Período correspondente: {master_start} até {master_end}"
        ws["A2"].font = subtitle_font
        
        # Headers Setup
        headers = ["Matrícula", "Nome do Colaborador", "Centro de Custo"]
        for d in dates_list:
            headers.append(d.strftime("%d/%m"))
        headers += ["Dias Trabalhados", "Valor Diário VT", "Total VT"]
        
        header_row = 4
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx)
            cell.value = h
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            
        ws.row_dimensions[header_row].height = 28
        
        # Data Rows
        start_data_row = 5
        for row_idx, colab in enumerate(collaborators_data, start=start_data_row):
            row_fill = zebra_fill if row_idx % 2 == 0 else white_fill
            
            # Col A: Matricula
            cell_mat = ws.cell(row=row_idx, column=1, value=colab["matricula"])
            cell_mat.font = data_font
            cell_mat.fill = row_fill
            cell_mat.border = thin_border
            cell_mat.alignment = Alignment(horizontal="center")
            
            # Col B: Nome
            cell_nome = ws.cell(row=row_idx, column=2, value=colab["nome"])
            cell_nome.font = data_font
            cell_nome.fill = row_fill
            cell_nome.border = thin_border
            cell_nome.alignment = Alignment(horizontal="left")
            
            # Col C: Centro de Custo
            cell_cc = ws.cell(row=row_idx, column=3, value=colab["local_trab"])
            cell_cc.font = data_font
            cell_cc.fill = row_fill
            cell_cc.border = thin_border
            cell_cc.alignment = Alignment(horizontal="left")
            
            # Presence columns
            num_date_cols = len(dates_list)
            presences_dict = colab.get("presences", {})
            
            for date_idx, d in enumerate(dates_list):
                day_num = d.day
                presence_val = presences_dict.get(day_num, 0)
                col_pos = 4 + date_idx
                
                cell_pres = ws.cell(row=row_idx, column=col_pos, value=presence_val)
                cell_pres.border = thin_border
                cell_pres.alignment = Alignment(horizontal="center")
                
                if presence_val == 1:
                    cell_pres.fill = presence_1_fill
                    cell_pres.font = presence_1_font
                else:
                    cell_pres.fill = presence_0_fill
                    cell_pres.font = presence_0_font
                    
            # Dias Trabalhados formula: =SUM(D{row}:[LastDateCol]{row})
            first_date_col = get_column_letter(4)
            last_date_col = get_column_letter(3 + num_date_cols)
            col_dias = 4 + num_date_cols
            
            cell_dias = ws.cell(row=row_idx, column=col_dias)
            cell_dias.value = f"=SUM({first_date_col}{row_idx}:{last_date_col}{row_idx})"
            cell_dias.font = bold_data_font
            cell_dias.fill = summary_fill
            cell_dias.border = thin_border
            cell_dias.alignment = Alignment(horizontal="center")
            
            # Valor Diário VT
            col_val_vt = col_dias + 1
            cell_val_vt = ws.cell(row=row_idx, column=col_val_vt, value=valor_diario_vt)
            cell_val_vt.font = data_font
            cell_val_vt.fill = row_fill
            cell_val_vt.border = thin_border
            cell_val_vt.number_format = '"R$ "#,##0.00'
            cell_val_vt.alignment = Alignment(horizontal="right")
            
            # Total VT formula
            col_total = col_val_vt + 1
            cell_total = ws.cell(row=row_idx, column=col_total)
            dias_letter = get_column_letter(col_dias)
            val_vt_letter = get_column_letter(col_val_vt)
            cell_total.value = f"={dias_letter}{row_idx}*{val_vt_letter}{row_idx}"
            cell_total.font = bold_data_font
            cell_total.fill = summary_fill
            cell_total.border = thin_border
            cell_total.number_format = '"R$ "#,##0.00'
            cell_total.alignment = Alignment(horizontal="right")
            
            ws.row_dimensions[row_idx].height = 20
            
        # Summary Row at the bottom
        last_row = start_data_row + len(collaborators_data) - 1
        total_row_idx = last_row + 2
        
        cell_total_label = ws.cell(row=total_row_idx, column=3, value="Total Geral")
        cell_total_label.font = Font(name=font_family, size=11, bold=True, color="1B365D")
        cell_total_label.alignment = Alignment(horizontal="right")
        
        # SUM of Dias Trabalhados
        col_dias = 4 + len(dates_list)
        dias_letter = get_column_letter(col_dias)
        cell_total_dias = ws.cell(row=total_row_idx, column=col_dias)
        cell_total_dias.value = f"=SUM({dias_letter}5:{dias_letter}{last_row})"
        cell_total_dias.font = Font(name=font_family, size=11, bold=True)
        cell_total_dias.border = Border(top=Side(style="double", color="1B365D"))
        cell_total_dias.alignment = Alignment(horizontal="center")
        
        # SUM of Total VT
        col_total = col_dias + 2
        total_letter = get_column_letter(col_total)
        cell_total_val = ws.cell(row=total_row_idx, column=col_total)
        cell_total_val.value = f"=SUM({total_letter}5:{total_letter}{last_row})"
        cell_total_val.font = Font(name=font_family, size=11, bold=True)
        cell_total_val.border = Border(top=Side(style="double", color="1B365D"))
        cell_total_val.number_format = '"R$ "#,##0.00'
        cell_total_val.alignment = Alignment(horizontal="right")
        
        # Auto-fit columns
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                if cell.row in (1, 2, total_row_idx):
                    continue
                if cell.value is not None:
                    val_str = str(cell.value)
                    if val_str.startswith("="):
                        max_len = max(max_len, 10)
                    else:
                        max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 10)
            
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 25
        
        # Save to bytes
        excel_buf = io.BytesIO()
        wb.save(excel_buf)
        excel_buf.seek(0)
        return excel_buf.getvalue()

    def process_pdf_alimentation(
        self,
        pdf_bytes: bytes,
        tipo_refeicao: str,
        db: Session,
        obra_id: Optional[int] = None,
        planilha_id: Optional[int] = None
    ) -> tuple[bytes, int, int, str, str]:
        import pypdf
        import io
        import re
        import datetime
        from collections import Counter
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        
        from app.repositories.obra import obra_repository
        from app.repositories.planilha import planilha_repository
        from app.repositories.colaborador import colaborador_repository
        from app.models.obra import Obra
        from app.models.planilha import Planilha
        
        # 1. Parse PDF Mirror point markings
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        collaborators_data = []
        
        day_weekday_pattern = re.compile(
            r"(\d{1,2})(?:/\d{2}(?:/\d{2,4})?)?\s*(?:-\s*|/\s*|\s+)\(?(Seg|Ter|Qua|Qui|Sex|Sáb|Sab|Dom|Segunda|Terça|Terca|Quarta|Quinta|Sexta|Sábado|Sabado|Domingo)\b",
            re.IGNORECASE
        )
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
                
            # Parse page text for period
            period_match = re.search(r"Espelho\s+de\s+Ponto\s+de\s+(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"Espelho\s+de\s+Ponto\s+de\s+(\d{2}/\d{2}/\d{4})\s+ate\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
            if not period_match:
                period_match = re.search(r"(\d{2}/\d{2}/\d{4})\s+ate\s+(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
                
            start_date_str = period_match.group(1) if period_match else None
            end_date_str = period_match.group(2) if period_match else None
            
            # Collaborator Name and Matricula
            matricula = None
            nome = None
            local_trab = None
            
            lines_clean = [l.strip() for l in text.split('\n') if l.strip()]
            colab_idx = -1
            for idx, line in enumerate(lines_clean):
                if "Dados do Colaborador" in line:
                    colab_idx = idx
                    break
                    
            if colab_idx != -1:
                val_line = None
                for i in range(colab_idx + 1, min(colab_idx + 8, len(lines_clean))):
                    if re.match(r"^[A-Z0-9]+?\s*-\s*[A-Za-zÀ-ÿ\s\.\-\(\)]+$", lines_clean[i], re.IGNORECASE):
                        val_line = lines_clean[i]
                        if i + 1 < len(lines_clean):
                            local_trab = lines_clean[i+1]
                        break
                
                if val_line:
                    match_val = re.match(r"^([A-Z0-9]+?)\s*-\s*(.+)$", val_line)
                    if match_val:
                        matricula = match_val.group(1).strip()
                        nome = match_val.group(2).strip()
            
            if not nome:
                combined_match = re.search(
                    r"(?:Nome|Colaborador|Funcionario|Funcionário|Empregado|Trabalhador)\s*:?\s*([A-Z0-9]+)\s*-\s*([^\n\r]+)",
                    text, re.IGNORECASE
                )
                if combined_match:
                    matricula = combined_match.group(1).strip()
                    nome_raw = combined_match.group(2).strip()
                    nome_cleaned = re.split(
                        r"\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)",
                        nome_raw, flags=re.IGNORECASE
                    )[0]
                    nome = nome_cleaned.strip()
                else:
                    name_match = re.search(
                        r"(?:Nome|Colaborador|Funcionario|Funcionário|Empregado|Trabalhador|Nome\s+do\s+Trabalhador)\s*:?\s*([^\n\r\t]+?)(?:\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)|\r|\n|$)",
                        text, re.IGNORECASE
                    )
                    if name_match:
                        nome = name_match.group(1).strip()
                    
                    mat_match = re.search(
                        r"(?:Matrícula|Matricula|Cadastro|Registro|Chapa|Cód\.?\s+Folha|Código|Codigo)\s*:?\s*([A-Z0-9]+)",
                        text, re.IGNORECASE
                    )
                    if mat_match:
                        matricula = mat_match.group(1).strip()
            
            if not nome:
                nome = f"Colaborador {page_num + 1}"
            if not matricula:
                matricula = "Desconhecido"
                
            if not local_trab or local_trab == "Desconhecido":
                local_match = re.search(
                    r"(?:Local\s+Trab|Centro\s+de\s+Custo|CC|Departamento|Setor|Seção|Secao)\s*:?\s*([^\n\r\t]+?)(?:\s{2,}|\s+(?:Matrícula|Matricula|PIS|CPF|Admissão|Admissao|Cargo|CTPS)|\r|\n|$)",
                    text, re.IGNORECASE
                )
                local_trab = local_match.group(1).strip() if local_match else "Desconhecido"
            
            # Day lines matching
            lines = text.split('\n')
            day_lines = []
            for line in lines:
                if day_weekday_pattern.search(line):
                    day_lines.append(line.strip())
                    
            # Extract Scheduled shift
            jornada_times_list = []
            for line in day_lines:
                jornada_match = re.search(r"\b(?:Jornada|Horário|Horario|Escala)\s*:?\s*(.*)$", line, re.IGNORECASE)
                if jornada_match:
                    jornada_part = jornada_match.group(1)
                    times = re.findall(r"\b\d{2}:\d{2}", jornada_part)
                    if times:
                        jornada_times_list.append(times)
                        
            scheduled_shift = []
            if jornada_times_list:
                min_len = min(len(lst) for lst in jornada_times_list)
                for i in range(min_len):
                    val = jornada_times_list[0][i]
                    if all(len(lst) > i and lst[i] == val for lst in jornada_times_list):
                        scheduled_shift.append(val)
                    else:
                        break
                        
            # Parse markings for each day number
            presences = {}
            for line in day_lines:
                match = day_weekday_pattern.search(line)
                if not match:
                    continue
                day_num = int(match.group(1))
                
                # Find all timestamps on this line
                all_times = re.findall(r"\b\d{2}:\d{2}", line)
                
                # Check for Jornada part
                jornada_match = re.search(r"\b(?:Jornada|Horário|Horario|Escala)\s*:?\s*(.*)$", line, re.IGNORECASE)
                has_jornada_keyword = False
                jornada_part_str = ""
                if jornada_match:
                    has_jornada_keyword = True
                    jornada_part_str = jornada_match.group(1)
                    
                actual_markings = []
                if has_jornada_keyword:
                    times_after_jornada = re.findall(r"\b\d{2}:\d{2}", jornada_part_str)
                    num_scheduled = len(scheduled_shift)
                    if len(times_after_jornada) > num_scheduled:
                        actual_markings = times_after_jornada[num_scheduled:]
                    else:
                        actual_markings = []
                else:
                    actual_markings = all_times
                
                # Calculate Alimentação Presence
                if tipo_refeicao == "almoco":
                    presence_val = 1 if len(actual_markings) > 0 else 0
                else:  # jantar
                    has_marking_after_18 = False
                    for t in actual_markings:
                        try:
                            h, m = map(int, t.split(":"))
                            if h >= 18:
                                has_marking_after_18 = True
                                break
                        except Exception:
                            pass
                    presence_val = 1 if has_marking_after_18 else 0
                
                presences[day_num] = presence_val
                
            if presences or (nome and matricula and matricula != "Desconhecido"):
                collaborators_data.append({
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "matricula": matricula,
                    "nome": nome,
                    "local_trab": local_trab,
                    "presences": presences
                })
                
        if not collaborators_data:
            raise ValueError("Nenhum dado de colaborador pôde ser extraído do PDF.")
            
        collaborators_data.sort(key=lambda x: x["nome"].lower())
        
        # Find period
        periods = [(c["start_date"], c["end_date"]) for c in collaborators_data if c["start_date"] and c["end_date"]]
        if periods:
            master_start, master_end = Counter(periods).most_common(1)[0][0]
        else:
            raise ValueError("Não foi possível detectar o período do espelho de ponto no PDF.")
            
        # Generate dates list
        start_date = datetime.datetime.strptime(master_start, "%d/%m/%Y").date()
        end_date = datetime.datetime.strptime(master_end, "%d/%m/%Y").date()
        
        dates_list = []
        curr = start_date
        while curr <= end_date:
            dates_list.append(curr)
            curr += datetime.timedelta(days=1)
            
        # 2. Fetch or Auto-Detect Obra & Planilha info for report metadata
        if not obra_id or not planilha_id:
            # Query all active Obras
            all_obras = db.query(Obra).filter(Obra.status == "ATIVO").all()
            
            # Determine the most common local_trab
            local_trabs = [c["local_trab"] for c in collaborators_data if c.get("local_trab") and c["local_trab"] != "Desconhecido"]
            
            if not local_trabs:
                raise ValueError("Não foi possível identificar o Local de Trabalho (Obra) no PDF.")
                
            most_common_local = Counter(local_trabs).most_common(1)[0][0]
            
            # Clean string helper
            def normalize_str(s: str) -> str:
                import unicodedata
                if not s:
                    return ""
                s = s.strip().lower()
                # Remove accents
                s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                return s
                
            norm_local = normalize_str(most_common_local)
            
            matched_obra = None
            for o in all_obras:
                norm_obra_name = normalize_str(o.nome)
                norm_obra_code = normalize_str(o.codigo)
                
                # Match if names are equal, or one is substring of the other, or matches code
                if norm_local == norm_obra_name or norm_obra_name in norm_local or norm_local in norm_obra_name:
                    matched_obra = o
                    break
                if norm_obra_code and norm_obra_code in norm_local:
                    matched_obra = o
                    break
                    
            if not matched_obra:
                raise ValueError(f"Não foi possível encontrar uma Obra cadastrada correspondente a '{most_common_local}' no PDF.")
                
            obra = matched_obra
            obra_id = matched_obra.id
            
            # Now find the planilha for this Obra
            planilha = db.query(Planilha).filter(
                Planilha.obra_id == matched_obra.id,
                Planilha.automacao == "ALIMENTACAO",
                Planilha.status == "ATIVO"
            ).first()
            
            if not planilha:
                raise ValueError(f"Não foi encontrada nenhuma Planilha ativa de Alimentação configurada para a Obra '{matched_obra.nome}'.")
                
            planilha_id = planilha.id
        else:
            obra = obra_repository.get(db, obra_id)
            planilha = planilha_repository.get(db, planilha_id)
            
        obra_nome = obra.nome if obra else "Desconhecida"
        planilha_nome = planilha.nome if planilha else "Desconhecida"
        
        # Fetch DB active colaboradores for matching
        active_colabs = colaborador_repository.get_multi(db, limit=1000, obra_id=obra_id, status="ATIVO")
        db_mats = {c.matricula.strip().lstrip("0"): c for c in active_colabs}
        
        # Build list of final output records
        final_list = []
        processed_db_mats = set()
        
        # Add PDF collaborators
        for colab in collaborators_data:
            mat_clean = colab["matricula"].strip().lstrip("0")
            matched_c = db_mats.get(mat_clean)
            
            nome_final = matched_c.nome if matched_c else colab["nome"]
            local_trab_final = colab["local_trab"]
            
            if matched_c:
                processed_db_mats.add(mat_clean)
                
            final_list.append({
                "matricula": colab["matricula"],
                "nome": nome_final,
                "local_trab": local_trab_final,
                "presences": colab["presences"]
            })
            
        # Add active DB colaboradores not in PDF (marked with 0 meals)
        for c_mat, c_obj in db_mats.items():
            if c_mat not in processed_db_mats:
                final_list.append({
                    "matricula": c_obj.matricula,
                    "nome": c_obj.nome,
                    "local_trab": obra_nome,
                    "presences": {}
                })
                
        # Sort again by name
        final_list.sort(key=lambda x: x["nome"].lower())
        
        # Generate Styled Excel Spreadsheet
        wb = Workbook()
        ws = wb.active
        ws.title = f"Alimentacao {tipo_refeicao.capitalize()}"
        ws.views.sheetView[0].showGridLines = True
        
        font_family = "Segoe UI"
        title_font = Font(name=font_family, size=16, bold=True, color="2E7D32") # Green for food
        subtitle_font = Font(name=font_family, size=10, italic=True, color="555555")
        header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
        data_font = Font(name=font_family, size=10)
        bold_data_font = Font(name=font_family, size=10, bold=True)
        
        header_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        zebra_fill = PatternFill(start_color="F1F8E9", end_color="F1F8E9", fill_type="solid") # Soft green zebra tint
        white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        summary_fill = PatternFill(start_color="DCEDC8", end_color="DCEDC8", fill_type="solid")
        
        presence_1_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
        presence_1_font = Font(name=font_family, size=10, color="1B5E20", bold=True)
        
        presence_0_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        presence_0_font = Font(name=font_family, size=10, color="9E9E9E")
        
        thin_border_side = Side(border_style="thin", color="D9D9D9")
        thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
        
        # Title Block
        ws.merge_cells("A1:G1")
        refeicao_title = "ALMOÇO" if tipo_refeicao == "almoco" else "JANTAR"
        ws["A1"] = f"CONTROLE DE ALIMENTAÇÃO - {refeicao_title}"
        ws["A1"].font = title_font
        
        ws.merge_cells("A2:G2")
        ws["A2"] = f"Obra: {obra_nome}  |  Planilha: {planilha_nome}  |  Período: {master_start} até {master_end}"
        ws["A2"].font = subtitle_font
        
        # Headers Setup
        headers = ["Matrícula", "Nome do Colaborador", "Centro de Custo"]
        for d in dates_list:
            headers.append(d.strftime("%d/%m"))
        headers += ["Total Refeições"]
        
        header_row = 4
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=header_row, column=col_idx)
            cell.value = h
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
            
        ws.row_dimensions[header_row].height = 28
        
        # Data Rows
        start_data_row = 5
        for row_idx, colab in enumerate(final_list, start=start_data_row):
            row_fill = zebra_fill if row_idx % 2 == 0 else white_fill
            
            # Col A: Matricula
            cell_mat = ws.cell(row=row_idx, column=1, value=colab["matricula"])
            cell_mat.font = data_font
            cell_mat.fill = row_fill
            cell_mat.border = thin_border
            cell_mat.alignment = Alignment(horizontal="center")
            
            # Col B: Nome
            cell_nome = ws.cell(row=row_idx, column=2, value=colab["nome"])
            cell_nome.font = data_font
            cell_nome.fill = row_fill
            cell_nome.border = thin_border
            cell_nome.alignment = Alignment(horizontal="left")
            
            # Col C: Centro de Custo
            cell_cc = ws.cell(row=row_idx, column=3, value=colab["local_trab"])
            cell_cc.font = data_font
            cell_cc.fill = row_fill
            cell_cc.border = thin_border
            cell_cc.alignment = Alignment(horizontal="left")
            
            # Presence columns
            num_date_cols = len(dates_list)
            presences_dict = colab.get("presences", {})
            
            for date_idx, d in enumerate(dates_list):
                day_num = d.day
                presence_val = presences_dict.get(day_num, 0)
                col_pos = 4 + date_idx
                
                cell_pres = ws.cell(row=row_idx, column=col_pos, value=presence_val)
                cell_pres.border = thin_border
                cell_pres.alignment = Alignment(horizontal="center")
                
                if presence_val == 1:
                    cell_pres.fill = presence_1_fill
                    cell_pres.font = presence_1_font
                else:
                    cell_pres.fill = row_fill
                    cell_pres.font = presence_0_font
                    
            # Total Refeições formula
            first_date_col = get_column_letter(4)
            last_date_col = get_column_letter(3 + num_date_cols)
            col_total = 4 + num_date_cols
            
            cell_total = ws.cell(row=row_idx, column=col_total)
            cell_total.value = f"=SUM({first_date_col}{row_idx}:{last_date_col}{row_idx})"
            cell_total.font = bold_data_font
            cell_total.fill = summary_fill
            cell_total.border = thin_border
            cell_total.alignment = Alignment(horizontal="center")
            
            ws.row_dimensions[row_idx].height = 20
            
        # Summary Row at the bottom
        last_row = start_data_row + len(final_list) - 1
        total_row_idx = last_row + 2
        
        cell_total_label = ws.cell(row=total_row_idx, column=3, value="Total Geral")
        cell_total_label.font = Font(name=font_family, size=11, bold=True, color="2E7D32")
        cell_total_label.alignment = Alignment(horizontal="right")
        
        # SUM of Total Refeições
        col_total = 4 + len(dates_list)
        total_letter = get_column_letter(col_total)
        cell_total_val = ws.cell(row=total_row_idx, column=col_total)
        cell_total_val.value = f"=SUM({total_letter}5:{total_letter}{last_row})"
        cell_total_val.font = Font(name=font_family, size=11, bold=True)
        cell_total_val.border = Border(top=Side(style="double", color="2E7D32"))
        cell_total_val.alignment = Alignment(horizontal="center")
        
        # Auto-fit columns
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                if cell.row in (1, 2, total_row_idx):
                    continue
                if cell.value is not None:
                    val_str = str(cell.value)
                    if val_str.startswith("="):
                        max_len = max(max_len, 10)
                    else:
                        max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 10)
            
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 25
        
        # Save to bytes
        excel_buf = io.BytesIO()
        wb.save(excel_buf)
        excel_buf.seek(0)
        return excel_buf.getvalue(), obra_id, planilha_id, obra_nome, planilha_nome

upload_service = UploadService()
