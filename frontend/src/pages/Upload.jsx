import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Toast, { ToastContainer } from '../components/Toast';
import { Table, Tr, Td } from '../components/Table';
import { Play, ArrowLeft, Check, AlertCircle, RefreshCw } from 'lucide-react';

const ControlsRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
`;

const Label = styled.label`
  font-size: 0.8125rem;
  font-weight: 600;
  color: #3c4043;
`;

const Select = styled.select`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
  &:focus {
    border-color: #1a73e8;
  }
`;

const DateInput = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
  &:focus {
    border-color: #1a73e8;
  }
`;

const PreviewActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const StatusBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  
  ${({ $found }) => $found ? `
    background-color: #e6f4ea;
    color: #0f9d58;
  ` : `
    background-color: #fce8e6;
    color: #d93025;
  `}
`;

const Upload = () => {
  const [selectedObraId, setSelectedObraId] = useState('');
  const [selectedPlanilhaId, setSelectedPlanilhaId] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [file, setFile] = useState(null);
  
  const [previewData, setPreviewData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploaderError, setUploaderError] = useState(null);
  
  const [toastMessage, setToastMessage] = useState(null);
  const [toastVariant, setToastVariant] = useState('success');

  // Load Active Obras
  const { data: obras } = useQuery({
    queryKey: ['activeObras'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/obras/');
      return response.data;
    }
  });

  // Load Active Planilhas
  const { data: planilhas } = useQuery({
    queryKey: ['activePlanilhas'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/planilhas/');
      return response.data;
    }
  });

  const showToast = (message, variant = 'success') => {
    setToastMessage(message);
    setToastVariant(variant);
  };

  const handlePreview = async () => {
    if (!selectedObraId) {
      setUploaderError('Por favor, selecione uma obra.');
      return;
    }
    if (!selectedPlanilhaId) {
      setUploaderError('Por favor, selecione uma planilha de destino.');
      return;
    }
    if (!file) {
      setUploaderError('Por favor, selecione um arquivo.');
      return;
    }
    setUploaderError(null);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('obra_id', selectedObraId);
    formData.append('planilha_id', selectedPlanilhaId);
    formData.append('file', file);
    if (selectedDate) {
      formData.append('override_date', selectedDate);
    }

    try {
      const response = await axios.post('/api/v1/uploads/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPreviewData(response.data);
      // Pre-set date if extracted from parser
      if (response.data.data && !selectedDate) {
        setSelectedDate(response.data.data);
      }
      showToast('Visualização gerada com sucesso.');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Erro ao processar visualização do arquivo.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCommit = async () => {
    if (!previewData) return;
    setIsProcessing(true);

    try {
      const payload = {
        obra_id: previewData.obra_id,
        planilha_id: previewData.planilha_id,
        date: previewData.data,
        filename: file.name,
        funcionarios: previewData.funcionarios.map(f => ({
          matricula: f.matricula,
          nome: f.nome,
          horarios: f.horarios
        }))
      };

      const response = await axios.post('/api/v1/uploads/commit', payload);
      const metrics = response.data;
      
      showToast(
        `Alimentação atualizada! Refeições gravadas: ${metrics.updated}, Ignorados: ${metrics.ignored}, Pendentes: ${metrics.pending}. Tempo: ${(metrics.processing_time_ms / 1000).toFixed(2)}s`,
        metrics.pending > 0 ? 'warning' : 'success'
      );
      
      // Clean up state
      setPreviewData(null);
      setFile(null);
      setSelectedObraId('');
      setSelectedPlanilhaId('');
      setSelectedDate('');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Falha ao sincronizar presença.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancel = () => {
    setPreviewData(null);
    setFile(null);
  };

  const filteredPlanilhas = planilhas?.filter(p => 
    p.obra_id === Number(selectedObraId) && 
    p.automacao === 'ALIMENTACAO' && 
    p.status === 'ATIVO'
  ) || [];

  if (isProcessing) {
    return <Loader message={previewData ? "Gravando refeições no Google Sheets..." : "Analisando arquivo de refeições..."} />;
  }

  return (
    <div>
      {toastMessage && (
        <ToastContainer>
          <Toast message={toastMessage} variant={toastVariant} onClose={() => setToastMessage(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Controle de Alimentação" 
        subtitle={previewData ? "Confirme as refeições extraídas antes de registrar" : "Selecione o arquivo de refeições exportado pelo relógio de ponto"} 
      />

      {!previewData ? (
        <Card>
          <ControlsRow>
            <FormGroup>
              <Label>Selecione a Obra</Label>
              <Select 
                value={selectedObraId} 
                onChange={(e) => {
                  setSelectedObraId(e.target.value);
                  setSelectedPlanilhaId(''); // Reset selected spreadsheet when work changes
                }}
              >
                <option value="">Selecione...</option>
                {obras?.map(o => (
                  <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
                ))}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Selecione a Planilha Google</Label>
              <Select 
                value={selectedPlanilhaId} 
                onChange={(e) => setSelectedPlanilhaId(e.target.value)}
                disabled={!selectedObraId}
              >
                <option value="">
                  {!selectedObraId ? 'Selecione uma obra primeiro...' : 'Selecione...'}
                </option>
                {selectedObraId && filteredPlanilhas.length === 0 ? (
                  <option value="" disabled>Nenhuma planilha ativa para esta obra</option>
                ) : (
                  filteredPlanilhas.map(p => (
                    <option key={p.id} value={p.id}>{p.nome} ({p.nome_aba})</option>
                  ))
                )}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Data (Opcional - substitui a data detectada no arquivo)</Label>
              <DateInput 
                type="date" 
                value={selectedDate} 
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </FormGroup>
          </ControlsRow>

          <FileUploader 
            onFileSelected={setFile} 
            selectedFile={file} 
            error={uploaderError} 
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <Button onClick={handlePreview} disabled={!file || !selectedObraId || !selectedPlanilhaId}>
              <Play size={16} />
              Analisar Arquivo
            </Button>
          </div>
        </Card>
      ) : (
        <div>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <strong>Obra:</strong> {previewData.obra_nome}<br />
                <strong>Data da Presença:</strong> {previewData.data}
              </div>
              <div>
                <strong>Planilha Google:</strong> {previewData.planilha_nome}<br />
                <strong>ID Planilha:</strong> <span style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{previewData.planilha_google_id}</span><br />
                <strong>Aba:</strong> {previewData.nome_aba}
              </div>
            </div>

            <Table headers={["Matrícula", "Funcionário", "Horários Detectados", "Encontrado", "Situação"]}>
              {previewData.funcionarios.map((emp, idx) => (
                <Tr key={idx}>
                  <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                  <Td><strong>{emp.nome}</strong></Td>
                  <Td>
                    {emp.horarios.map((t, i) => (
                      <span key={i} style={{ backgroundColor: '#f1f3f4', padding: '0.2rem 0.4rem', borderRadius: '4px', marginRight: '0.25rem', fontSize: '0.8rem', fontWeight: 500 }}>
                        {t}
                      </span>
                    ))}
                  </Td>
                  <Td>
                    <StatusBadge $found={emp.encontrado}>
                      {emp.encontrado ? "SIM" : "NÃO"}
                    </StatusBadge>
                  </Td>
                  <Td>
                    <span style={{ fontSize: '0.8rem', color: emp.encontrado ? '#5f6368' : '#d93025', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      {!emp.encontrado && <AlertCircle size={12} />}
                      {emp.situacao}
                    </span>
                  </Td>
                </Tr>
              ))}
            </Table>

            <PreviewActions>
              <Button variant="secondary" onClick={handleCancel}>
                <ArrowLeft size={16} />
                Cancelar
              </Button>
              <Button variant={previewData.funcionarios.some(f => !f.encontrado) ? "success" : "primary"} onClick={handleCommit}>
                <Check size={16} />
                Registrar Alimentação no Google Sheets
              </Button>
            </PreviewActions>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Upload;
