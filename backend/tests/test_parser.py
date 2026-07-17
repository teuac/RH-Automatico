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
