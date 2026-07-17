import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base

class Obra(Base):
    __tablename__ = "obras"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default="ATIVO", nullable=False)  # 'ATIVO', 'INATIVO'
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    uploads = relationship("Upload", back_populates="obra")
    planilhas = relationship("Planilha", back_populates="obra", cascade="all, delete-orphan")
