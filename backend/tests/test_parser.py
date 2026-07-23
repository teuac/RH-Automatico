import pytest
from app.parser.intelligent_parser import IntelligentParser

def test_parse_txt_correct_format():
    parser = IntelligentParser()
    sample_txt = """
    Obra: Residencial Alfa
    Data: 13/07/2026
    ========================
    001798
    José Carlos
    05:58 11:30 12:30 18:03
    """
    
    result = parser.parse_txt(sample_txt)
    
    assert result.obra_nome == "Residencial Alfa"
    assert result.data == "2026-07-13"
    assert len(result.funcionarios) == 1
    
    emp = result.funcionarios[0]
    assert emp.matricula == "001798"
    assert emp.nome == "José Carlos"
    assert emp.horarios == ["05:58", "11:30", "12:30", "18:03"]

def test_parse_txt_multiple_entries():
    parser = IntelligentParser()
    sample_txt = """
    Obra: Condominio Sol
    Data: 2026-07-13
    
    001798
    José Carlos
    05:58 11:30 12:30 18:03
    
    001799
    Maria Oliveira
    08:00 12:00 13:00 17:00
    """
    
    result = parser.parse_txt(sample_txt)
    
    assert result.obra_nome == "Condominio Sol"
    assert result.data == "2026-07-13"
    assert len(result.funcionarios) == 2
    
    assert result.funcionarios[0].matricula == "001798"
    assert result.funcionarios[1].matricula == "001799"
    assert result.funcionarios[1].nome == "Maria Oliveira"
    assert result.funcionarios[1].horarios == ["08:00", "12:00", "13:00", "17:00"]

def test_sanitize_date_str():
    from app.services.upload_service import sanitize_date_str
    
    assert sanitize_date_str("2026-07-13") == "2026-07-13"
    assert sanitize_date_str("2026-07-13 05:58:00") == "2026-07-13"
    # Should fallback to YYYY-MM-DD when given non-date string
    res = sanitize_date_str("05:58 11:30 12:30 18:03")
    assert len(res) == 10 and res.count("-") == 2

def test_parse_csv_section_header_dates():
    parser = IntelligentParser()
    sample_csv = """Matricula,Nome,Horarios
867,Mariana Cardoso dos Santos,07:00 11:59 11:59
,,02/06/2026
731,Djalma Francisco Pereira,06:47 06:47 12:00 13:00
776,Gilson Santos,06:58 06:58 12:00 13:00
"""
    result = parser.parse_csv(sample_csv)
    
    assert len(result.funcionarios) == 3
    assert result.funcionarios[0].matricula == "867"
    
    # Djalma and Gilson appear after 02/06/2026 date header
    assert result.funcionarios[1].matricula == "731"
    assert result.funcionarios[1].data == "2026-06-02"
    
    assert result.funcionarios[2].matricula == "776"
    assert result.funcionarios[2].data == "2026-06-02"
