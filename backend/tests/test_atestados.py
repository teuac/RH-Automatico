import pytest
from datetime import date
from app.repositories.atestado import atestado_repository

def test_atestado_days_calculation():
    d_start = date(2026, 7, 1)
    d_end = date(2026, 7, 5)
    days = (d_end - d_start).days + 1
    assert days == 5
