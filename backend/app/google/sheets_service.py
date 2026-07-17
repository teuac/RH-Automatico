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
        """Loads Service Account credentials from env string or local file"""
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        try:
            # 1. Try loading from GOOGLE_SERVICE_ACCOUNT_INFO JSON string
            if settings.GOOGLE_SERVICE_ACCOUNT_INFO:
                info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_INFO)
                self.creds = service_account.Credentials.from_service_account_info(
                    info, scopes=scopes
                )
                self.service = build("sheets", "v4", credentials=self.creds)
                app_logger.info("Google Sheets API service successfully initialized from GOOGLE_SERVICE_ACCOUNT_INFO env.")
                return

            # 2. Fall back to local credentials file path
            file_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if os.path.exists(file_path):
                self.creds = service_account.Credentials.from_service_account_file(
                    file_path, scopes=scopes
                )
                self.service = build("sheets", "v4", credentials=self.creds)
                app_logger.info(f"Google Sheets API service successfully initialized from file: {file_path}")
                return

            app_logger.warning(
                "Google Service Account credentials not found in env variable or credentials file. "
                "Google Sheets updates will be skipped or mocked in development."
            )
        except Exception as e:
            error_logger.exception(f"Failed to initialize Google Sheets service: {str(e)}")

    def is_configured(self) -> bool:
        return self.service is not None

    def read_sheet_values(self, spreadsheet_id: str, range_name: str) -> Optional[List[List]]:
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
            result = sheet.values().get(spreadsheet_id=spreadsheet_id, range=range_name).execute()
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
                spreadsheet_id=spreadsheet_id,
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
        date_str: str,  # format YYYY-MM-DD or DD/MM/YYYY
        matricula: str,
        employee_name: str
    ) -> Tuple[str, str]:
        """
        Syncs presence for a single employee.
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

        if not values or len(values) < 2:
            return "PENDENTE", "Planilha vazia ou sem cabeçalhos."

        # Parse date formats to find date column
        # Date formats inside sheets could be DD/MM/YYYY or YYYY-MM-DD or DD/MM
        # Standardize date_str to dd/mm/yyyy
        # date_str is YYYY-MM-DD
        date_parts = date_str.split("-")
        dd_mm_yyyy = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}" if len(date_parts) == 3 else date_str
        dd_mm = f"{date_parts[2]}/{date_parts[1]}" if len(date_parts) == 3 else date_str

        headers = [str(cell).strip() for cell in values[0]]
        
        col_index_date = -1
        for idx, header in enumerate(headers):
            if header == date_str or header == dd_mm_yyyy or header == dd_mm:
                col_index_date = idx
                break

        if col_index_date == -1:
            return "PENDENTE", f"Coluna referente à data {dd_mm_yyyy} não foi localizada."

        # Find employee row
        # Check first columns for matricula or name matching
        row_index_employee = -1
        
        for idx, row in enumerate(values[1:], start=2): # 1-based indexing for row number, since values[0] is row 1
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
            if employee_name.lower() in row_name.lower() or row_name.lower() in employee_name.lower():
                row_index_employee = idx
                # Keep searching to see if a better matricula matches, but hold this as fallback

        if row_index_employee == -1:
            return "PENDENTE", f"Funcionário {employee_name} ({matricula}) não localizado na planilha."

        # Check if already marked
        current_row_data = values[row_index_employee - 1]
        if col_index_date < len(current_row_data):
            cell_value = str(current_row_data[col_index_date]).strip().upper()
            if cell_value == "A":
                return "IGNORADO", "Já registrado alimentação ('A')."

        # Update the cell to 'A'
        success = self.update_cell(spreadsheet_id, tab_name, row_index_employee, col_index_date, "A")
        if success:
            return "ATUALIZADO", f"Alimentação registrada na linha {row_index_employee} col {self.get_column_letter(col_index_date)}."
        else:
            return "PENDENTE", "Falha ao gravar alimentação na planilha."

google_sheets_service = GoogleSheetsService()
