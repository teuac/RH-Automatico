from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.role import role_permissions

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'upload:import', 'obras:write', etc.
    description = Column(String(255), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
