from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.repositories.base import BaseRepository
from app.models.user import User
from app.models.role import Role

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).filter(User.email == email).first()

    def get_users_with_roles(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).options(joinedload(User.roles)).offset(skip).limit(limit).all()

    def create_pending_user(self, db: Session, email: str, full_name: str, picture_url: Optional[str] = None) -> User:
        """Create a user. First user gets ATIVO & Administrador, others get PENDENTE & Consulta."""
        is_first = db.query(User).count() == 0
        status_val = "ATIVO" if is_first else "PENDENTE"
        
        user = User(
            email=email,
            full_name=full_name,
            picture_url=picture_url,
            status=status_val,
            is_active=True
        )
        db.add(user)
        
        if is_first:
            admin_role = db.query(Role).filter(Role.name == "Administrador").first()
            if admin_role:
                user.roles.append(admin_role)
        else:
            consulta_role = db.query(Role).filter(Role.name == "Consulta").first()
            if consulta_role:
                user.roles.append(consulta_role)
                
        db.commit()
        db.refresh(user)
        return user

    def update_user_status(self, db: Session, user: User, status: str) -> User:
        user.status = status
        db.commit()
        db.refresh(user)
        return user

    def set_user_roles(self, db: Session, user: User, role_names: List[str]) -> User:
        # Clear existing roles
        user.roles.clear()
        # Find new roles
        roles = db.query(Role).filter(Role.name.in_(role_names)).all()
        user.roles.extend(roles)
        db.commit()
        db.refresh(user)
        return user

user_repository = UserRepository()
