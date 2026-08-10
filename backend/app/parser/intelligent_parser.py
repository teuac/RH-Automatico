import re
import csv
import io
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel

class ParsedFuncionario(BaseModel):
    matricula: str
    nome: str
    horarios: List[str]
    data: Optional[str] = None

class ParsedData(BaseModel):
    obra_nome: Optional[str] = None
    data: Optional[str] = None
    datas_detectadas: List[str] = []  # All unique dates found in the file
    funcionarios: List[ParsedFuncionario] = []

class IntelligentParser:
    """
    Intelligent Parser class to process and extract presence logs
    from TXT, CSV, and XLSX files.
    """

    @staticmethod
    def clean_string(val: str) -> str:
        if pd.isna(val) if 'pd' in globals() else False:
            return ""
        val_str = str(val).strip()
        if val_str.lower() in ("nan", "nat", "<na>", "none", "null"):
            return ""
        return val_str

    @staticmethod
    def is_valid_employee(matricula: str, nome: str) -> bool:
        if not matricula or not nome:
            return False
            
        mat_lower = matricula.lower().strip()
        nome_lower = nome.lower().strip()
        
        # Filter typical empty/null/NaT/nan values
        for val in (mat_lower, nome_lower):
            if val in ("", "nan", "nat", "none", "null", "undefined", "<na>"):
                return False
                
        # Filter footprint/copyright footer labels or page pagination info
        if any(term in mat_lower or term in nome_lower for term in (
            "página", "pagina", "by rhnydus", "rhnydus", "total", "relatório", "relatorio", "período", "periodo", "filtro"
        )):
            return False
            
        # Filter out cases where matricula is a date-like value (e.g. contains 00:00:00 or matches date patterns)
        if "00:00:00" in mat_lower:
            return False
            
        if re.search(r'\d{4}-\d{2}-\d{2}', mat_lower) or re.search(r'\d{2}/\d{2}/\d{4}', mat_lower):
            return False
            
        return True

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Convert date to YYYY-MM-DD format"""
        if not date_str:
            return None
        # Remove whitespace
        date_str = date_str.strip()
        # Pattern YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        # Pattern DD/MM/YYYY
        match_br = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', date_str)
        if match_br:
            return f"{match_br.group(3)}-{match_br.group(2)}-{match_br.group(1)}"
        return None

    @staticmethod
    def extract_date_from_row(row_cells: List[Any]) -> Optional[str]:
        """
        Scans row cells for any standalone date (DD/MM/YYYY, YYYY-MM-DD, or pandas Timestamp).
        Commonly found in section headers before employee rows.
        """
        import datetime as _dt
        for cell in row_cells:
            if cell is None:
                continue
            # Handle pandas Timestamp / Python datetime directly
            if isinstance(cell, (_dt.datetime, _dt.date)):
                return cell.strftime("%Y-%m-%d")
            try:
                if isinstance(cell, pd.Timestamp) and not pd.isna(cell):
                    return cell.strftime("%Y-%m-%d")
            except Exception:
                pass
            val = str(cell).strip()
            if not val or val.lower() in ("nan", "nat", "none", "null"):
                continue
            # Search DD/MM/YYYY
            match_br = re.search(r'\b(\d{2})/(\d{2})/(\d{4})\b', val)
            if match_br:
                return f"{match_br.group(3)}-{match_br.group(2)}-{match_br.group(1)}"
            # Search YYYY-MM-DD
            match_iso = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', val)
            if match_iso:
                return f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"
        return None

    @staticmethod
    def is_date_only_row(row_cells: List[Any]) -> bool:
        """
        Returns True if this row is a date-section header (only non-empty cell is a date).
        Used to detect section separators like '27/06/2026' rows in Excel reports.
        """
        non_empty = []
        for cell in row_cells:
            if cell is None:
                continue
            try:
                if pd.isna(cell):
                    continue
            except Exception:
                pass
            val = str(cell).strip()
            if val and val.lower() not in ("nan", "nat", "none", "null", ""):
                non_empty.append(val)

        if len(non_empty) != 1:
            return False
        val = non_empty[0]
        return bool(
            re.match(r'^\d{2}/\d{2}/\d{4}$', val) or
            re.match(r'^\d{4}-\d{2}-\d{2}$', val)
        )

    def parse_txt(self, file_content: str) -> ParsedData:

        lines = [line.strip() for line in file_content.splitlines()]
        
        obra_nome = None
        data_ponto = None
        current_active_date = None
        funcionarios: List[ParsedFuncionario] = []
        
        # Regex helpers
        obra_pattern = re.compile(r'(?i)(?:obra|projeto|local):\s*(.+)')
        date_pattern = re.compile(r'(?i)(?:data|periodo):\s*([\d\/\-]+)')
        matricula_pattern = re.compile(r'^\d{4,10}$')
        nome_pattern = re.compile(r'^[A-Za-zÀ-ÿ\s\.\-\(\)]+$')
        times_pattern = re.compile(r'^(\d{2}:\d{2}\s*)+$')
        
        i = 0
        n_lines = len(lines)
        
        while i < n_lines:
            line = lines[i]
            if not line:
                i += 1
                continue
                
            # Check for header date line
            line_found_date = self.extract_date_from_row([line])
            if line_found_date:
                current_active_date = line_found_date
                if not data_ponto:
                    data_ponto = line_found_date

            # Try to match metadata headers first
            obra_match = obra_pattern.match(line)
            if obra_match:
                obra_nome = self.clean_string(obra_match.group(1))
                i += 1
                continue
                
            date_match = date_pattern.match(line)
            if date_match:
                parsed_date = self.parse_date(self.clean_string(date_match.group(1)))
                if parsed_date:
                    data_ponto = parsed_date
                    current_active_date = parsed_date
                i += 1
                continue
            
            # Look ahead for a 3-line employee pattern: ID -> Name -> Times
            if i + 2 < n_lines:
                potential_id = line
                potential_name = lines[i+1]
                potential_times = lines[i+2]
                
                if (matricula_pattern.match(potential_id) and 
                    nome_pattern.match(potential_name) and 
                    times_pattern.match(potential_times)):
                    
                    horarios = potential_times.split()
                    funcionarios.append(ParsedFuncionario(
                        matricula=potential_id,
                        nome=potential_name,
                        horarios=horarios,
                        data=current_active_date or data_ponto
                    ))
                    i += 3
                    continue
                    
            i += 1

        # Collect all unique dates from funcionarios + header date
        datas_set = {f.data for f in funcionarios if f.data}
        if data_ponto:
            datas_set.add(data_ponto)
        datas_detectadas = sorted(datas_set)
            
        return ParsedData(
            obra_nome=obra_nome,
            data=data_ponto,
            datas_detectadas=datas_detectadas,
            funcionarios=funcionarios
        )

    def parse_csv(self, file_content: str) -> ParsedData:
        """
        Parses CSV structure.
        Expected headers or column names like:
        Matrícula/Registro, Nome/Funcionário, Data, Batidas/Horários
        """
        f = io.StringIO(file_content)
        reader = csv.reader(f)
        rows = list(reader)
        
        if not rows:
            return ParsedData()
            
        # Try to identify headers
        headers = [h.strip().lower() for h in rows[0]]
        
        # Check mapping positions
        idx_matricula = -1
        idx_nome = -1
        idx_data = -1
        idx_horarios = -1
        
        for idx, h in enumerate(headers):
            if any(term in h for term in ["matr", "reg", "num", "cod", "id"]):
                idx_matricula = idx
            elif any(term in h for term in ["nome", "func", "colab"]):
                idx_nome = idx
            elif "data" in h:
                idx_data = idx
            elif any(term in h for term in ["hor", "bat", "ponto", "marc"]):
                idx_horarios = idx
                
        funcionarios = []
        data_ponto = None
        current_active_date = None
        
        # If headers not clearly mapped, fallback to first 4 columns
        if idx_matricula == -1: idx_matricula = 0
        if idx_nome == -1: idx_nome = 1
        if idx_data == -1: idx_data = 2
        if idx_horarios == -1: idx_horarios = 3
        
        # Read contents
        start_row = 1 if len(headers) > 1 else 0
        for row in rows[start_row:]:
            if not row or all(not str(c).strip() for c in row):
                continue
                
            row_found_date = self.extract_date_from_row(row)
            if row_found_date:
                current_active_date = row_found_date
                if not data_ponto:
                    data_ponto = row_found_date

            if len(row) <= max(idx_matricula, idx_nome, idx_horarios):
                continue
                
            matricula = self.clean_string(row[idx_matricula])
            nome = self.clean_string(row[idx_nome])
            horarios_raw = self.clean_string(row[idx_horarios])
            
            if not self.is_valid_employee(matricula, nome):
                continue
                
            row_date = None
            if idx_data < len(row):
                raw_date = self.clean_string(row[idx_data])
                row_date = self.parse_date(raw_date)
                    
            final_date = row_date or current_active_date or data_ponto

            # Times could be space or comma separated
            horarios = re.findall(r'\d{2}:\d{2}', horarios_raw)
            
            funcionarios.append(ParsedFuncionario(
                matricula=matricula,
                nome=nome,
                horarios=horarios,
                data=final_date
            ))
            
        datas_set = {f.data for f in funcionarios if f.data}
        if data_ponto:
            datas_set.add(data_ponto)
        datas_detectadas = sorted(datas_set)

        return ParsedData(
            data=data_ponto,
            datas_detectadas=datas_detectadas,
            funcionarios=funcionarios
        )


    def parse_xlsx(self, file_bytes: bytes) -> ParsedData:
        """
        Parses Excel sheets using pandas.

        Handles the multi-day format where date section headers (e.g., '27/06/2026')
        separate groups of employees by day. Columns are auto-detected:
          - matricula: first column with a numeric-only cell value
          - nome: first non-empty string column after matricula
          - horarios: all remaining columns (collected as time-formatted tokens)

        Also handles pandas Timestamp date cells from Excel date formatting.
        """
        # Read without assuming headers to preserve all rows including date section rows
        df = pd.read_excel(io.BytesIO(file_bytes), header=None, dtype=str)

        # Replace NaN strings back to NaN for clean checks
        df = df.where(df.notna(), other=None)

        # Try to detect if first row is a header (text like "Matrícula", "Nome", etc.)
        first_row = [self.clean_string(str(c)) if c is not None else "" for c in df.iloc[0]]
        has_header = any(
            any(t in v.lower() for t in ["matr", "nome", "func", "hora", "batid"])
            for v in first_row if v
        )
        start_row = 1 if has_header else 0

        # Detect fixed column positions from header (if present)
        idx_matricula = -1
        idx_nome = -1
        idx_horarios_start = -1

        if has_header:
            for idx, h in enumerate(first_row):
                hl = h.lower()
                if idx_matricula == -1 and any(t in hl for t in ["matr", "reg", "num", "cod"]):
                    idx_matricula = idx
                elif idx_nome == -1 and any(t in hl for t in ["nome", "func", "colab"]):
                    idx_nome = idx
                elif idx_horarios_start == -1 and any(t in hl for t in ["hor", "bat", "ponto", "marc"]):
                    idx_horarios_start = idx

        funcionarios = []
        data_ponto = None
        current_active_date = None

        for row_idx in range(start_row, len(df)):
            row_raw = list(df.iloc[row_idx])

            # Build clean string list and check if all empty
            row_str = [self.clean_string(str(c)) if c is not None else "" for c in row_raw]
            if not any(row_str):
                continue

            # ── 1. Check for date section header rows ──────────────────────
            # First try pandas Timestamp / datetime detection
            row_date_found = self.extract_date_from_row(row_raw)
            if not row_date_found:
                row_date_found = self.extract_date_from_row(row_str)

            if row_date_found:
                current_active_date = row_date_found
                if not data_ponto:
                    data_ponto = row_date_found
                # If this row is ONLY a date (section separator), skip employee parsing
                if self.is_date_only_row(row_str):
                    continue

            # ── 2. Auto-detect column positions from actual data ──────────
            # Find matricula column: first col with a numeric-like non-empty value
            local_mat_idx = idx_matricula
            local_nome_idx = idx_nome
            local_hor_start = idx_horarios_start

            if local_mat_idx == -1:
                for ci, v in enumerate(row_str):
                    if v and re.match(r'^\d{3,10}$', v.strip()):
                        local_mat_idx = ci
                        break

            if local_mat_idx == -1:
                # Cannot identify matricula for this row — skip
                continue

            if local_nome_idx == -1:
                # Nome: first non-empty string column AFTER matricula that isn't a time or number
                for ci in range(local_mat_idx + 1, len(row_str)):
                    v = row_str[ci].strip()
                    if v and not re.match(r'^\d{2}:\d{2}(:\d{2})?$', v) and not re.match(r'^\d+$', v):
                        local_nome_idx = ci
                        break

            if local_nome_idx == -1:
                continue

            # Horarios start: first column AFTER nome with time-like values (HH:MM)
            if local_hor_start == -1:
                local_hor_start = local_nome_idx + 1

            # ── 3. Extract values ─────────────────────────────────────────
            matricula = row_str[local_mat_idx].strip()
            nome = row_str[local_nome_idx].strip()

            if not self.is_valid_employee(matricula, nome):
                continue

            # Collect all time tokens from columns after nome column
            horarios = []
            for ci in range(local_hor_start, len(row_str)):
                v = row_str[ci]
                horarios += re.findall(r'\d{2}:\d{2}', v)

            final_date = current_active_date or data_ponto

            funcionarios.append(ParsedFuncionario(
                matricula=matricula,
                nome=nome,
                horarios=horarios,
                data=final_date
            ))

        datas_set = {f.data for f in funcionarios if f.data}
        if data_ponto:
            datas_set.add(data_ponto)
        datas_detectadas = sorted(datas_set)

        return ParsedData(
            data=data_ponto,
            datas_detectadas=datas_detectadas,
            funcionarios=funcionarios
        )

