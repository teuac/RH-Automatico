import pytest
from unittest.mock import MagicMock
from app.google.sheets_service import GoogleSheetsService

def test_get_column_letter():
    service = GoogleSheetsService()
    assert service.get_column_letter(0) == "A"
    assert service.get_column_letter(1) == "B"
    assert service.get_column_letter(2) == "C"
    assert service.get_column_letter(32) == "AG"
    assert service.get_column_letter(33) == "AH"

def test_get_day_range_cols():
    service = GoogleSheetsService()
    headers = ["Matricula", "Nome"] + [str(d) for d in range(1, 32)] + ["Dias Totais", "Faltas Totais"]
    start_col, end_col, num_days = service._get_day_range_cols(headers)
    assert start_col == "C"
    assert end_col == "AG"
    assert num_days == 31

def test_ensure_tab_exists_builds_correct_matrix_and_styles():
    service = GoogleSheetsService()
    service.service = MagicMock()

    # Mock metadata: sheet does not exist initially
    service.service.spreadsheets().get().execute.return_value = {
        "sheets": [
            {
                "properties": {
                    "title": "Aba Antiga"
                }
            }
        ]
    }

    # Mock addSheet batchUpdate reply
    service.service.spreadsheets().batchUpdate().execute.return_value = {
        "replies": [
            {
                "addSheet": {
                    "properties": {
                        "sheetId": 12345
                    }
                }
            }
        ]
    }

    # Mock reading first sheet for master employee list
    service.service.spreadsheets().values().get().execute.return_value = {
        "values": [
            ["Matricula", "Nome"],
            ["001", "João Silva"],
            ["002", "Maria Santos"]
        ]
    }

    success, created = service.ensure_tab_exists(
        spreadsheet_id="dummy_id",
        tab_name="Julho 2026",
        year=2026,
        month=7,
        obra_name="OBRA TESTE"
    )

    assert success is True
    assert created is True

    # Inspect update call for values written
    update_calls = service.service.spreadsheets().values().update.call_args_list
    assert len(update_calls) > 0

    written_body = update_calls[0][1]["body"]["values"]

    # Row 0: Title
    assert "CONTROLE DE PRESENÇA" in written_body[0][0]
    
    # Row 1: Headers
    headers = written_body[1]
    assert headers[0] == "Matricula"
    assert headers[1] == "Nome"
    assert headers[2] == "1"
    assert headers[32] == "31"
    assert headers[33] == "Dias Totais"
    assert headers[34] == "Faltas Totais"

    # Employee rows: João Silva (Row 3), Maria Santos (Row 4)
    assert written_body[2][0] == "001"
    assert written_body[2][1] == "João Silva"
    assert written_body[2][-2] == '=CONT.SE(C3:AG3; "A")'
    assert written_body[2][-1] == '=CONT.SE(C3:AG3; "F")'

    assert written_body[3][0] == "002"
    assert written_body[3][1] == "Maria Santos"
    assert written_body[3][-2] == '=CONT.SE(C4:AG4; "A")'
    assert written_body[3][-1] == '=CONT.SE(C4:AG4; "F")'

    # Separator row (Row 28, index 27)
    assert all(cell == "" for cell in written_body[27])

    # Terceirizadas Section Header row (Row 29, index 28)
    assert "TERCEIRIZADAS" in written_body[28][0]

    # Terceirizadas Table Sub-Header row (Row 30, index 29)
    assert written_body[29][0] == "Empresa / Terceirizada"
    assert written_body[29][-2] == "Dias Totais"
    assert written_body[29][-1] == "Faltas Totais"

    # Check Terceirizadas blank rows have formula (Row 31 is first blank terceirizada row, index 30)
    assert written_body[30][-2] == '=SOMA(C31:AG31)'
    assert written_body[30][-1] == ''

    # Check batchUpdate style requests from mock return value
    mock_batch = service.service.spreadsheets.return_value.batchUpdate
    assert mock_batch.call_count >= 2

    # Find the call containing requests
    style_requests = None
    for call in mock_batch.call_args_list:
        body = call.kwargs.get("body", {}) if hasattr(call, 'kwargs') and "body" in call.kwargs else (call[1].get("body", {}) if len(call) > 1 and isinstance(call[1], dict) else {})
        if "requests" in body and any("addConditionalFormatRule" in req for req in body["requests"]):
            style_requests = body["requests"]
            break

    assert style_requests is not None

    # Verify conditional format rule for 'A' (Green)
    cond_rules = [r for r in style_requests if "addConditionalFormatRule" in r]
    assert len(cond_rules) == 3

    rule_a = cond_rules[0]["addConditionalFormatRule"]["rule"]
    assert rule_a["booleanRule"]["condition"]["values"][0]["userEnteredValue"] == "A"
    assert rule_a["booleanRule"]["format"]["backgroundColor"]["green"] == 0.941
