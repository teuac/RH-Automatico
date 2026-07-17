import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.role import user_roles

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    picture_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="PENDENTE", nullable=False)  # 'PENDENTE', 'ATIVO'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    uploads = relationship("Upload", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
