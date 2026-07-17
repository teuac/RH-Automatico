import json
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.repositories.planilha import planilha_repository
from app.repositories.audit import audit_repository
from app.schemas.planilha import PlanilhaCreate, PlanilhaUpdate, PlanilhaResponse
from app.auth.rbac import get_active_user
from app.models.user import User

class PlanilhaController:
    @staticmethod
    def get_all(db: Session = Depends(get_db), current_user: User = Depends(get_active_user)) -> List[PlanilhaResponse]:
        return planilha_repository.get_multi(db)

    @staticmethod
    def get_by_id(planilha_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)) -> PlanilhaResponse:
        planilha = planilha_repository.get(db, planilha_id)
        if not planilha:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")
        return planilha

    @staticmethod
    def create(
        request: Request,
        payload: PlanilhaCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> PlanilhaResponse:
        data = payload.model_dump()

        # Para ALIMENTACAO: abas criadas automaticamente por mês — nome_aba é opcional
        if data.get('automacao') == 'ALIMENTACAO':
            if not data.get('nome_aba'):
                data['nome_aba'] = 'AUTO'
        else:
            # Para outros tipos, nome_aba é obrigatório
            if not data.get('nome_aba'):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Nome da aba é obrigatório para este tipo de automação."
                )

        planilha = planilha_repository.create(db, data)

        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Planilhas",
            action="CREATE",
            description=f"Cadastrou nova planilha: {planilha.nome} (Automacao: {planilha.automacao})",
            object_changed="planilhas",
            object_id=str(planilha.id),
            result="SUCESSO",
            after_state=json.dumps(data)
        )
        return planilha

    @staticmethod
    def update(
        planilha_id: int,
        request: Request,
        payload: PlanilhaUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ) -> PlanilhaResponse:
        planilha = planilha_repository.get(db, planilha_id)
        if not planilha:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")
            
        before_state = {
            "nome": planilha.nome,
            "planilha_google_id": planilha.planilha_google_id,
            "nome_aba": planilha.nome_aba,
            "status": planilha.status,
            "observacoes": planilha.observacoes
        }
        
        # Update
        updated_data = payload.model_dump(exclude_unset=True)
        updated_planilha = planilha_repository.update(db, planilha, updated_data)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Planilhas",
            action="UPDATE",
            description=f"Atualizou a planilha: {updated_planilha.nome}",
            object_changed="planilhas",
            object_id=str(updated_planilha.id),
            result="SUCESSO",
            before_state=json.dumps(before_state),
            after_state=json.dumps(updated_data)
        )
        return updated_planilha

    @staticmethod
    def delete(
        planilha_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
    ):
        planilha = planilha_repository.get(db, planilha_id)
        if not planilha:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")
            
        before_state = {
            "nome": planilha.nome,
            "planilha_google_id": planilha.planilha_google_id,
            "nome_aba": planilha.nome_aba,
            "status": planilha.status
        }
        
        planilha_repository.remove(db, planilha_id)
        
        # Log Audit Trail
        audit_repository.log(
            db=db,
            user_id=current_user.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            module="Configuracoes",
            screen="Planilhas",
            action="DELETE",
            description=f"Removeu a planilha: {before_state['nome']}",
            object_changed="planilhas",
            object_id=str(planilha_id),
            result="SUCESSO",
            before_state=json.dumps(before_state)
        )
        return {"detail": "Planilha removida com sucesso."}

planilha_controller = PlanilhaController()
