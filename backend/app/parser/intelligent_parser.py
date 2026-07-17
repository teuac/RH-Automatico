import re
import csv
import io
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel

class ParsedFuncionario(BaseModel):
    matricula: str
    nome: str
    horarios: List[str]

class ParsedData(BaseModel):
    obra_nome: Optional[str] = None
    data: Optional[str] = None
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
        return date_str

    def parse_txt(self, file_content: str) -> ParsedData:
        lines = [line.strip() for line in file_content.splitlines()]
        
        obra_nome = None
        data_ponto = None
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
                        horarios=horarios
                    ))
                    i += 3
                    continue
                    
            i += 1
            
        return ParsedData(
            obra_nome=obra_nome,
            data=data_ponto,
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
        
        # If headers not clearly mapped, fallback to first 4 columns
        if idx_matricula == -1: idx_matricula = 0
        if idx_nome == -1: idx_nome = 1
        if idx_data == -1: idx_data = 2
        if idx_horarios == -1: idx_horarios = 3
        
        # Read contents
        start_row = 1 if len(headers) > 1 else 0
        for row in rows[start_row:]:
            if len(row) <= max(idx_matricula, idx_nome, idx_horarios):
                continue
                
            matricula = self.clean_string(row[idx_matricula])
            nome = self.clean_string(row[idx_nome])
            horarios_raw = self.clean_string(row[idx_horarios])
            
            if not self.is_valid_employee(matricula, nome):
                continue
                
            if idx_data < len(row):
                raw_date = self.clean_string(row[idx_data])
                parsed_date = self.parse_date(raw_date)
                if parsed_date and not data_ponto:
                    data_ponto = parsed_date
                    
            # Times could be space or comma separated
            horarios = re.findall(r'\d{2}:\d{2}', horarios_raw)
            
            funcionarios.append(ParsedFuncionario(
                matricula=matricula,
                nome=nome,
                horarios=horarios
            ))
            
        return ParsedData(
            data=data_ponto,
            funcionarios=funcionarios
        )

    def parse_xlsx(self, file_bytes: bytes) -> ParsedData:
        """
        Parses Excel sheets using pandas.
        """
        df = pd.read_excel(io.BytesIO(file_bytes))
        
        # Find column indexes
        cols = [str(c).strip().lower() for c in df.columns]
        
        idx_matricula = -1
        idx_nome = -1
        idx_data = -1
        idx_horarios = -1
        
        for idx, col in enumerate(cols):
            if any(term in col for term in ["matr", "reg", "num", "cod", "id"]):
                idx_matricula = idx
            elif any(term in col for term in ["nome", "func", "colab"]):
                idx_nome = idx
            elif "data" in col:
                idx_data = idx
            elif any(term in col for term in ["hor", "bat", "ponto", "marc"]):
                idx_horarios = idx
                
        if idx_matricula == -1: idx_matricula = 0
        if idx_nome == -1: idx_nome = 1
        if idx_data == -1: idx_data = 2
        if idx_horarios == -1: idx_horarios = 3
        
        funcionarios = []
        data_ponto = None
        
        for _, row in df.iterrows():
            row_list = list(row)
            if len(row_list) <= max(idx_matricula, idx_nome, idx_horarios):
                continue
                
            matricula = self.clean_string(row_list[idx_matricula])
            nome = self.clean_string(row_list[idx_nome])
            horarios_raw = self.clean_string(row_list[idx_horarios])
            
            if not self.is_valid_employee(matricula, nome):
                continue
                
            if idx_data < len(row_list):
                raw_date = self.clean_string(row_list[idx_data])
                parsed_date = self.parse_date(raw_date)
                if parsed_date and not data_ponto:
                    data_ponto = parsed_date
                    
            horarios = re.findall(r'\d{2}:\d{2}', str(horarios_raw))
            
            funcionarios.append(ParsedFuncionario(
                matricula=matricula,
                nome=nome,
                horarios=horarios
            ))
            
        return ParsedData(
            data=data_ponto,
            funcionarios=funcionarios
        )
