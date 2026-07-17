import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class Planilha(Base):
    __tablename__ = "planilhas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False, index=True)
    planilha_google_id = Column(String(255), nullable=False)
    nome_aba = Column(String(100), nullable=False)
    automacao = Column(String(100), default="ALIMENTACAO", nullable=False)  # 'ALIMENTACAO', 'CONTROLE_VT'
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50), default="ATIVO", nullable=False)  # 'ATIVO', 'INATIVO'
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    obra = relationship("Obra", back_populates="planilhas")
    uploads = relationship("Upload", back_populates="planilha")
