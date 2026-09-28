from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging, json


from app.database.session import get_db
from app.models.contratacao import Contratacao
from app.schemas.contratacao import ContratacaoCreate, ContratacaoResponse
from app.services.onboarding_service import onboarding_service
from app.services.document_service import document_service
from app.auth.rbac import RoleChecker
from app.models.user import User

logger = logging.getLogger("app")

router = APIRouter(prefix="/contratacoes", tags=["Contratações e Onboarding"])

ADMIN_RH = ["Administrador", "RH"]
ALL_ROLES = ["Administrador", "RH", "Consulta"]

@router.get("/", response_model=List[ContratacaoResponse], dependencies=[Depends(RoleChecker(ALL_ROLES))])
def list_contratacoes(db: Session = Depends(get_db)):
    """Lists all hiring processes in the system."""
    return db.query(Contratacao).order_by(Contratacao.created_at.desc()).all()

@router.get("/{id}", response_model=ContratacaoResponse, dependencies=[Depends(RoleChecker(ALL_ROLES))])
def get_contratacao(id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information for a single hiring process."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo de contratação não encontrado.")
    return item

@router.post("/", response_model=ContratacaoResponse, dependencies=[Depends(RoleChecker(ADMIN_RH))])
def create_contratacao(payload: ContratacaoCreate, db: Session = Depends(get_db)):
    """Registers a new candidate onboarding process."""
    # Check if number already has an active process
    existing = db.query(Contratacao).filter(
        Contratacao.telefone == payload.telefone,
        Contratacao.status.in_(["PENDENTE", "EM_ANDAMENTO"])
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Já existe um processo de contratação em andamento para este número."
        )

    item = Contratacao(
        nome_candidato=payload.nome_candidato,
        cargo=payload.cargo,
        telefone=payload.telefone,
        status="PENDENTE",
        current_step=0
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{id}", dependencies=[Depends(RoleChecker(ADMIN_RH))])
def delete_contratacao(id: int, db: Session = Depends(get_db)):
    """Deletes an onboarding record from the database."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    db.delete(item)
    db.commit()
    return {"detail": "Processo excluído com sucesso."}

@router.post("/{id}/start", dependencies=[Depends(RoleChecker(ADMIN_RH))])
def start_onboarding(id: int, request: Request, db: Session = Depends(get_db)):
    """Triggers initial contact and begins WhatsApp document collection."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    
    current_user = request.state.user if hasattr(request.state, "user") else None
    user_name = current_user.full_name if current_user else "Recrutador RH"

    success = onboarding_service.start_workflow(db, item, user_name)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao iniciar contato via WhatsApp. Verifique as credenciais da Evolution API.")

    return {"detail": "Workflow de contratação iniciado com sucesso."}

@router.post("/{id}/pause", dependencies=[Depends(RoleChecker(ADMIN_RH))])
def pause_onboarding(id: int, db: Session = Depends(get_db)):
    """Pauses conversation state machine for manual takeover."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    onboarding_service.pause_workflow(db, item)
    return {"detail": "Workflow interrompido. Atendimento em modo manual."}

@router.post("/{id}/resume", dependencies=[Depends(RoleChecker(ADMIN_RH))])
def resume_onboarding(id: int, db: Session = Depends(get_db)):
    """Resumes onboarding state machine from the last pending step."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    
    success = onboarding_service.resume_workflow(db, item)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao enviar mensagem de retomada.")
        
    return {"detail": "Workflow retomado com sucesso."}

@router.get("/{id}/download", dependencies=[Depends(RoleChecker(ALL_ROLES))])
def download_documents(id: int, db: Session = Depends(get_db)):
    """Downloads ZIP with all collected document files plus the merged PDF summary."""
    item = db.query(Contratacao).filter(Contratacao.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Processo não encontrado.")
    
    zip_stream = document_service.generate_hiring_zip(db, item)
    filename = f"contratacao_{item.nome_candidato.replace(' ', '_')}_{item.id}.zip"
    
    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def log_debug_webhook(msg: str):
    try:
        import datetime
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass

@router.post("/webhook")
async def webhook_receiver(request: Request, db: Session = Depends(get_db)):
    """Evolution API Webhook receiver to capture candidate interactions."""
    try:
        body = await request.json()
        log_debug_webhook(f"RECEIVED WEBHOOK. Event: {body.get('event')}. Body: {json.dumps(body)}")
        logger.info(f"Evolution API webhook received. Event: {body.get('event')}. Body: {json.dumps(body)}")
    except Exception as e:
        logger.error(f"Error parsing webhook body JSON: {str(e)}")
        log_debug_webhook(f"ERROR PARSING JSON: {str(e)}")
        return Response(status_code=400, content="Invalid JSON payload")

    event = body.get("event")
    # We only process message upsert events
    if event != "messages.upsert":
        log_debug_webhook(f"IGNORED: Event is not messages.upsert (was '{event}')")
        logger.info(f"Webhook ignored: event is not messages.upsert (was '{event}')")
        return {"status": "ignored_event", "event": event}

    data = body.get("data")
    if not data:
        log_debug_webhook("IGNORED: Payload has no 'data' object")
        logger.warning("Webhook ignored: payload has no 'data' object")
        return {"status": "no_data"}

    key = data.get("key", {})
    from_me = key.get("fromMe", False)
    
    # Ignore messages sent by ourselves/the bot to prevent loops
    if from_me:
        log_debug_webhook("IGNORED: Message is fromMe=True (sent by bot itself)")
        logger.info("Webhook ignored: message sent by the bot (fromMe=True)")
        return {"status": "ignored_bot_message"}

    remote_jid = key.get("remoteJid", "")
    if "@g.us" in remote_jid:
        log_debug_webhook(f"IGNORED: Group chat message from remoteJid {remote_jid}")
        logger.info(f"Webhook ignored: group chat message from remoteJid {remote_jid}")
        return {"status": "ignored_group_message"}
        
    phone = remote_jid.split("@")[0] # Extract digits from e.g. "557999999999@s.whatsapp.net"
    
    msg_type = data.get("messageType")
    message_content = data.get("message", {})

    text_msg = None
    media_msg = None

    if msg_type == "conversation":
        text_msg = message_content.get("conversation")
    elif msg_type == "extendedTextMessage":
        text_msg = message_content.get("extendedTextMessage", {}).get("text")
    elif msg_type in ("imageMessage", "documentMessage"):
        media_obj = message_content.get(msg_type, {})
        media_msg = {
            "messageId": key.get("id"),
            "remoteJid": remote_jid,
            "mimeType": media_obj.get("mimetype"),
            "url": media_obj.get("url")
        }
    elif msg_type in ("buttonsResponseMessage", "templateButtonReplyMessage"):
        btn_obj = message_content.get(msg_type, {})
        text_msg = btn_obj.get("selectedDisplayText") or btn_obj.get("selectedId")
    else:
        # Check if conversation is nested
        if "conversation" in message_content:
            text_msg = message_content.get("conversation")
        elif "extendedTextMessage" in message_content:
            text_msg = message_content.get("extendedTextMessage", {}).get("text")

    log_debug_webhook(f"PARSED: phone={phone}, msg_type={msg_type}, text_msg='{text_msg}', media={bool(media_msg)}")
    logger.info(f"Parsed webhook details: phone={phone}, msg_type={msg_type}, text_msg={text_msg}, media={bool(media_msg)}")

    if text_msg or media_msg:
        # Process response in workflow state machine
        try:
            onboarding_service.process_incoming_message(
                db=db,
                phone=phone,
                text=text_msg,
                media_data=media_msg
            )
            log_debug_webhook("PROCESSED: State machine finished execution successfully.")
        except Exception as sm_err:
            log_debug_webhook(f"ERROR IN STATE MACHINE: {str(sm_err)}")
            logger.error(f"Error executing state machine: {str(sm_err)}")
        return {"status": "processed"}

    log_debug_webhook(f"IGNORED: Unable to extract text or media from type {msg_type}")
    logger.warning(f"Webhook ignored: unable to extract text or media from message content. Type was: {msg_type}")
    return {"status": "ignored_type", "type": msg_type}
