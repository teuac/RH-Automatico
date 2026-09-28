import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base


class Contratacao(Base):
    __tablename__ = "contratacoes"

    id = Column(Integer, primary_key=True, index=True)
    nome_candidato = Column(String(255), nullable=False)
    cargo = Column(String(150), nullable=False)
    telefone = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="PENDENTE", nullable=False)  # 'PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDO', 'INTERROMPIDO_HUMANO', 'REJEITADO'
    motivo_rejeicao = Column(Text, nullable=True)
    current_step = Column(Integer, default=0, nullable=False)

    # Coleta de dados de perguntas adicionais
    possui_dependentes_14 = Column(String(100), nullable=True)
    optante_vt = Column(String(100), nullable=True)
    dados_bancarios = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # Relationships
    documentos = relationship("ContratacaoDocumento", back_populates="contratacao", cascade="all, delete-orphan")
    mensagens = relationship("ContratacaoMensagem", back_populates="contratacao", cascade="all, delete-orphan")


class ContratacaoDocumento(Base):
    __tablename__ = "contratacao_documentos"

    id = Column(Integer, primary_key=True, index=True)
    contratacao_id = Column(Integer, ForeignKey("contratacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_documento = Column(String(100), nullable=False)  # 'RG_FRENTE', 'RG_VERSO', 'CARTEIRA_TRABALHO', etc.
    file_path = Column(String(500), nullable=True)

    # Resultados de validação da IA
    qualidade_valida = Column(Boolean, nullable=True)
    validade_valida = Column(Boolean, nullable=True)
    legitimidade_valida = Column(Boolean, nullable=True)
    ocr_status = Column(String(50), default="PENDENTE", nullable=False)  # 'PENDENTE', 'APROVADO', 'REJEITADO'
    feedback_recusa = Column(Text, nullable=True)
    extracted_data = Column(Text, nullable=True)  # JSON em formato string

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    contratacao = relationship("Contratacao", back_populates="documentos")


class ContratacaoMensagem(Base):
    __tablename__ = "contratacao_mensagens"

    id = Column(Integer, primary_key=True, index=True)
    contratacao_id = Column(Integer, ForeignKey("contratacoes.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)  # 'BOT', 'RH', 'CANDIDATO'
    text = Column(Text, nullable=True)
    type = Column(String(50), default="text", nullable=False)  # 'text', 'image', 'document'
    media_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    contratacao = relationship("Contratacao", back_populates="mensagens")
