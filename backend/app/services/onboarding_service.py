import datetime
import os
import json
import logging
import re
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import pypdf

from app.models.contratacao import Contratacao, ContratacaoDocumento, ContratacaoMensagem
from app.services.whatsapp_service import whatsapp_service
from app.repositories.settings import system_settings_repository

logger = logging.getLogger("app")

_reader = None

def get_easyocr_reader():
    global _reader
    if _reader is None:
        import easyocr
        # Initialize easyocr reader for Portuguese, CPU-only
        _reader = easyocr.Reader(['pt'], gpu=False)
    return _reader


# Constants for document validation keys
DOC_TYPES = {
    5: "RG_FRENTE",
    6: "RG_VERSO",
    7: "CARTEIRA_TRABALHO",
    8: "TITULO_ELEITOR",
    9: "CERTIDAO_NASCIMENTO",
    10: "COMPROVANTE_ESCOLARIDADE",
    11: "CARTAO_VACINA"
}

DOC_PROMPTS = {
    5: "Pode me mandar a foto da FRENTE do seu RG?",
    6: "Pode me mandar foto do verso do seu RG?",
    7: "Pode me mandar foto da sua carteira de trabalho?",
    8: "Pode me mandar foto do seu titulo de eleitor?",
    9: "Pode me mandar uma foto da sua certidão de nascimento?",
    10: "Pode me mandar foto do seu comprovante de escolaridade,",
    11: "pode me mandar foto do seu cartão vacina ?"
}

