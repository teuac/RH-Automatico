import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Toast, { ToastContainer } from '../components/Toast';
import { Bus, Play, Sparkles, DollarSign } from 'lucide-react';

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

const FormRow = styled.div`
  max-width: 350px;
  margin-bottom: 1.5rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
`;

const Label = styled.label`
  font-size: 0.8125rem;
  font-weight: 700;
  color: #37474f;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const InputWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const CurrencySymbol = styled.div`
  position: absolute;
  left: 12px;
  color: #5f6368;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
`;

const InputNumber = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  border-radius: 8px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 40px;
  width: 100%;
  background-color: white;
  color: #202124;
  transition: border-color 0.2s ease;
  &:focus {
    border-color: #1a73e8;
  }
`;

const DetectionBadge = styled.div`
  background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
  border: 1px solid #1a73e8;
  color: #1b365d;
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
const ControleVT = () => {
  const [valorDiarioVT, setValorDiarioVT] = useState('12.00');
  const [file, setFile] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [toast, setToast] = useState(null);

  // Fetch Settings for default VT value
  const { data: settings } = useQuery({
    queryKey: ['systemSettingsVT'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/settings/');
      return response.data;
    }
  });

  useEffect(() => {
    if (settings && settings.valor_diario_vt) {
      setValorDiarioVT(settings.valor_diario_vt);
    }
  }, [settings]);

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  const handlePdfProcess = async () => {
    const vtVal = parseFloat(valorDiarioVT);
    if (!file || isNaN(vtVal) || vtVal <= 0) {
      showToast('Selecione o arquivo PDF e insira um valor diário de VT válido.', 'error');
      return;
    }

    setLoading(true);
    setLoadingMsg('Processando espelhos de ponto (PDF), identificando a Obra e gerando planilha de VT...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('valor_diario_vt', String(vtVal));

    try {
      const response = await axios.post('/api/v1/controle-vt/process-pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `relatorio_vale_transporte_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showToast('Planilha de Vale Transporte gerada e baixada com sucesso!');
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
        title="Controle de Vale Transporte (VT)" 
        subtitle="Carregue o PDF do espelho de ponto para gerar o cálculo de diárias e relatórios de VT" 
      />

      {loading && <Loader message={loadingMsg} />}

      {!loading && (
        <Card title="Geração de Relatório de Vale Transporte">
          <FormRow>
            <FormGroup>
              <Label>Valor Diário de VT *</Label>
              <InputWrapper>
                <CurrencySymbol>R$</CurrencySymbol>
                <InputNumber 
                  type="number"
                  step="0.10"
                  min="0"
                  value={valorDiarioVT} 
                  onChange={(e) => setValorDiarioVT(e.target.value)} 
                  placeholder="12.00"
                />
              </InputWrapper>
            </FormGroup>
          </FormRow>

          <DetectionBadge>
            <Sparkles size={20} style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <strong>Detecção Automática Ativa:</strong> O sistema lerá os dados do PDF para identificar a <strong>Obra correspondente</strong> (pelo Local de Trabalho) e cruzar com os colaboradores ativos no banco de dados. Qualquer colaborador faltante no arquivo será incluído com saldo de VT zerado.
            </div>
          </DetectionBadge>

          <FileUploader 
            onFileSelected={(selectedFile) => setFile(selectedFile)}
            selectedFile={file}
            acceptedFormats=".pdf"
          />

          <ActionRow>
            <Button 
              onClick={handlePdfProcess} 
              disabled={!file || parseFloat(valorDiarioVT) <= 0}
              style={{ backgroundColor: '#1a73e8', borderColor: '#1a73e8' }}
            >
              <Play size={16} />
              Gerar Planilha de Vale Transporte
            </Button>
          </ActionRow>
        </Card>
      )}
    </PageContainer>
  );
};

export default ControleVT;
