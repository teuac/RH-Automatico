import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Date and Time stored separately as requested
    action_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    action_time = Column(String(8), nullable=False)   # HH:MM:SS
    
    module = Column(String(100), nullable=False, index=True)  # e.g., 'Upload', 'Configuracao'
    screen = Column(String(100), nullable=False)  # e.g., 'Obras', 'Usuarios'
    action = Column(String(100), nullable=False, index=True)  # e.g., 'IMPORT', 'CREATE', 'UPDATE'
    description = Column(Text, nullable=True)
    
    object_changed = Column(String(100), nullable=True)  # e.g., 'users', 'obras'
    object_id = Column(String(100), nullable=True)
    result = Column(String(50), nullable=False)  # 'SUCESSO', 'ERRO'
    
    before_state = Column(Text, nullable=True)  # JSON dump of before state
    after_state = Column(Text, nullable=True)   # JSON dump of after state
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")