class OnboardingService:
    def _get_greeting(self) -> str:
        """Determines the correct greeting based on local time (UTC-3 typical for Brazil)."""
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        hour = now.hour
        if 5 <= hour < 12:
            return "Bom dia"
        elif 12 <= hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"

    def log_message(self, db: Session, contratacao_id: int, sender: str, text: str, msg_type: str = "text", media_url: Optional[str] = None):
        """Saves a message in the chat logs."""
        msg = ContratacaoMensagem(
            contratacao_id=contratacao_id,
            sender=sender,
            text=text,
            type=msg_type,
            media_url=media_url
        )
        db.add(msg)
        db.commit()

    def start_workflow(self, db: Session, contratacao: Contratacao, user_name: str) -> bool:
        """Starts the hiring workflow on WhatsApp by sending the initial greeting."""
        contratacao.status = "EM_ANDAMENTO"
        contratacao.current_step = 1
        db.commit()

        greeting = self._get_greeting()
        msg_text = (
            f"{greeting}! Me chamo {user_name}, faço parte do RH da AC Engenharia. "
            f"Falo com *{contratacao.nome_candidato}*, que se candidatou à vaga de *{contratacao.cargo}*?"
        )
        
        self.log_message(db, contratacao.id, "BOT", msg_text)
        success = whatsapp_service.send_message(db, contratacao.telefone, msg_text)
        
        # Auto-configure webhook on startup for convenience
        try:
            # Get settings to check if external URL is saved
            url_setting = system_settings_repository.get_by_key(db, "BACKEND_EXTERNAL_URL")
            if url_setting and url_setting.value:
                whatsapp_service.configure_webhook(db, url_setting.value)
        except Exception as e:
            logger.error(f"Error configuring webhook automatically: {str(e)}")

        return bool(success)

    def pause_workflow(self, db: Session, contratacao: Contratacao):
        """Interrupts onboarding flow for manual human intervention."""
        contratacao.status = "INTERROMPIDO_HUMANO"
        db.commit()
        
        info_msg = "[Workflow interrompido pelo RH. Atendimento em modo manual.]"
        self.log_message(db, contratacao.id, "RH", info_msg)

    def resume_workflow(self, db: Session, contratacao: Contratacao) -> bool:
        """Resumes the onboarding workflow from the last pending state."""
        contratacao.status = "EM_ANDAMENTO"
        db.commit()

        # Re-configure webhook to make sure we are listening to the correct ngrok URL
        try:
            url_setting = system_settings_repository.get_by_key(db, "BACKEND_EXTERNAL_URL")
            if url_setting and url_setting.value:
                whatsapp_service.configure_webhook(db, url_setting.value)
        except Exception as e:
            logger.error(f"Error configuring webhook on resume: {str(e)}")

        # Resend the prompt for the current step to resume conversation
        prompt_text = self._get_prompt_for_step(contratacao)
        self.log_message(db, contratacao.id, "BOT", f"[Retomando workflow] {prompt_text}")
        success = whatsapp_service.send_message(db, contratacao.telefone, prompt_text)
        return bool(success)

    def _get_prompt_for_step(self, contratacao: Contratacao) -> str:
        step = contratacao.current_step
        if step == 1:
            return f"Olá! Falo com *{contratacao.nome_candidato}*, que se candidatou à vaga de *{contratacao.cargo}*?"
        elif step == 2:
            return "Você ainda possui interesse na vaga?"
        elif step == 3:
            return "Que bom! Vou precisar de alguns documentos seus para prosseguirmos com a contratação, podemos prosseguir?"
        elif step in DOC_PROMPTS:
            return DOC_PROMPTS[step]
        elif step == 12:
            return "Você possui dependentes menores do que 14 anos?"
        elif step == 13:
            return "Será optante pelo vale transporte(desconto de 4% no salario)?"
        elif step == 14:
            return "pode me informar seus dados bancários ? (Agencia conta e numero)"
        elif step == 15:
            summary = self._generate_summary_text(contratacao)
            return f"{summary}\n\nVocê deseja alterar algum dado? (Responda SIM para alterar ou NÃO para confirmar)"
        elif step == 16:
            return "Qual dado você deseja alterar? Envie uma das seguintes opções: RG Frente, RG Verso, Carteira, Titulo, Certidao, Escolaridade, Vacina, Dependentes, Vale Transporte, Banco"
        return "Olá, em breve entraremos em contato."

    def _generate_summary_text(self, contratacao: Contratacao) -> str:
        return (
            f"*Resumo dos dados coletados:*\n\n"
            f"👤 *Nome:* {contratacao.nome_candidato}\n"
            f"💼 *Cargo:* {contratacao.cargo}\n"
            f"👪 *Dependentes < 14 anos:* {contratacao.possui_dependentes_14 or 'Não'}\n"
            f"🚌 *Optante Vale Transporte:* {contratacao.optante_vt or 'Não'}\n"
            f"🏦 *Dados Bancários:* {contratacao.dados_bancarios or 'Não Informado'}"
        )

    def validate_document_local(self, file_path: str, tipo_doc: str, candidate_name: str) -> Dict[str, Any]:
        """Validates document front/back quality, validity and type via local EasyOCR or PyPDF."""
        extracted_text = ""
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document file not found: {file_path}")
                
            if file_path.lower().endswith(".pdf"):
                # Extract text using PyPDF
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    extracted_text += page.extract_text() or ""
            else:
                # Extract text using EasyOCR
                reader = get_easyocr_reader()
                ocr_results = reader.readtext(file_path)
                extracted_text = " ".join([res[1] for res in ocr_results])
        except Exception as e:
            logger.error(f"Error during local OCR extraction: {str(e)}")
            extracted_text = ""

        # Normalize extracted text for keyword checking
        normalized_text = extracted_text.lower().strip()
        
        # 1. Quality / Legibility Check
        # Legible files should yield at least 12 characters of text.
        qualidade_valida = len(normalized_text) >= 12
        
        # 2. Legitimacy Check (matches Portuguese document keywords / structure)
        keywords = {
            "CARTEIRA_TRABALHO": ["trabalho", "previdencia", "social", "ctps", "ministerio", "mte", "carteira"],
            "TITULO_ELEITOR": ["titulo", "eleitor", "eleitoral", "justica", "zona", "secao", "inscricao"],
            "CERTIDAO_NASCIMENTO": ["certidao", "nascimento", "registro", "civil", "termo", "livro", "folha", "nascido", "cartorio"],
            "COMPROVANTE_ESCOLARIDADE": ["comprovante", "escolaridade", "conclusao", "historico", "diploma", "certificado", "ensino", "escola", "curso", "medio", "declaracao", "colegio", "disciplina"],
            "CARTAO_VACINA": ["vacina", "vacinacao", "cartao", "dose", "covid", "sus", "imunizacao", "dose", "lote", "fabricante"]
        }
        
        legitimidade_valida = False
        
        if tipo_doc == "RG_FRENTE":
            # Frente do RG: Look for Name, CPF, Date of issue, general header, OR signature/digital indicators
            name_parts = [part.lower() for part in candidate_name.split() if len(part) > 3]
            has_name = any(part in normalized_text for part in name_parts)
            has_cpf = bool(re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", extracted_text) or re.search(r"\d{11}", normalized_text))
            has_date = bool(re.search(r"\d{2}/\d{2}/\d{4}", extracted_text))
            
            # Header indicators
            doc_kws = ["carteira", "identidade", "registro", "geral", "ssp", "republica", "federativa", "nacional", "cin", "seguranca"]
            has_doc_kws = any(kw in normalized_text for kw in doc_kws)
            
            # Fingerprint, Signature, or Photo markers
            sig_kws = ["polegar", "assinatura", "digital", "impressao", "foto", "manuscrita", "marca", "direito", "polegar direito", "frente"]
            has_sig = any(kw in normalized_text for kw in sig_kws)
            
            # If it contains header kws, name, cpf, date, or signature/photo indicators
            if has_doc_kws or has_name or has_cpf or has_date or has_sig:
                legitimidade_valida = True
                
        elif tipo_doc == "RG_VERSO":
            # Verso do RG: Search for naturality, parents, birth date, registry terms, SSP, but NO "foto"
            doc_kws = ["registro", "geral", "identidade", "carteira", "ssp", "republica", "federativa", "nascimento", "filiacao", "pai", "mae", "cpf", "naturalidade", "doc", "certidao", "casamento"]
            matches = [kw for kw in doc_kws if kw in normalized_text]
            legitimidade_valida = len(matches) > 0
            
        else:
            doc_kws = keywords.get(tipo_doc, [])
            matches = [kw for kw in doc_kws if kw in normalized_text]
            legitimidade_valida = len(matches) > 0
        
        # 3. Validity Check
        validade_valida = True
        if "cancelado" in normalized_text or "invalido" in normalized_text or "vencido" in normalized_text:
            validade_valida = False
            
        # Overall validity
        valido = qualidade_valida and legitimidade_valida and validade_valida
        
        # Generate feedback messages
        if valido:
            feedback = "Documento verificado e aprovado localmente."
        elif not qualidade_valida:
            feedback = "A imagem enviada parece estar muito desfocada ou sem texto visível. Por favor, envie uma foto mais nítida e bem iluminada."
        elif not legitimidade_valida:
            friendly_name = tipo_doc.replace("_", " ").title()
            feedback = f"O documento enviado não foi reconhecido como um(a) {friendly_name}. Por favor, envie o documento correto."
        else:
            feedback = "O documento enviado foi detectado como inválido, vencido ou cancelado."

        # Extract structured data using regex
        extracted_data = {}
        
        # Check if candidate name (or parts of it) is present in the document
        name_parts = [part.lower() for part in candidate_name.split() if len(part) > 3]
        name_matches = [part for part in name_parts if part in normalized_text]
        if name_matches:
            extracted_data["nome_candidato_confirmado"] = True
            
        # Try extracting CPF
        cpf_match = re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", extracted_text)
        if cpf_match:
            extracted_data["cpf"] = cpf_match.group(0)
            
        # Try extracting dates (birth date, issue date)
        dates = re.findall(r"\d{2}/\d{2}/\d{4}", extracted_text)
        if dates:
            extracted_data["datas_detectadas"] = dates

        return {
            "valido": valido,
            "qualidade_valida": qualidade_valida,
            "validade_valida": validade_valida,
            "legitimidade_valida": legitimidade_valida,
            "feedback": feedback,
            "extracted_data": extracted_data
        }


    def process_incoming_message(self, db: Session, phone: str, text: Optional[str], media_data: Optional[Dict[str, Any]]) -> None:
        """Processes candidate response using state machine."""
        # Find active onboarding process using robust phone matching
        active_processes = db.query(Contratacao).filter(
            Contratacao.status == "EM_ANDAMENTO"
        ).all()
        
        contratacao = None
        incoming_clean = "".join(filter(str.isdigit, phone))
        
        for p in active_processes:
            p_clean = "".join(filter(str.isdigit, p.telefone))
            
            # Match last 8 digits to handle Brazilian extra 9 digit mismatch
            if len(p_clean) >= 8 and len(incoming_clean) >= 8:
                if p_clean[-8:] == incoming_clean[-8:]:
                    contratacao = p
                    break
            elif p_clean == incoming_clean:
                contratacao = p
                break
        
        if not contratacao:
            # Import dynamically to write warnings to our debug log
            try:
                from app.routes.contratacoes import log_debug_webhook
                log_debug_webhook(f"WARNING: No active onboarding process found in DB matching number: {phone} (incoming_clean: {incoming_clean})")
            except Exception:
                pass
            logger.warning(f"No active onboarding process found for number: {phone}")
            return

        # Add candidate message to history
        sender_name = contratacao.nome_candidato
        if media_data:
            msg_text = f"[Mídia: {media_data.get('mimeType')}]"
            self.log_message(db, contratacao.id, "CANDIDATO", msg_text, msg_type="image", media_url=media_data.get("url"))
        else:
            msg_text = text or ""
            self.log_message(db, contratacao.id, "CANDIDATO", msg_text)

        step = contratacao.current_step
        clean_text = (text or "").strip().lower()

        # State Machine Logic
        # ─────────────────────────────────────────────────────────────────
        # Clean and normalize text by removing punctuation for key matching
        clean_norm = re.sub(r'[!?.,]', '', clean_text).strip()

        # State Machine Logic
        # ─────────────────────────────────────────────────────────────────
        if step == 1:
            # Candidate Greeting response: Check if candidate says "no" or "not me"
            negation_kws = ["não", "nao", "não é", "errado", "incorreto", "no", "engano"]
            is_negation = any(re.search(r'\b' + kw + r'\b', clean_norm) for kw in negation_kws)
            
            if not is_negation:
                contratacao.current_step = 2
                self._send_and_log(db, contratacao, "Você ainda possui interesse na vaga?")
            else:
                contratacao.status = "REJEITADO"
                contratacao.motivo_rejeicao = f"Candidato informou que não é o destinatário correto: '{text}'"
                self._send_and_log(db, contratacao, "Sentimos muito pelo incômodo. O atendimento será finalizado. Obrigado.")
                
        elif step == 2:
            # Interest confirmation: Check if candidate declares desinterest
            negation_kws = ["não", "nao", "desisto", "sem interesse", "no", "recuso", "perdi o interesse"]
            is_negation = any(re.search(r'\b' + kw + r'\b', clean_norm) for kw in negation_kws)
            
            if not is_negation:
                contratacao.current_step = 3
                self._send_and_log(db, contratacao, "Que bom! Vou precisar de alguns documentos seus para prosseguirmos com a contratação, podemos prosseguir?")
            else:
                contratacao.current_step = 21 # Collect reason
                self._send_and_log(db, contratacao, "Entendo. Ficou alguma dúvida? Por favor, nos informe o motivo do desinteresse para podermos registrar no sistema.")

        elif step == 21:
            # Collecting interest rejection reason
            contratacao.status = "REJEITADO"
            contratacao.motivo_rejeicao = f"Candidato declarou desinteresse. Motivo: '{text}'"
            self._send_and_log(db, contratacao, "Muito obrigado pelo seu retorno. O processo foi finalizado.")

        elif step == 3:
            # Document permissions confirmation
            negation_kws = ["não", "nao", "no", "perai", "pera", "espera", "parar", "cancelar"]
            is_negation = any(re.search(r'\b' + kw + r'\b', clean_norm) for kw in negation_kws)
            
            if not is_negation:
                contratacao.current_step = 5
                intro_msg = "Vamos começar!"
                whatsapp_service.send_message(db, contratacao.telefone, intro_msg)
                self.log_message(db, contratacao.id, "BOT", intro_msg)
                self._send_and_log(db, contratacao, DOC_PROMPTS[5])
            else:
                contratacao.status = "INTERROMPIDO_HUMANO"
                self._send_and_log(db, contratacao, "Sem problemas. Vou passar o seu atendimento para um profissional do RH entrar em contato e tirar as suas dúvidas.")

        elif step in DOC_TYPES:
            # Candidate is uploading a document file/image
            if not media_data:
                self._send_and_log(db, contratacao, f"Por favor, envie o documento solicitado como uma foto ou PDF. {DOC_PROMPTS[step]}")
                return

            # Download document from Evolution API
            file_bytes = whatsapp_service.download_media(db, media_data["messageId"], media_data["remoteJid"])
            if not file_bytes:
                self._send_and_log(db, contratacao, "Desculpe, ocorreu um erro ao receber seu arquivo. Por favor, tente enviar novamente.")
                return

            # Save file locally
            tipo_doc = DOC_TYPES[step]
            ext = "pdf" if "pdf" in media_data["mimeType"] else "jpg"
            filename = f"{tipo_doc}_{contratacao.id}_{int(datetime.datetime.utcnow().timestamp())}.{ext}"
            
            uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "contratacoes", str(contratacao.id)))
            os.makedirs(uploads_dir, exist_ok=True)
            file_path = os.path.join(uploads_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            # Local OCR validation
            val_result = self.validate_document_local(file_path, tipo_doc, contratacao.nome_candidato)
            
            # Save validation metadata in db
            doc_record = db.query(ContratacaoDocumento).filter_by(
                contratacao_id=contratacao.id,
                tipo_documento=tipo_doc
            ).first()
            
            if not doc_record:
                doc_record = ContratacaoDocumento(
                    contratacao_id=contratacao.id,
                    tipo_documento=tipo_doc
                )
                db.add(doc_record)
            
            doc_record.file_path = file_path
            doc_record.qualidade_valida = val_result.get("qualidade_valida", True)
            doc_record.validade_valida = val_result.get("validade_valida", True)
            doc_record.legitimidade_valida = val_result.get("legitimidade_valida", True)
            doc_record.ocr_status = "APROVADO" if val_result.get("valido", True) else "REJEITADO"
            doc_record.feedback_recusa = val_result.get("feedback")
            doc_record.extracted_data = json.dumps(val_result.get("extracted_data", {}))
            
            db.commit()

            # Reply back based on validation results
            if val_result.get("valido", True):
                # Valid document! Proceed to next step
                self._send_and_log(db, contratacao, f"✅ Documento validado com sucesso! {val_result.get('feedback', '')}")
                
                # Advance step
                next_step = step + 1
                if next_step == 4: # Skip step 4 helper placeholder
                    next_step = 5
                
                contratacao.current_step = next_step
                db.commit()

                # Prompt for next document or question
                next_prompt = self._get_prompt_for_step(contratacao)
                self._send_and_log(db, contratacao, next_prompt)
            else:
                # Invalid document. Ask again
                self._send_and_log(db, contratacao, f"❌ Houve um problema na validação: {val_result.get('feedback')}\nPor favor, envie o documento novamente.")

        elif step == 12:
            # Dependentes response
            contratacao.possui_dependentes_14 = text
            contratacao.current_step = 13
            db.commit()
            self._send_and_log(db, contratacao, "Será optante pelo vale transporte(desconto de 4% no salario)?")

        elif step == 13:
            # Vale Transporte response
            contratacao.optante_vt = text
            contratacao.current_step = 14
            db.commit()
            self._send_and_log(db, contratacao, "pode me informar seus dados bancários ? (Agencia conta e numero)")

        elif step == 14:
            # Bank Details response
            contratacao.dados_bancarios = text
            contratacao.current_step = 15
            db.commit()
            
            # Send summary overview and ask confirmation
            prompt = self._get_prompt_for_step(contratacao)
            self._send_and_log(db, contratacao, prompt)

        elif step == 15:
            # Overview confirmation
            if clean_text in ("sim", "s", "quero", "alterar", "desejo", "sim, desejo alterar"):
                contratacao.current_step = 16
                self._send_and_log(db, contratacao, "Qual dado você deseja alterar? Envie uma das seguintes palavras-chave: RG Frente, RG Verso, Carteira, Titulo, Certidao, Escolaridade, Vacina, Dependentes, Vale Transporte, Banco")
            else:
                # Finished successfully!
                contratacao.status = "CONCLUIDO"
                db.commit()
                self._send_and_log(db, contratacao, "Contratação confirmada e documentos arquivados! Logo mais você receberá as informações da data do exame admissional. Obrigado!")

        elif step == 16:
            # Candidate is choosing which option to edit
            lower_choice = clean_text
            mapped_step = None
            prompt_resend = ""

            if "frente" in lower_choice or "rg frente" in lower_choice:
                mapped_step = 5
                prompt_resend = "Pode me enviar novamente a foto da FRENTE do seu RG?"
            elif "verso" in lower_choice or "rg verso" in lower_choice:
                mapped_step = 6
                prompt_resend = "Pode me enviar novamente a foto do VERSO do seu RG?"
            elif "carteira" in lower_choice or "trabalho" in lower_choice:
                mapped_step = 7
                prompt_resend = "Pode me enviar novamente a foto da sua carteira de trabalho?"
            elif "titulo" in lower_choice or "eleitor" in lower_choice:
                mapped_step = 8
                prompt_resend = "Pode me enviar novamente a foto do seu titulo de eleitor?"
            elif "certidao" in lower_choice or "nascimento" in lower_choice:
                mapped_step = 9
                prompt_resend = "Pode me enviar novamente a foto da sua certidão de nascimento?"
            elif "escolaridade" in lower_choice or "comprovante" in lower_choice:
                mapped_step = 10
                prompt_resend = "Pode me enviar novamente a foto do seu comprovante de escolaridade?"
            elif "vacina" in lower_choice or "cartao vacina" in lower_choice:
                mapped_step = 11
                prompt_resend = "Pode me enviar novamente a foto do seu cartão vacina?"
            elif "dependente" in lower_choice:
                mapped_step = 12
                prompt_resend = "Você possui dependentes menores do que 14 anos?"
            elif "vale" in lower_choice or "transporte" in lower_choice or "vt" in lower_choice:
                mapped_step = 13
                prompt_resend = "Será optante pelo vale transporte(desconto de 4% no salario)?"
            elif "banco" in lower_choice or "bancario" in lower_choice:
                mapped_step = 14
                prompt_resend = "pode me informar seus dados bancários ? (Agencia conta e numero)"

            if mapped_step:
                contratacao.current_step = mapped_step
                db.commit()
                self._send_and_log(db, contratacao, prompt_resend)
            else:
                self._send_and_log(db, contratacao, "Opção inválida. Digite uma das palavras-chave: RG Frente, RG Verso, Carteira, Titulo, Certidao, Escolaridade, Vacina, Dependentes, Vale Transporte, Banco")

    def _send_and_log(self, db: Session, contratacao: Contratacao, text: str):
        self.log_message(db, contratacao.id, "BOT", text)
        whatsapp_service.send_message(db, contratacao.telefone, text)

onboarding_service = OnboardingService()
