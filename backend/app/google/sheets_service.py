import os
import json
from typing import Dict, List, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from app.config.settings import settings
from app.config.logging_config import app_logger, error_logger

class GoogleSheetsService:
    """
    Google Sheets Service interacting with Spreadsheet via Service Account.
    """

    def __init__(self):
        self.creds = None
        self.service = None
        self._initialize_credentials()

    def _initialize_credentials(self):
        """Loads Service Account credentials from individual env vars, JSON string, or local file"""
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        try:
            # 1. Prioridade: variáveis individuais GOOGLE_SA_* definidas no .env
            sa_dict = settings.google_service_account_dict
            if sa_dict:
                self.creds = service_account.Credentials.from_service_account_info(
                    sa_dict, scopes=scopes
                )
                self.service = build("sheets", "v4", credentials=self.creds)
                app_logger.info("Google Sheets API service successfully initialized from individual GOOGLE_SA_* env vars.")
                return

            # 2. Fallback: JSON completo na variável GOOGLE_SERVICE_ACCOUNT_INFO
            if settings.GOOGLE_SERVICE_ACCOUNT_INFO:
                info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_INFO)
                self.creds = service_account.Credentials.from_service_account_info(
                    info, scopes=scopes
                )
                self.service = build("sheets", "v4", credentials=self.creds)
                app_logger.info("Google Sheets API service successfully initialized from GOOGLE_SERVICE_ACCOUNT_INFO env.")
                return

            # 3. Fallback: arquivo JSON local
            file_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if os.path.exists(file_path):
                self.creds = service_account.Credentials.from_service_account_file(
                    file_path, scopes=scopes
                )
                self.service = build("sheets", "v4", credentials=self.creds)
                app_logger.info(f"Google Sheets API service successfully initialized from file: {file_path}")
                return

            app_logger.warning(
                "Google Service Account credentials not found. "
                "Defina GOOGLE_SA_CLIENT_EMAIL, GOOGLE_SA_PRIVATE_KEY e GOOGLE_SA_PROJECT_ID no .env. "
                "Google Sheets updates will be skipped or mocked in development."
            )
        except Exception as e:
            error_logger.exception(f"Failed to initialize Google Sheets service: {str(e)}")

    def is_configured(self) -> bool:
        return self.service is not None

    def read_sheet_values(self, spreadsheet_id: str, range_name: str, value_render_option: Optional[str] = None) -> Optional[List[List]]:
        """Reads values from a spreadsheet range"""
        if not self.is_configured():
            # Mock data for dev when credentials are not available
            return [
                ["Matricula", "Nome", "10/07/2026", "11/07/2026", "12/07/2026", "13/07/2026"],
                ["001798", "José Carlos", "", "", "", ""],
                ["001799", "Maria Oliveira", "", "", "", ""]
            ]
        try:
            sheet = self.service.spreadsheets()
            kwargs = {"spreadsheetId": spreadsheet_id, "range": range_name}
            if value_render_option:
                kwargs["valueRenderOption"] = value_render_option
            result = sheet.values().get(**kwargs).execute()
            return result.get("values", [])
        except Exception as e:
            error_logger.exception(f"Error reading from Google Sheet {spreadsheet_id}: {str(e)}")
            raise e

    def get_column_letter(self, col_index: int) -> str:
        """Converts zero-indexed column index to Excel column letters (e.g. 0 -> A, 27 -> AB)"""
        letter = ""
        while col_index >= 0:
            letter = chr(col_index % 26 + 65) + letter
            col_index = col_index // 26 - 1
        return letter

    def _get_day_range_cols(self, headers: List[str]) -> Tuple[str, str, int]:
        """Returns (start_day_col_letter, end_day_col_letter, num_days) based on headers list"""
        start_col = "C"
        dias_totais_idx = -1
        for idx, h in enumerate(headers):
            if h in ("Dias Totais", "Faltas Totais"):
                dias_totais_idx = idx
                break
        if dias_totais_idx > 2:
            end_col_idx = dias_totais_idx - 1
        else:
            end_col_idx = len(headers) - 1
        end_col = self.get_column_letter(end_col_idx)
        num_days = max(1, end_col_idx - 2 + 1)
        return start_col, end_col, num_days

    def get_sheet_id(self, spreadsheet_id: str, tab_name: str) -> Optional[int]:
        """Fetches the numeric sheetId for a given tab_name in a spreadsheet"""
        if not self.is_configured():
            return 0
        try:
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for s in sheet_metadata.get('sheets', []):
                props = s.get('properties', {})
                if props.get('title') == tab_name:
                    return props.get('sheetId')
        except Exception as e:
            error_logger.exception(f"Error fetching sheetId for tab '{tab_name}': {str(e)}")
        return None

    def restyle_terceirizadas_headers(self, spreadsheet_id: str, sheet_id: int, matrix: List[List]):
        """
        Dynamically locates TERCEIRIZADAS section header and sub-header in matrix,
        cleans background color of any previous rows, and applies Dark Slate and Slate Blue header styling
        to the exact current row indices.
        """
        if not self.is_configured() or sheet_id is None or not matrix:
            return

        terc_sec_row_idx = -1
        terc_header_row_idx = -1

        for idx, r in enumerate(matrix):
            if r:
                row_str = " ".join([str(c).strip().lower() for c in r[:2] if c])
                if "terceirizadas" in row_str:
                    terc_sec_row_idx = idx
                elif "empresa / terceirizada" in row_str or "nome / terceirizada" in row_str:
                    terc_header_row_idx = idx

        if terc_sec_row_idx == -1:
            return

        headers = matrix[1] if len(matrix) > 1 else []
        _, _, num_days = self._get_day_range_cols(headers)
        total_cols = num_days + 4 if num_days > 0 else 35

        requests = []

        # 1. Reset background color for rows 2 to (terc_sec_row_idx - 1) to clean any old header color when section moves down
        if terc_sec_row_idx > 2:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 2,
                        "endRowIndex": terc_sec_row_idx,
                        "startColumnIndex": 0,
                        "endColumnIndex": total_cols
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            })

        # 2. Format TERCEIRIZADAS Section Header Row: Dark Slate background (#37474F)
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": terc_sec_row_idx,
                    "endRowIndex": terc_sec_row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": total_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.22, "green": 0.28, "blue": 0.31},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 11, "fontFamily": "Arial"},
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        })

        # 3. Format TERCEIRIZADAS Sub-Header Row: Slate Blue (#33598C) for entire row
        if terc_header_row_idx != -1:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": terc_header_row_idx,
                        "endRowIndex": terc_header_row_idx + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": total_cols
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.35, "blue": 0.55},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10, "fontFamily": "Arial"},
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            })

        try:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
            app_logger.info(f"Successfully restyled Terceirizadas header at row {terc_sec_row_idx + 1} and subheader at row {terc_header_row_idx + 1}.")
        except Exception as e:
            error_logger.exception(f"Error restyling Terceirizadas section: {str(e)}")

    def update_cell(self, spreadsheet_id: str, tab_name: str, row_num: int, col_num: int, value: str) -> bool:
        """
        Updates a specific cell using A1 notation.
        row_num: 1-indexed row number
        col_num: 0-indexed column number
        """
        if not self.is_configured():
            app_logger.info(f"[MOCK] Updated sheet {spreadsheet_id} tab {tab_name} cell {self.get_column_letter(col_num)}{row_num} to '{value}'")
            return True
            
        col_letter = self.get_column_letter(col_num)
        cell_range = f"'{tab_name}'!{col_letter}{row_num}"
        body = {"values": [[value]]}
        
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=cell_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            app_logger.info(f"Updated Google Sheets cell {cell_range} to {value}")
            return True
        except Exception as e:
            error_logger.exception(f"Error updating cell {cell_range} in spreadsheet {spreadsheet_id}: {str(e)}")
            return False

    def sync_presence(
        self,
        spreadsheet_id: str,
        tab_name: str,
        date_str: str,  # format YYYY-MM-DD
        matricula: str,
        employee_name: str,
        mark: str = "A"  # "A" = alimentou, "F" = falta
    ) -> Tuple[str, str]:
        """
        Syncs presence for a single employee.
        mark: the value to write in the cell — 'A' (fed) or 'F' (absent)
        Returns: Tuple[status, details]
          status: 'ATUALIZADO', 'PENDENTE', 'IGNORADO'
          details: reason or description of results
        """
        # Load sheets matrix
        try:
            # We assume reading the top 200 rows of columns A to AZ is sufficient.
            range_name = f"'{tab_name}'!A1:AZ200"
            values = self.read_sheet_values(spreadsheet_id, range_name)
        except Exception as e:
            return "PENDENTE", f"Erro de comunicação com a planilha: {str(e)}"

        if not values or len(values) < 1:
            return "PENDENTE", "Planilha vazia ou sem cabeçalhos."

        # Parse date formats to find date column
        # Date formats inside sheets could be DD/MM/YYYY, YYYY-MM-DD, DD/MM, or only the day number (D or DD)
        date_parts = date_str.split("-")
        dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else date_str
        dd_mm = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else date_str
        
        alt_dates = set([date_str, dd_mm_yyyy, dd_mm])
        if len(date_parts) == 3:
            try:
                day_int = int(date_parts[2])
                month_int = int(date_parts[1])
                alt_dates.add(str(day_int))
                alt_dates.add(f"{day_int:02d}")
                alt_dates.add(f"{day_int}/{date_parts[1]}/{date_parts[0]}")
                alt_dates.add(f"{day_int}/{month_int}/{date_parts[0]}")
                alt_dates.add(f"{date_parts[2]}/{month_int}/{date_parts[0]}")
                alt_dates.add(f"{day_int}/{date_parts[1]}")
                alt_dates.add(f"{day_int}/{month_int}")
                alt_dates.add(f"{date_parts[2]}/{month_int}")
            except ValueError:
                pass

        # Dynamically locate the header row (index 1 if row 0 is a Title row, otherwise index 0)
        header_row_idx = 0
        if len(values) > 1 and any("matricula" in str(cell).lower() for cell in values[1]):
            header_row_idx = 1

        headers = [str(cell).strip() for cell in values[header_row_idx]]
        
        col_index_date = -1
        for idx, header in enumerate(headers):
            if header in alt_dates:
                col_index_date = idx
                break

        if col_index_date == -1:
            return "PENDENTE", f"Coluna referente à data {dd_mm_yyyy} não foi localizada."

        # Find employee row starting after the headers
        row_index_employee = -1
        
        for idx, row in enumerate(values[header_row_idx + 1:], start=header_row_idx + 2):
            if not row:
                continue
            
            # Check matricula in col 0 or 1
            row_matricula = str(row[0]).strip() if len(row) > 0 else ""
            row_matricula_alt = str(row[1]).strip() if len(row) > 1 else ""
            
            # Compare matricula (remove leading zeros for clean matching)
            clean_input_mat = matricula.lstrip("0")
            clean_row_mat = row_matricula.lstrip("0")
            clean_row_mat_alt = row_matricula_alt.lstrip("0")

            if (clean_input_mat and (clean_input_mat == clean_row_mat or clean_input_mat == clean_row_mat_alt)):
                row_index_employee = idx
                break
                
            # Fallback to name search if matricula match fails
            row_name = str(row[1]).strip() if len(row) > 1 else str(row[0]).strip()
            if employee_name.strip() and row_name.strip() and (employee_name.lower() in row_name.lower() or row_name.lower() in employee_name.lower()):
                row_index_employee = idx
                # Keep searching to see if a better matricula matches, but hold this as fallback

        if row_index_employee == -1:
            # Automatically register the employee to the spreadsheet tab at the next row
            new_row_num = len(values) + 1
            range_to_append = f"'{tab_name}'!A{new_row_num}:B{new_row_num}"
            body = {"values": [[matricula, employee_name]]}
            try:
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_to_append,
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute()
                app_logger.info(f"Automatically registered new employee {employee_name} ({matricula}) to Google Sheets tab {tab_name} on row {new_row_num}.")
                
                # Append the new row to our local matrix to maintain correct row count for subsequent iterations
                values.append([matricula, employee_name])
                row_index_employee = new_row_num
            except Exception as e:
                return "PENDENTE", f"Falha ao cadastrar funcionário novo na planilha: {str(e)}"

        # Check if already marked with the same value (avoid overwrite)
        current_row_data = values[row_index_employee - 1]
        if col_index_date < len(current_row_data):
            cell_value = str(current_row_data[col_index_date]).strip().upper()
            if cell_value == mark:
                return "IGNORADO", f"Célula já marcada como '{mark}'."
            # If cell has "A" or "J" and we'd write "F", skip (presença/justificativa prevalece sobre falta)
            if cell_value in ("A", "J") and mark == "F":
                return "IGNORADO", f"Presença/Justificativa já registrada ({cell_value}) — falta ignorada."
        # Update the cell to the specified mark
        success = self.update_cell(spreadsheet_id, tab_name, row_index_employee, col_index_date, mark)
        if success:
            return "ATUALIZADO", f"Status '{mark}' registrado na linha {row_index_employee} col {self.get_column_letter(col_index_date)}."
        else:
            return "PENDENTE", f"Falha ao gravar status '{mark}' na planilha."

    def _clean_matrix_gaps(self, matrix: List[List]) -> bool:
        """
        Removes unnecessary empty colaborador rows between the last populated employee and
        the TERCEIRIZADAS section, leaving exactly one clean separator row.
        Returns True if matrix was modified, False otherwise.
        """
        if not matrix or len(matrix) < 4:
            return False

        header_row_idx = 0
        if len(matrix) > 1 and any("matricula" in str(cell).lower() for cell in matrix[1]):
            header_row_idx = 1

        terc_sec_idx = -1
        for idx, r in enumerate(matrix):
            if r and any("terceirizadas" in str(c).lower() for c in r[:2]):
                terc_sec_idx = idx
                break

        if terc_sec_idx == -1 or terc_sec_idx <= header_row_idx + 1:
            return False

        colab_slice = matrix[header_row_idx + 1 : terc_sec_idx]

        def is_populated(row: List) -> bool:
            if not row:
                return False
            mat = str(row[0]).strip() if len(row) > 0 else ""
            name = str(row[1]).strip() if len(row) > 1 else ""
            if mat.lower() in ("matricula", "matrícula", "terceirizadas") or name.lower() in ("nome", "funcionário", "funcionario"):
                return False
            return bool(mat or name)

        last_populated_rel_idx = -1
        for idx, row in enumerate(colab_slice):
            if is_populated(row):
                last_populated_rel_idx = idx

        keep_end_rel_idx = last_populated_rel_idx + 1
        current_colab_len = len(colab_slice)
        target_colab_len = keep_end_rel_idx + 1

        if current_colab_len > target_colab_len:
            start_del = header_row_idx + 1 + target_colab_len
            del matrix[start_del : terc_sec_idx]
            return True

        return False

    def _reenforce_total_formulas(self, matrix: List[List], valor_diario_vt: Optional[float] = None) -> bool:
        """
        Re-evaluates and ensures that every data row in matrix has the exact correct dynamic formulas:
        - Colaboradores rows: =CONT.SE(C{r}:{end_c}{r}; "A") (* valor_diario_vt if provided) for Dias Totais/Valor VT, =CONT.SE(C{r}:{end_c}{r}; "F") for Faltas Totais
        - Terceirizadas rows: =SOMA(C{r}:{end_c}{r}) (* valor_diario_vt if provided) for Dias Totais, "" for Faltas Totais
        Returns True if any formula in matrix was modified/repaired, False otherwise.
        """
        if not matrix or len(matrix) < 2:
            return False

        header_row_idx = 0
        if len(matrix) > 1 and any("matricula" in str(cell).lower() for cell in matrix[1]):
            header_row_idx = 1

        headers = [str(cell).strip() for cell in matrix[header_row_idx]]
        start_c, end_c, num_days = self._get_day_range_cols(headers)
        if num_days <= 0:
            return False

        col_dias = num_days + 2
        col_faltas = num_days + 3

        terc_sec_idx = -1
        terc_header_idx = -1

        for idx, r in enumerate(matrix):
            if r:
                row_str = " ".join([str(c).strip().lower() for c in r[:2] if c])
                if "terceirizadas" in row_str and terc_sec_idx == -1:
                    terc_sec_idx = idx
                elif ("empresa / terceirizada" in row_str or "nome / terceirizada" in row_str) and terc_header_idx == -1:
                    terc_header_idx = idx

        modified = False

        for r_idx in range(header_row_idx + 1, len(matrix)):
            r = r_idx + 1  # 1-indexed row number in Google Sheets
            row = matrix[r_idx]

            if r_idx in (header_row_idx, terc_sec_idx):
                continue

            if r_idx == terc_header_idx:
                while len(row) <= col_faltas:
                    row.append("")
                if row[col_dias] != "Dias Totais":
                    row[col_dias] = "Dias Totais"
                    modified = True
                if row[col_faltas] != "Faltas Totais":
                    row[col_faltas] = "Faltas Totais"
                    modified = True
                continue

            # Skip separator empty row between Colaboradores and Terceirizadas
            if terc_sec_idx != -1 and r_idx == terc_sec_idx - 1:
                continue

            while len(row) <= col_faltas:
                row.append("")

            if terc_header_idx != -1 and r_idx > terc_header_idx:
                # Terceirizada data row: Dias Totais = SOMA (* valor_diario_vt if specified)
                if valor_diario_vt and valor_diario_vt > 0:
                    expected_dias = f'=SOMA({start_c}{r}:{end_c}{r}) * {valor_diario_vt}'
                else:
                    expected_dias = f'=SOMA({start_c}{r}:{end_c}{r})'
                expected_faltas = ""
                if row[col_dias] != expected_dias:
                    row[col_dias] = expected_dias
                    modified = True
                if row[col_faltas] != expected_faltas:
                    row[col_faltas] = expected_faltas
                    modified = True
            elif terc_sec_idx != -1 and r_idx > terc_sec_idx:
                continue
            else:
                # Colaborador data row: Dias Totais = CONT.SE "A" (* valor_diario_vt if specified), Faltas Totais = CONT.SE "F"
                if valor_diario_vt and valor_diario_vt > 0:
                    expected_dias = f'=CONT.SE({start_c}{r}:{end_c}{r}; "A") * {valor_diario_vt}'
                elif row[col_dias] and "*" in str(row[col_dias]):
                    mult = str(row[col_dias]).split("*")[-1].strip()
                    expected_dias = f'=CONT.SE({start_c}{r}:{end_c}{r}; "A") * {mult}'
                else:
                    expected_dias = f'=CONT.SE({start_c}{r}:{end_c}{r}; "A")'

                expected_faltas = f'=CONT.SE({start_c}{r}:{end_c}{r}; "F")'
                if row[col_dias] != expected_dias:
                    row[col_dias] = expected_dias
                    modified = True
                if row[col_faltas] != expected_faltas:
                    row[col_faltas] = expected_faltas
                    modified = True

        return modified

    def batch_sync_presence(
        self,
        spreadsheet_id: str,
        tab_name: str,
        date_str: str,
        employees: List[Dict[str, Any]],
        valor_diario_vt: Optional[float] = None
    ) -> List[Tuple[str, str, str]]:
        """
        Syncs presence for multiple employees in a batch (1 Read + 1 Write call).
        Returns: List of tuples (matricula, status_result, details)
        """
        if not self.is_configured():
            results = []
            for emp in employees:
                results.append((emp.get("matricula", ""), "ATUALIZADO", "Sincronização simulada em desenvolvimento (Mock)."))
            return results

        try:
            # 1. Read sheet values once with value_render_option="FORMULA" to preserve formula expressions
            range_name = f"'{tab_name}'!A1:AZ500"
            values = self.read_sheet_values(spreadsheet_id, range_name, value_render_option="FORMULA")
        except Exception as e:
            return [(emp.get("matricula", ""), "PENDENTE", f"Erro de comunicação com a planilha: {str(e)}") for emp in employees]

        if not values or len(values) < 1:
            return [(emp.get("matricula", ""), "PENDENTE", "Planilha vazia ou sem cabeçalhos.") for emp in employees]

        # 2. Find date column index
        date_parts = date_str.split("-")
        dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else date_str
        dd_mm = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else date_str
        
        alt_dates = set([date_str, dd_mm_yyyy, dd_mm])
        if len(date_parts) == 3:
            try:
                day_int = int(date_parts[2])
                month_int = int(date_parts[1])
                alt_dates.add(str(day_int))
                alt_dates.add(f"{day_int:02d}")
                alt_dates.add(f"{day_int}/{date_parts[1]}/{date_parts[0]}")
                alt_dates.add(f"{day_int}/{month_int}/{date_parts[0]}")
                alt_dates.add(f"{date_parts[2]}/{month_int}/{date_parts[0]}")
                alt_dates.add(f"{day_int}/{date_parts[1]}")
                alt_dates.add(f"{day_int}/{month_int}")
                alt_dates.add(f"{date_parts[2]}/{month_int}")
            except ValueError:
                pass

        # Dynamically locate the header row (index 1 if row 0 is a Title row, otherwise index 0)
        header_row_idx = 0
        if len(values) > 1 and any("matricula" in str(cell).lower() for cell in values[1]):
            header_row_idx = 1

        headers = [str(cell).strip() for cell in values[header_row_idx]]
        col_index_date = -1
        for idx, header in enumerate(headers):
            if header in alt_dates:
                col_index_date = idx
                break

        if col_index_date == -1:
            return [(emp.get("matricula", ""), "PENDENTE", f"Coluna de data {dd_mm_yyyy} não encontrada.") for emp in employees]

        # Convert values matrix to list of lists of strings
        matrix = []
        for r in values:
            row_list = [str(c) for c in r]
            matrix.append(row_list)

        results = []
        sheet_updated = False

        for emp in employees:
            matricula = emp.get("matricula", "")
            nome = emp.get("nome", "")
            mark = emp.get("presenca", "A")

            # Match employee in matrix
            row_index_employee = -1
            
            for idx, row in enumerate(matrix[header_row_idx + 1:], start=header_row_idx + 2):
                if not row:
                    continue
                row_matricula = str(row[0]).strip() if len(row) > 0 else ""
                row_matricula_alt = str(row[1]).strip() if len(row) > 1 else ""
                row_name = str(row[1]).strip() if len(row) > 1 else str(row[0]).strip()

                # Skip section headers and non-employee rows
                if row_matricula.lower() in ("terceirizadas", "código/id", "codigo/id", "matricula", "matrícula") or row_name.lower() in ("terceirizadas", "nome / terceirizada"):
                    continue

                clean_input_mat = matricula.lstrip("0")
                clean_row_mat = row_matricula.lstrip("0")
                clean_row_mat_alt = row_matricula_alt.lstrip("0")

                if (clean_input_mat and (clean_input_mat == clean_row_mat or clean_input_mat == clean_row_mat_alt)):
                    row_index_employee = idx
                    break
                    
                if nome.strip() and row_name.strip() and (nome.lower() in row_name.lower() or row_name.lower() in nome.lower()):
                    row_index_employee = idx

            # If not found, use a pre-allocated empty slot before Terceirizadas, or insert/append
            if row_index_employee == -1:
                terc_idx = -1
                for idx, r in enumerate(matrix):
                    if r and any("terceirizadas" in str(c).lower() for c in r[:2]):
                        terc_idx = idx
                        break

                start_c, end_c, num_days_count = self._get_day_range_cols(headers)

                # 1. Try to find a pre-allocated empty colaborador slot before Terceirizadas
                empty_slot_idx = -1
                search_limit = terc_idx if terc_idx != -1 else len(matrix)
                for idx in range(header_row_idx + 1, search_limit):
                    r = matrix[idx]
                    if r and len(r) >= 2 and str(r[0]).strip() == "" and str(r[1]).strip() == "":
                        empty_slot_idx = idx
                        break

                if empty_slot_idx != -1:
                    matrix[empty_slot_idx][0] = matricula
                    matrix[empty_slot_idx][1] = nome
                    row_index_employee = empty_slot_idx + 1
                elif terc_idx != -1:
                    insert_pos = terc_idx
                    if terc_idx > 0 and not any(matrix[terc_idx - 1]):
                        insert_pos = terc_idx - 1
                    r_num = insert_pos + 1
                    formula_dias = f'=CONT.SE({start_c}{r_num}:{end_c}{r_num}; "A")'
                    formula_faltas = f'=CONT.SE({start_c}{r_num}:{end_c}{r_num}; "F")'
                    new_row = [matricula, nome] + [""] * num_days_count + [formula_dias, formula_faltas]
                    matrix.insert(insert_pos, new_row)
                    row_index_employee = insert_pos + 1
                else:
                    r_num = len(matrix) + 1
                    formula_dias = f'=CONT.SE({start_c}{r_num}:{end_c}{r_num}; "A")'
                    formula_faltas = f'=CONT.SE({start_c}{r_num}:{end_c}{r_num}; "F")'
                    new_row = [matricula, nome] + [""] * num_days_count + [formula_dias, formula_faltas]
                    matrix.append(new_row)
                    row_index_employee = len(matrix)

                sheet_updated = True
                app_logger.info(f"Local batch: registered employee {nome} ({matricula})")

            # Ensure row has enough cells up to the date column
            current_row = matrix[row_index_employee - 1]
            while len(current_row) <= col_index_date:
                current_row.append("")

            # Check existing value
            cell_value = current_row[col_index_date].strip().upper()
            if cell_value == mark:
                results.append((matricula, "IGNORADO", f"Célula já marcada como '{mark}'."))
                continue
            
            # If cell has "A" or "J" and we'd write "F", skip (presença/justificativa prevalece sobre falta)
            if cell_value in ("A", "J") and mark == "F":
                results.append((matricula, "IGNORADO", f"Presença/Justificativa já registrada ({cell_value}) — falta ignorada."))
                continue
            
            # If cell has "A" and we'd write "J", skip (presença prevalece sobre justificativa)
            if cell_value == "A" and mark == "J":
                results.append((matricula, "IGNORADO", "Alimentação já registrada — justificativa ignorada."))
                continue

            # Update in-memory cell
            current_row[col_index_date] = mark
            sheet_updated = True
            results.append((matricula, "ATUALIZADO", f"Status '{mark}' marcado."))

        # 3. Always clean matrix gaps and re-enforce/repair total formulas for all rows in matrix
        gaps_cleaned = self._clean_matrix_gaps(matrix)
        formulas_repaired = self._reenforce_total_formulas(matrix, valor_diario_vt=valor_diario_vt)

        # Write the entire updated matrix back in a single API call if any updates occurred
        if sheet_updated or gaps_cleaned or formulas_repaired:
            try:
                write_body = {"values": matrix}
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=write_body
                ).execute()
                app_logger.info(f"Batch Sincronização: Gravado com sucesso na aba {tab_name}.")

                # Dynamically restyle Terceirizadas header rows so colors ALWAYS follow the actual text position
                sheet_id = self.get_sheet_id(spreadsheet_id, tab_name)
                if sheet_id is not None:
                    self.restyle_terceirizadas_headers(spreadsheet_id, sheet_id, matrix)
            except Exception as e:
                # If the batch write fails, all updates fail
                return [(emp.get("matricula", ""), "PENDENTE", f"Falha na gravação em lote: {str(e)}") for emp in employees]

        return results

    def ensure_tab_exists(
        self,
        spreadsheet_id: str,
        tab_name: str,
        year: int,
        month: int,
        obra_name: str = "",
        valor_diario_vt: Optional[float] = None
    ) -> tuple[bool, bool]:
        """
        Verifies if a tab with tab_name exists in the spreadsheet.
        If it doesn't, creates it, copies employee list (Matrícula/Nome) from the first sheet or DB,
        and initializes headers with all the calendar days of the month.
        Returns: (success: bool, tab_was_created: bool)
        """
        if not self.is_configured():
            app_logger.info(f"[MOCK] Checked/Created tab '{tab_name}' in spreadsheet {spreadsheet_id}")
            return True, False

        try:
            # 1. Fetch metadata to get list of sheets
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            existing_tabs = [s.get('properties', {}).get('title') for s in sheets]
            if tab_name in existing_tabs:
                app_logger.info(f"Tab '{tab_name}' already exists in spreadsheet {spreadsheet_id}.")
                return True, False

            app_logger.info(f"Tab '{tab_name}' not found. Creating automatically...")

            # 2. Add new sheet
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': tab_name
                            }
                        }
                    }
                ]
            }
            add_sheet_res = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            new_sheet_prop = add_sheet_res.get('replies', [{}])[0].get('addSheet', {}).get('properties', {})
            sheet_id = new_sheet_prop.get('sheetId')
            app_logger.info(f"Tab '{tab_name}' successfully created with ID {sheet_id}.")

            # 3. Read employee list from first sheet as master reference
            employees = []
            if existing_tabs:
                first_sheet_name = existing_tabs[0]
                # Read columns A (Matricula) and B (Nome) up to 250 rows
                range_to_read = f"'{first_sheet_name}'!A1:B250"
                first_sheet_values = self.read_sheet_values(spreadsheet_id, range_to_read)
                
                # Identify header index for master sheet read
                master_header_idx = 0
                if first_sheet_values and len(first_sheet_values) > 1 and any("matricula" in str(c).lower() for c in first_sheet_values[1]):
                    master_header_idx = 1
                
                if first_sheet_values and len(first_sheet_values) > (master_header_idx + 1):
                    for row in first_sheet_values[master_header_idx + 1:]:
                        if row and len(row) >= 1:
                            mat = str(row[0]).strip()
                            name = str(row[1]).strip() if len(row) > 1 else ""
                            # Stop if we reach Terceirizadas section in existing tab
                            if any("terceirizadas" in str(cell).lower() for cell in row):
                                break
                            if mat or name:
                                # Skip header labels
                                if mat.lower() in ("matricula", "matrícula", "nome", "funcionário", "funcionario"):
                                    continue
                                employees.append([mat, name])

            # Fallback: query active db colaboradores for this obra if no employees found in master sheet
            if not employees and obra_name:
                try:
                    from app.database.session import SessionLocal
                    from app.models.obra import Obra
                    from app.models.colaborador import Colaborador
                    db_sess = SessionLocal()
                    o_db = db_sess.query(Obra).filter(Obra.nome.ilike(f"%{obra_name}%")).first()
                    if o_db:
                        c_list = db_sess.query(Colaborador).filter(Colaborador.obra_id == o_db.id, Colaborador.status == "ATIVO").all()
                        employees = [[c.matricula, c.nome] for c in c_list]
                    db_sess.close()
                except Exception as e_db:
                    app_logger.warning(f"Could not fetch colaboradores fallback: {str(e_db)}")

            # 4. Generate calendar dates for the month (Only Day Numbers)
            import calendar
            num_days = calendar.monthrange(year, month)[1]
            month_dates = [str(day) for day in range(1, num_days + 1)]

            # Calculate total columns and formula letter coordinates
            # Col A (0): Matricula, Col B (1): Nome
            # Col C (2) to (1 + num_days): Days 1..num_days
            # Col (2 + num_days): Dias Totais / Valor VT, Col (3 + num_days): Faltas Totais
            start_day_col = "C"
            end_day_col = self.get_column_letter(1 + num_days)
            total_cols = num_days + 4

            # 5. Build full initialization data matrix
            months = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            month_name = months.get(month, "")
            obra_display = obra_name if obra_name else "GERAL"

            if valor_diario_vt and valor_diario_vt > 0:
                title_text = f"  CONTROLE DE VT - OBRA: {obra_display.upper()} - PERÍODO: {month_name.upper()} DE {year}"
            else:
                title_text = f"  CONTROLE DE PRESENÇA - OBRA: {obra_display.upper()} - PERÍODO: {month_name.upper()} DE {year}"
            
            title_row = [title_text] + [""] * (total_cols - 1)
            header_row = ["Matricula", "Nome"] + month_dates + ["Dias Totais", "Faltas Totais"]
            
            new_sheet_data = [title_row, header_row]

            # Fit exact number of colaborador slots so TERCEIRIZADAS section follows right after without empty gaps
            num_colab_slots = max(len(employees), 1)
            for i in range(num_colab_slots):
                r = len(new_sheet_data) + 1  # 1-indexed row number in Google Sheets
                if valor_diario_vt and valor_diario_vt > 0:
                    formula_dias = f'=CONT.SE({start_day_col}{r}:{end_day_col}{r}; "A") * {valor_diario_vt}'
                else:
                    formula_dias = f'=CONT.SE({start_day_col}{r}:{end_day_col}{r}; "A")'

                formula_faltas = f'=CONT.SE({start_day_col}{r}:{end_day_col}{r}; "F")'
                
                if i < len(employees):
                    new_sheet_data.append(employees[i] + [""] * num_days + [formula_dias, formula_faltas])
                else:
                    new_sheet_data.append(["", ""] + [""] * num_days + [formula_dias, formula_faltas])

            # Add Terceirizadas section
            # 1. Separator blank row
            new_sheet_data.append([""] * total_cols)
            
            # 2. TERCEIRIZADAS section header row
            new_sheet_data.append(["  TERCEIRIZADAS (ALIMENTAÇÃO MANUAL)"] + [""] * (total_cols - 1))

            # 3. Terceirizadas table sub-header row
            new_sheet_data.append(["Empresa / Terceirizada", ""] + month_dates + ["Dias Totais", "Faltas Totais"])

            # 4. 15 pre-formatted blank rows for manual entry of Terceirizadas
            for _ in range(15):
                r = len(new_sheet_data) + 1
                if valor_diario_vt and valor_diario_vt > 0:
                    formula_dias = f'=SOMA({start_day_col}{r}:{end_day_col}{r}) * {valor_diario_vt}'
                else:
                    formula_dias = f'=SOMA({start_day_col}{r}:{end_day_col}{r})'
                formula_faltas = ""
                new_sheet_data.append(["", ""] + [""] * num_days + [formula_dias, formula_faltas])

            # 6. Write values to newly created tab
            write_range = f"'{tab_name}'!A1:AZ250"
            write_body = {"values": new_sheet_data}
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=write_range,
                valueInputOption="USER_ENTERED",
                body=write_body
            ).execute()
            app_logger.info(f"Successfully initialized tab '{tab_name}' with {len(employees)} employees and Terceirizadas section.")

            # Dynamically locate Terceirizadas section header and sub-header row indices in new_sheet_data
            terc_sec_row_idx = 28
            terc_header_row_idx = 29
            for idx, r in enumerate(new_sheet_data):
                if r:
                    row_str = " ".join([str(c).strip().lower() for c in r[:2] if c])
                    if "terceirizadas" in row_str:
                        terc_sec_row_idx = idx
                    elif "empresa / terceirizada" in row_str or "nome / terceirizada" in row_str:
                        terc_header_row_idx = idx

            # 7. Apply styling requests
            if sheet_id is not None:
                style_requests = [
                    # 1. Freeze 2 rows (Title + Header) and 2 columns (Matricula + Nome)
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "gridProperties": {
                                    "frozenRowCount": 2,
                                    "frozenColumnCount": 2
                                }
                            },
                            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
                        }
                    },
                    # 2. Column widths: Matricula (90px), Nome (220px), Days (45px), Dias Totais (85px), Faltas Totais (85px)
                    {
                        "updateDimensionProperties": {
                            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                            "properties": {"pixelSize": 90},
                            "fields": "pixelSize"
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                            "properties": {"pixelSize": 220},
                            "fields": "pixelSize"
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": num_days + 2},
                            "properties": {"pixelSize": 45},
                            "fields": "pixelSize"
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": num_days + 2, "endIndex": num_days + 3},
                            "properties": {"pixelSize": 85},
                            "fields": "pixelSize"
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": num_days + 3, "endIndex": num_days + 4},
                            "properties": {"pixelSize": 85},
                            "fields": "pixelSize"
                        }
                    },
                    # 5. General Cell Alignments across rows 2 to 500 (Applied FIRST)
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 0, "endColumnIndex": 1},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 10}}},
                            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 1, "endColumnIndex": 2},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 10}}},
                            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": num_days + 2},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 10}}},
                            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": num_days + 2, "endColumnIndex": num_days + 4},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 10, "bold": True}}},
                            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,textFormat)"
                        }
                    },
                    # 6. Format Title Row 1 (Row index 0): Dark Navy Blue background, white bold text
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": total_cols},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.06, "green": 0.23, "blue": 0.44},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 12, "fontFamily": "Arial"},
                                    "horizontalAlignment": "LEFT",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    # 7. Format Main Header Row 2 (Row index 1): Google Blue for Days, Dark Green for Dias Totais, Dark Red for Faltas Totais
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": num_days + 2},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.1, "green": 0.45, "blue": 0.91},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10, "fontFamily": "Arial"},
                                    "horizontalAlignment": "CENTER",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": num_days + 2, "endColumnIndex": num_days + 3},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.06, "green": 0.62, "blue": 0.35},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10, "fontFamily": "Arial"},
                                    "horizontalAlignment": "CENTER",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": num_days + 3, "endColumnIndex": num_days + 4},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.85, "green": 0.19, "blue": 0.15},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10, "fontFamily": "Arial"},
                                    "horizontalAlignment": "CENTER",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    # 8. Format TERCEIRIZADAS Section Header Row: Dark Slate background
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": terc_sec_row_idx, "endRowIndex": terc_sec_row_idx + 1, "startColumnIndex": 0, "endColumnIndex": total_cols},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.22, "green": 0.28, "blue": 0.31},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 11, "fontFamily": "Arial"},
                                    "horizontalAlignment": "LEFT",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    # 9. Format TERCEIRIZADAS Sub-Header Row: Slate Blue background for entire row
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet_id, "startRowIndex": terc_header_row_idx, "endRowIndex": terc_header_row_idx + 1, "startColumnIndex": 0, "endColumnIndex": total_cols},
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 0.2, "green": 0.35, "blue": 0.55},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10, "fontFamily": "Arial"},
                                    "horizontalAlignment": "CENTER",
                                    "verticalAlignment": "MIDDLE"
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                        }
                    },
                    # 10. Conditional Format Rule 1: Light Green background for 'A'
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": num_days + 2}],
                                "booleanRule": {
                                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "A"}]},
                                    "format": {
                                        "backgroundColor": {"red": 0.886, "green": 0.941, "blue": 0.851},
                                        "textFormat": {"foregroundColor": {"red": 0.220, "green": 0.341, "blue": 0.137}, "bold": True}
                                    }
                                }
                            },
                            "index": 0
                        }
                    },
                    # 11. Conditional Format Rule 2: Light Red background for 'F'
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": num_days + 2}],
                                "booleanRule": {
                                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "F"}]},
                                    "format": {
                                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902},
                                        "textFormat": {"foregroundColor": {"red": 0.753, "green": 0.0, "blue": 0.0}, "bold": True}
                                    }
                                }
                            },
                            "index": 1
                        }
                    },
                    # 12. Conditional Format Rule 3: Light Blue background for 'J'
                    {
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 500, "startColumnIndex": 2, "endColumnIndex": num_days + 2}],
                                "booleanRule": {
                                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "J"}]},
                                    "format": {
                                        "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.98},
                                        "textFormat": {"foregroundColor": {"red": 0.06, "green": 0.23, "blue": 0.44}, "bold": True}
                                    }
                                }
                            },
                            "index": 2
                        }
                    }
                ]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests": style_requests}
                ).execute()
                app_logger.info("Successfully styled Google Sheet tab with custom colors, conditional coloring, froze rows/cols, and aligned cells.")

            return True, True

        except Exception as e:
            error_logger.exception(f"Error ensuring tab '{tab_name}' exists in spreadsheet {spreadsheet_id}: {str(e)}")
            return False, False

google_sheets_service = GoogleSheetsService()
