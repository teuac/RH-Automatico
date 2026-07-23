import React, { useState, useEffect } from 'react';
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
import { Bus, Play, ArrowLeft, Check, AlertCircle, RefreshCw, DollarSign, Calendar, Users, Search } from 'lucide-react';

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 992px) {
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

const InputNumber = styled.input`
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

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 992px) {
    grid-template-columns: repeat(2, 1fr);
  }
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
`;

const StatCard = styled.div`
  background: white;
  border: 1px solid #dadce0;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const StatIcon = styled.div`
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background-color: ${({ $bg }) => $bg || '#e8f0fe'};
  color: ${({ $color }) => $color || '#1a73e8'};
  display: flex;
  align-items: center;
  justify-content: center;
`;

const StatInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

const StatLabel = styled.span`
  font-size: 0.75rem;
  color: #5f6368;
  font-weight: 500;
`;

const StatValue = styled.span`
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #202124;
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

const SearchBox = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #f1f3f4;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  max-width: 320px;
  margin-bottom: 1rem;

  input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 0.875rem;
    width: 100%;
  }
`;

const ControleVT = () => {
  const [selectedObra, setSelectedObra] = useState('');
  const [selectedPlanilha, setSelectedPlanilha] = useState('');
  const [valorDiarioVT, setValorDiarioVT] = useState('12.00');
  const [file, setFile] = useState(null);
  
  const [step, setStep] = useState('upload'); // 'upload' | 'preview' | 'result'
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [toast, setToast] = useState(null);
  
  const [previewData, setPreviewData] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch Settings for default VT value
  const { data: settings } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/settings/');
      return response.data;
    }
  });

  // Fetch Active Obras
  const { data: obras, isLoading: loadingObras } = useQuery({
    queryKey: ['activeObrasVT'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/obras/');
      return response.data;
    }
  });

  // Fetch Active Planilhas
  const { data: planilhas, isLoading: loadingPlanilhas } = useQuery({
    queryKey: ['activePlanilhasVT'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/planilhas/');
      return response.data;
    }
  });

  useEffect(() => {
    if (settings && settings.valor_diario_vt) {
      setValorDiarioVT(settings.valor_diario_vt);
    }
  }, [settings]);

  // Auto-select Planilha when Obra is selected
  useEffect(() => {
    if (selectedObra && planilhas) {
      const matching = planilhas.filter(p => p.obra_id === Number(selectedObra) && p.status === 'ATIVO');
      if (matching.length > 0) {
        setSelectedPlanilha(String(matching[0].id));
      } else {
        const globalMatching = planilhas.filter(p => !p.obra_id && p.status === 'ATIVO');
        if (globalMatching.length > 0) {
          setSelectedPlanilha(String(globalMatching[0].id));
        }
      }
    }
  }, [selectedObra, planilhas]);

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  const handleGeneratePreview = async () => {
    if (!selectedObra) {
      showToast('Selecione uma Obra para continuar.', 'error');
      return;
    }
    if (!selectedPlanilha) {
      showToast('Selecione a Planilha de destino para continuar.', 'error');
      return;
    }
    if (!file) {
      showToast('Selecione o arquivo de ponto para upload.', 'error');
      return;
    }

    setLoading(true);
    setLoadingMsg('Analisando arquivo e agrupando marcações multi-datas de VT...');

    try {
      const formData = new FormData();
      formData.append('obra_id', selectedObra);
      formData.append('planilha_id', selectedPlanilha);
      formData.append('valor_diario_vt', valorDiarioVT);
      formData.append('file', file);

      const response = await axios.post('/api/v1/controle-vt/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setPreviewData(response.data);
      setStep('preview');
      showToast('Prévia de Controle VT gerada com sucesso.');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Erro ao gerar prévia do arquivo.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleProcessSync = async () => {
    if (!previewData) return;

    setLoading(true);
    setLoadingMsg(`Sincronizando ${previewData.datas_encontradas?.length || 0} datas com o Google Sheets...`);

    try {
      const formData = new FormData();
      formData.append('obra_id', selectedObra);
      formData.append('planilha_id', selectedPlanilha);
      formData.append('valor_diario_vt', valorDiarioVT);
      formData.append('file', file);

      const response = await axios.post('/api/v1/controle-vt/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setResultData(response.data);
      setStep('result');
      showToast('Sincronização de Vale Transporte concluída com sucesso!');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Erro ao sincronizar dados de VT com o Google Sheets.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreviewData(null);
    setResultData(null);
    setStep('upload');
  };

  const activeObrasList = obras?.filter(o => o.status === 'ATIVO') || [];

  const filteredPreviewRows = previewData?.linhas_preview?.filter(row => 
    row.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    row.matricula.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Controle de Vale Transporte (VT)" 
        subtitle="Processamento automatizado de marcações de ponto multi-datas com cálculo de diárias de VT" 
      />

      {loading && <Loader message={loadingMsg} />}

      {!loading && step === 'upload' && (
        <Card title="Upload de Marcações de Ponto (VT Multi-Datas)">
          <FormGrid>
            <FormGroup>
              <Label>Obra de Destino *</Label>
              <Select value={selectedObra} onChange={(e) => setSelectedObra(e.target.value)}>
                <option value="">-- Selecione uma Obra --</option>
                {activeObrasList.map(o => (
                  <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
                ))}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Planilha Google *</Label>
              <Select value={selectedPlanilha} onChange={(e) => setSelectedPlanilha(e.target.value)}>
                <option value="">-- Selecione a Planilha --</option>
                {planilhas?.filter(p => p.status === 'ATIVO').map(p => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
                ))}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Valor Diário de VT (R$) *</Label>
              <InputNumber 
                type="number"
                step="0.50"
                min="0"
                value={valorDiarioVT} 
                onChange={(e) => setValorDiarioVT(e.target.value)} 
                placeholder="12.00"
              />
            </FormGroup>
          </FormGrid>

          <FileUploader 
            onFileSelected={(selectedFile) => setFile(selectedFile)}
            selectedFile={file}
            acceptedFormats=".txt,.csv,.xlsx"
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <Button onClick={handleGeneratePreview} disabled={!selectedObra || !selectedPlanilha || !file}>
              <Play size={16} />
              Gerar Prévia do Controle VT
            </Button>
          </div>
        </Card>
      )}

      {!loading && step === 'preview' && previewData && (
        <div>
          <StatsGrid>
            <StatCard>
              <StatIcon $bg="#e8f0fe" $color="#1a73e8">
                <Users size={22} />
              </StatIcon>
              <StatInfo>
                <StatLabel>Colaboradores</StatLabel>
                <StatValue>{previewData.total_colaboradores}</StatValue>
              </StatInfo>
            </StatCard>

            <StatCard>
              <StatIcon $bg="#fef7e0" $color="#b06000">
                <Calendar size={22} />
              </StatIcon>
              <StatInfo>
                <StatLabel>Datas Encontradas</StatLabel>
                <StatValue>{previewData.datas_encontradas?.length || 0}</StatValue>
              </StatInfo>
            </StatCard>

            <StatCard>
              <StatIcon $bg="#e6f4ea" $color="#0f9d58">
                <Check size={22} />
              </StatIcon>
              <StatInfo>
                <StatLabel>Presenças Totais</StatLabel>
                <StatValue>{previewData.total_presencas}</StatValue>
              </StatInfo>
            </StatCard>

            <StatCard>
              <StatIcon $bg="#f3e8fd" $color="#9334e8">
                <DollarSign size={22} />
              </StatIcon>
              <StatInfo>
                <StatLabel>Total VT Estimado</StatLabel>
                <StatValue>R$ {previewData.valor_total_estimado?.toFixed(2)}</StatValue>
              </StatInfo>
            </StatCard>
          </StatsGrid>

          <Card title={`Prévia das Marcações — Obra: ${previewData.obra?.nome}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
              <SearchBox>
                <Search size={16} color="#5f6368" />
                <input 
                  type="text" 
                  placeholder="Buscar funcionário ou matrícula..." 
                  value={searchTerm} 
                  onChange={(e) => setSearchTerm(e.target.value)} 
                />
              </SearchBox>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <Button variant="secondary" onClick={handleReset}>
                  <ArrowLeft size={16} />
                  Voltar
                </Button>
                <Button onClick={handleProcessSync}>
                  <Check size={16} />
                  Sincronizar Controle VT com Google Sheets
                </Button>
              </div>
            </div>

            <Table headers={["Matrícula", "Nome", "Cadastro no Sistema", "Dias de Presença", "Valor Total VT (R$)", "Datas com Presença"]}>
              {filteredPreviewRows.map((row, idx) => (
                <Tr key={idx}>
                  <Td><strong>{row.matricula}</strong></Td>
                  <Td>{row.nome}</Td>
                  <Td>
                    <StatusBadge $found={row.status_match === 'ENCONTRADO'}>
                      {row.status_match === 'ENCONTRADO' ? 'ENCONTRADO' : 'NÃO CADASTRADO'}
                    </StatusBadge>
                  </Td>
                  <Td style={{ fontWeight: 600, color: '#1a73e8' }}>{row.dias_presenca} dias</Td>
                  <Td style={{ fontWeight: 700, color: '#0f9d58' }}>R$ {row.valor_total?.toFixed(2)}</Td>
                  <Td style={{ fontSize: '0.8rem', color: '#5f6368', maxWidth: '250px' }}>
                    {row.datas_presenca?.join(', ')}
                  </Td>
                </Tr>
              ))}
            </Table>
          </Card>
        </div>
      )}

      {!loading && step === 'result' && resultData && (
        <Card title="Resultado da Sincronização de Vale Transporte">
          <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: '#e6f4ea', color: '#0f9d58', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
              <Check size={36} />
            </div>
            
            <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.5rem', color: '#202124', marginBottom: '0.5rem' }}>
              Sincronização Concluída com Sucesso!
            </h3>
            <p style={{ color: '#5f6368', fontSize: '0.9rem', marginBottom: '2rem' }}>
              {resultData.message}
            </p>

            <StatsGrid style={{ maxWidth: '700px', margin: '0 auto 2rem' }}>
              <StatCard>
                <StatIcon $bg="#e8f0fe" $color="#1a73e8">
                  <Calendar size={20} />
                </StatIcon>
                <StatInfo>
                  <StatLabel>Datas Processadas</StatLabel>
                  <StatValue>{resultData.datas_processadas?.length || 0}</StatValue>
                </StatInfo>
              </StatCard>

              <StatCard>
                <StatIcon $bg="#e6f4ea" $color="#0f9d58">
                  <Check size={20} />
                </StatIcon>
                <StatInfo>
                  <StatLabel>Atualizados</StatLabel>
                  <StatValue>{resultData.total_atualizados}</StatValue>
                </StatInfo>
              </StatCard>

              <StatCard>
                <StatIcon $bg="#f3e8fd" $color="#9334e8">
                  <DollarSign size={20} />
                </StatIcon>
                <StatInfo>
                  <StatLabel>Valor Total VT</StatLabel>
                  <StatValue>R$ {resultData.valor_total_vt?.toFixed(2)}</StatValue>
                </StatInfo>
              </StatCard>

              <StatCard>
                <StatIcon $bg="#f1f3f4" $color="#5f6368">
                  <RefreshCw size={20} />
                </StatIcon>
                <StatInfo>
                  <StatLabel>Tempo</StatLabel>
                  <StatValue>{(resultData.tempo_processamento_ms / 1000).toFixed(2)}s</StatValue>
                </StatInfo>
              </StatCard>
            </StatsGrid>

            <Button onClick={handleReset}>
              <RefreshCw size={16} />
              Realizar Novo Processamento de VT
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ControleVT;
