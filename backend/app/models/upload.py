import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.session import Base

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    obra_id = Column(Integer, ForeignKey("obras.id", ondelete="CASCADE"), nullable=False)
    planilha_id = Column(Integer, ForeignKey("planilhas.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    
    # Process stats
    total_employees = Column(Integer, default=0, nullable=False)
    updated_count = Column(Integer, default=0, nullable=False)
    ignored_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)
    processing_time_ms = Column(Float, default=0.0, nullable=False)  # Milliseconds
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="uploads")
    obra = relationship("Obra", back_populates="uploads")
    planilha = relationship("Planilha", back_populates="uploads")
    pending_records = relationship("PendingRecord", back_populates="upload", cascade="all, delete-orphan")
