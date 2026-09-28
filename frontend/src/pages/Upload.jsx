import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Toast, { ToastContainer } from '../components/Toast';
import axios from 'axios';
import { Moon, Sun, Play, AlertCircle, Sparkles } from 'lucide-react';

// ─── Animations ──────────────────────────────────────────────────────────────
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// ─── Styled Components ────────────────────────────────────────────────────────
const PageContainer = styled.div`
  animation: ${fadeIn} 0.4s ease-out;
  max-width: 700px;
  margin: 0 auto;
`;

const MealSelectorLabel = styled.div`
  font-size: 0.8125rem;
  font-weight: 700;
  color: #37474f;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const MealCardsContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const MealCard = styled.div`
  background: ${({ $active }) => $active ? '#e8f5e9' : 'white'};
  border: 2px solid ${({ $active }) => $active ? '#2e7d32' : '#dadce0'};
  border-radius: 12px;
  padding: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: ${({ $active }) => $active ? '0 4px 12px rgba(46, 125, 50, 0.15)' : 'none'};

  &:hover {
    border-color: #2e7d32;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  }

  &:active {
    transform: translateY(0);
  }
`;

const MealIconWrapper = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: ${({ $active }) => $active ? '#2e7d32' : '#f1f3f4'};
  color: ${({ $active }) => $active ? 'white' : '#5f6368'};
  transition: all 0.2s ease;
`;

const MealTextWrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const MealTitle = styled.span`
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: ${({ $active }) => $active ? '#1b5e20' : '#202124'};
`;

const MealDescription = styled.span`
  font-size: 0.75rem;
  color: ${({ $active }) => $active ? '#2e7d32' : '#5f6368'};
  margin-top: 0.2rem;
  line-height: 1.3;
`;

const DetectionBadge = styled.div`
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #2e7d32;
  color: #1b5e20;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  font-size: 0.8125rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  line-height: 1.4;
`;

const ActionRow = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
`;

// ─── Main Component ───────────────────────────────────────────────────────────
const Upload = () => {
  const [tipoRefeicao, setTipoRefeicao] = useState('almoco'); // 'almoco' | 'jantar'
  const [file, setFile] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [toast, setToast] = useState(null);

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  const handleGenerateSpreadsheet = async () => {
    if (!file) {
      showToast('Selecione o arquivo de ponto (PDF) para continuar.', 'error');
      return;
    }

    setLoading(true);
    setLoadingMsg(`Analisando PDF, identificando Obra e gerando planilha de ${tipoRefeicao === 'almoco' ? 'Almoço' : 'Jantar'}...`);

    const formData = new FormData();
    formData.append('tipo_refeicao', tipoRefeicao);
    formData.append('file', file);

    try {
      const response = await axios.post('/api/v1/uploads/process-pdf-alimentation', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `relatorio_alimentacao_${tipoRefeicao}_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showToast('Planilha de Alimentação gerada com sucesso!');
      setFile(null);
    } catch (err) {
      console.error(err);
      if (err.response?.data instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const errorObj = JSON.parse(reader.result);
            showToast(errorObj.detail || 'Erro ao processar o PDF e gerar a planilha.', 'error');
          } catch (e) {
            showToast('Erro ao processar o PDF e gerar a planilha.', 'error');
          }
        };
        reader.readAsText(err.response.data);
      } else {
        showToast(err.response?.data?.detail || 'Erro ao processar o PDF e gerar a planilha.', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Controle de Alimentação" 
        subtitle="Carregue o PDF do espelho de ponto para gerar relatórios de refeições" 
      />

      {loading && <Loader message={loadingMsg} />}

      {!loading && (
        <Card title="Upload de Espelho de Ponto">
          <MealSelectorLabel>Tipo de Refeição</MealSelectorLabel>
          <MealCardsContainer>
            <MealCard 
              $active={tipoRefeicao === 'almoco'} 
              onClick={() => setTipoRefeicao('almoco')}
            >
              <MealIconWrapper $active={tipoRefeicao === 'almoco'}>
                <Sun size={24} />
              </MealIconWrapper>
              <MealTextWrapper>
                <MealTitle $active={tipoRefeicao === 'almoco'}>Almoço</MealTitle>
                <MealDescription $active={tipoRefeicao === 'almoco'}>
                  Todos os colaboradores com qualquer batida no dia.
                </MealDescription>
              </MealTextWrapper>
            </MealCard>

            <MealCard 
              $active={tipoRefeicao === 'jantar'} 
              onClick={() => setTipoRefeicao('jantar')}
            >
              <MealIconWrapper $active={tipoRefeicao === 'jantar'}>
                <Moon size={24} />
              </MealIconWrapper>
              <MealTextWrapper>
                <MealTitle $active={tipoRefeicao === 'jantar'}>Jantar</MealTitle>
                <MealDescription $active={tipoRefeicao === 'jantar'}>
                  Apenas colaboradores com batidas registradas após as 18:00h.
                </MealDescription>
              </MealTextWrapper>
            </MealCard>
          </MealCardsContainer>

          <DetectionBadge>
            <Sparkles size={20} style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <strong>Detecção Automática Ativa:</strong> O sistema lerá os dados do PDF para identificar a <strong>Obra correspondente</strong> (pelo Local de Trabalho) e a <strong>estrutura de planilha ativa</strong> de alimentação no banco de dados. Você só precisa escolher o tipo de refeição e carregar o arquivo.
            </div>
          </DetectionBadge>

          <FileUploader 
            onFileSelected={(selectedFile) => setFile(selectedFile)}
            selectedFile={file}
            acceptedFormats=".pdf"
          />

          <ActionRow>
            <Button 
              onClick={handleGenerateSpreadsheet} 
              disabled={!file}
              style={{ backgroundColor: '#2e7d32', borderColor: '#2e7d32' }}
            >
              <Play size={16} />
              Gerar Planilha de Alimentação
            </Button>
          </ActionRow>
        </Card>
      )}
    </PageContainer>
  );
};

export default Upload;
