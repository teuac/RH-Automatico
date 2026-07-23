import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id = Column(Integer, primary_key=True, index=True)
    matricula = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(255), nullable=False, index=True)
    funcao = Column(String(150), nullable=True)
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="ATIVO", nullable=False)  # 'ATIVO', 'INATIVO'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    obra = relationship("Obra", back_populates="colaboradores")
    atestados = relationship("Atestado", back_populates="colaborador", cascade="all, delete-orphan")
