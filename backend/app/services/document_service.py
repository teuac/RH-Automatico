import io
import os
import zipfile
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont
import pypdf
from sqlalchemy.orm import Session
from app.models.contratacao import Contratacao

class DocumentService:
    def create_summary_pdf(self, contratacao: Contratacao) -> bytes:
        """Generates a summary page with candidate answers and text data as a PDF using PIL."""
        # A4 size at 150 DPI: 1240 x 1754
        width, height = 1240, 1754
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        
        # Draw background decoration (a sleek header block matching company branding)
        draw.rectangle([(0, 0), (width, 180)], fill="#0f9d58") # Sleek emerald green header
        
        # Try loading default font or system fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            header_font = ImageFont.truetype("arial.ttf", 26)
            text_font = ImageFont.truetype("arial.ttf", 20)
            bold_font = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            bold_font = ImageFont.load_default()

        # Title
        draw.text((60, 60), "AC ENGENHARIA — FICHA DE CONTRATAÇÃO", fill="white", font=title_font)
        draw.text((60, 120), f"Resumo de coleta de dados via WhatsApp - Telefone: {contratacao.telefone}", fill="#e8f5e9", font=text_font)

        # Content margins
        margin_x = 80
        curr_y = 240

        def draw_section(title: str):
            nonlocal curr_y
            draw.rectangle([(margin_x, curr_y), (width - margin_x, curr_y + 40)], fill="#f1f3f4")
            draw.text((margin_x + 15, curr_y + 8), title, fill="#202124", font=header_font)
            curr_y += 70

        def draw_field(label: str, val: str):
            nonlocal curr_y
            draw.text((margin_x, curr_y), f"{label}:", fill="#5f6368", font=bold_font)
            draw.text((margin_x + 300, curr_y), str(val or "Não Informado"), fill="#202124", font=text_font)
            curr_y += 40

        # Candidato info
        draw_section("Dados Cadastrais")
        draw_field("Nome do Candidato", contratacao.nome_candidato)
        draw_field("Cargo Pretendido", contratacao.cargo)
        draw_field("Telefone de Contato", contratacao.telefone)
        draw_field("Data de Abertura", contratacao.created_at.strftime("%d/%m/%Y %H:%M"))
        draw_field("Status do Processo", contratacao.status)
        curr_y += 40

        # Coleta de Dados
        draw_section("Respostas ao Questionário")
        draw_field("Dependentes < 14 anos", contratacao.possui_dependentes_14)
        draw_field("Vale Transporte (VT)", contratacao.optante_vt)
        
        # Bank info is text-wrapped
        draw.text((margin_x, curr_y), "Dados Bancários:", fill="#5f6368", font=bold_font)
        bank_lines = (contratacao.dados_bancarios or "Não Informado").split("\n")
        bx = margin_x + 300
        for line in bank_lines:
            draw.text((bx, curr_y), line.strip(), fill="#202124", font=text_font)
            curr_y += 30
        curr_y += 50

        # Footer
        draw.rectangle([(0, height - 80), (width, height)], fill="#f1f3f4")
        draw.text((margin_x, height - 50), "Gerado automaticamente pelo Sistema de Gestão de Contratações - AC Engenharia", fill="#5f6368", font=text_font)

        # Output bytes of PDF
        pdf_buf = io.BytesIO()
        image.save(pdf_buf, format="PDF")
        return pdf_buf.getvalue()

    def generate_hiring_zip(self, db: Session, contratacao: Contratacao) -> io.BytesIO:
        """Gathers all candidate documents, converts images, merges them into 1 PDF, and returns a ZIP archive."""
        zip_buffer = io.BytesIO()
        
        # Gathers all successfully uploaded documents
        docs_to_merge = []
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Generate candidate answers summary page as PDF
            summary_pdf_data = self.create_summary_pdf(contratacao)
            zf.writestr("Ficha_Resumo_Contratacao.pdf", summary_pdf_data)
            
            # Save summary page to list of files to merge
            summary_pdf_stream = io.BytesIO(summary_pdf_data)
            docs_to_merge.append(summary_pdf_stream)
            
            # 2. Add individual documents to the ZIP and prepare them for merging
            for doc in contratacao.documentos:
                if not doc.file_path or not os.path.exists(doc.file_path):
                    continue
                
                filename = os.path.basename(doc.file_path)
                
                # Read raw file bytes
                with open(doc.file_path, "rb") as f:
                    file_bytes = f.read()
                
                # Write individual document to zip
                zf.writestr(f"documentos/{doc.tipo_documento}_{filename}", file_bytes)
                
                # Prepare file for PDF merging
                if doc.file_path.lower().endswith(".pdf"):
                    docs_to_merge.append(io.BytesIO(file_bytes))
                else:
                    # Convert image file to PDF in memory using PIL
                    try:
                        with Image.open(doc.file_path) as img:
                            img_pdf_buf = io.BytesIO()
                            img.convert("RGB").save(img_pdf_buf, format="PDF")
                            docs_to_merge.append(io.BytesIO(img_pdf_buf.getvalue()))
                    except Exception as e:
                        print(f"Error converting document {doc.file_path} to PDF: {str(e)}")

            # 3. Merge all files into 1 consolidated PDF
            if docs_to_merge:
                try:
                    merger = pypdf.PdfMerger()
                    for doc_stream in docs_to_merge:
                        merger.append(doc_stream)
                    
                    merged_pdf_buf = io.BytesIO()
                    merger.write(merged_pdf_buf)
                    merger.close()
                    
                    # Write consolidated PDF to the root of the ZIP file
                    zf.writestr("Documentos_Consolidados_Mesclados.pdf", merged_pdf_buf.getvalue())
                except Exception as e:
                    print(f"Error compiling merged PDF document: {str(e)}")

        zip_buffer.seek(0)
        return zip_buffer

document_service = DocumentService()
