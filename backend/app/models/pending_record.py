import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class PendingRecord(Base):
    __tablename__ = "pending_records"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    
    employee_id = Column(String(50), nullable=True)  # Registration number, e.g. "001798"
    employee_name = Column(String(255), nullable=False)
    date = Column(String(50), nullable=False)  # YYYY-MM-DD or date string
    times = Column(String(255), nullable=True)  # e.g., "05:58 11:30 12:30 18:03"
    
    status = Column(String(50), default="PENDENTE", nullable=False)  # 'PENDENTE', 'RESOLVIDO', 'IGNORADO'
    reason = Column(Text, nullable=True)  # Why it's pending (e.g. "Não cadastrado na planilha")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    upload = relationship("Upload", back_populates="pending_records")
