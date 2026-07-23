import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class Atestado(Base):
    __tablename__ = "atestados"

    id = Column(Integer, primary_key=True, index=True)
    colaborador_id = Column(Integer, ForeignKey("colaboradores.id", ondelete="CASCADE"), nullable=False, index=True)
    data_inicio = Column(Date, nullable=False, index=True)
    data_fim = Column(Date, nullable=False, index=True)
    dias = Column(Integer, nullable=False)
    cid = Column(String(100), nullable=True)
    motivo = Column(String(255), nullable=True)
    status = Column(String(50), default="HOMOLOGADO", nullable=False)  # 'HOMOLOGADO', 'PENDENTE', 'CANCELADO'
    observacoes = Column(Text, nullable=True)
    documento_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    colaborador = relationship("Colaborador", back_populates="atestados")
