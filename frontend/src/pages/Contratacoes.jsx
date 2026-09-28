import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { 
  UserPlus, Search, Filter, Plus, FileText, CheckCircle2, Clock, 
  AlertCircle, Trash2, ArrowLeft, Pause, Play, Download, XCircle, RefreshCw, MessageSquare, ShieldCheck
} from 'lucide-react';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import Button from '../components/Button';
import Input from '../components/Input';
import Modal from '../components/Modal';
import Loader from '../components/Loader';
import Toast, { ToastContainer } from '../components/Toast';
import { Table, Tr, Td } from '../components/Table';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
`;

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
`;

const StatIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background-color: ${props => props.$bg || '#e8f0fe'};
  color: ${props => props.$color || '#1a73e8'};
  display: flex;
  align-items: center;
  justify-content: center;
`;

const StatInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

const StatValue = styled.span`
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #202124;
`;

const StatLabel = styled.span`
  font-size: 0.8125rem;
  color: #5f6368;
  font-weight: 500;
`;

const Toolbar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const SearchBox = styled.div`
  position: relative;
  flex: 1;
  max-width: 360px;
  svg {
    position: absolute;
    left: 0.875rem;
    top: 50%;
    transform: translateY(-50%);
    color: #9aa0a6;
  }
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 0.625rem 1rem 0.625rem 2.5rem;
  border: 1px solid #dadce0;
  border-radius: 8px;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
  &:focus {
    border-color: #1a73e8;
    box-shadow: 0 0 0 2px rgba(26,115,232,0.15);
  }
`;

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: ${props => {
    switch (props.$status) {
      case 'CONCLUIDO': return '#e6f4ea';
      case 'PENDENTE': return '#f1f3f4';
      case 'EM_ANDAMENTO': return '#e8f0fe';
      case 'INTERROMPIDO_HUMANO': return '#fef7e0';
      case 'REJEITADO': return '#fce8e6';
      default: return '#f1f3f4';
    }
  }};
  color: ${props => {
    switch (props.$status) {
      case 'CONCLUIDO': return '#137333';
      case 'PENDENTE': return '#5f6368';
      case 'EM_ANDAMENTO': return '#1a73e8';
      case 'INTERROMPIDO_HUMANO': return '#b06000';
      case 'REJEITADO': return '#c5221f';
      default: return '#5f6368';
    }
  }};
`;

// Detail Layout components
const DetailHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #dadce0;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const CandidateMeta = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  h2 {
    font-family: 'Outfit', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #202124;
  }
  p {
    font-size: 0.875rem;
    color: #5f6368;
    strong { color: #202124; }
  }
`;

const ActionsRow = styled.div`
  display: flex;
  gap: 0.75rem;
  align-items: center;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.5rem;
  @media (max-width: 992px) {
    grid-template-columns: 1fr;
  }
`;

// WhatsApp live message logger
const ChatCard = styled(Card)`
  display: flex;
  flex-direction: column;
  height: 600px;
  padding: 0;
  overflow: hidden;
`;

const ChatHeader = styled.div`
  padding: 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dadce0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #202124;
`;

const ChatBody = styled.div`
  flex: 1;
  padding: 1.25rem;
  overflow-y: auto;
  background-color: #efeae2; /* WhatsApp chat background */
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const ChatBubble = styled.div`
  max-width: 75%;
  padding: 0.5rem 0.875rem;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.4;
  position: relative;
  box-shadow: 0 1px 1px rgba(0,0,0,0.1);
  word-break: break-word;
  
  ${props => props.$sender === 'CANDIDATO' ? `
    align-self: flex-start;
    background-color: white;
    color: #303030;
    border-top-left-radius: 0;
  ` : `
    align-self: flex-end;
    background-color: #d9fdd3; /* WhatsApp bot light green bubble */
    color: #303030;
    border-top-right-radius: 0;
  `}
`;

const ChatTime = styled.span`
  display: block;
  font-size: 0.6875rem;
  color: #8696a0;
  text-align: right;
  margin-top: 0.25rem;
`;

const EmptyChat = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #5f6368;
  gap: 0.5rem;
  p { font-size: 0.875rem; }
`;

// Checklist Panel
const ChecklistPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
`;

const SectionHeader = styled.div`
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: #202124;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const DocList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const DocItem = styled.div`
  background: white;
  border: 1px solid #dadce0;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const DocTop = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const DocTitle = styled.span`
  font-weight: 600;
  font-size: 0.875rem;
  color: #202124;
`;

const QualityGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 0.25rem;
`;

const QualityItem = styled.span`
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-align: center;
  background-color: ${props => props.$valid === true ? '#e6f4ea' : (props.$valid === false ? '#fce8e6' : '#f1f3f4')};
  color: ${props => props.$valid === true ? '#137333' : (props.$valid === false ? '#c5221f' : '#5f6368')};
  font-weight: 500;
`;

const DocFeedback = styled.p`
  font-size: 0.75rem;
  color: #c5221f;
  background-color: #fdf6f6;
  border: 1px solid #fce8e6;
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.25rem;
`;

const ExtractedDataBox = styled.div`
  font-family: monospace;
  font-size: 0.75rem;
  background-color: #f8f9fa;
  padding: 0.5rem;
  border-radius: 4px;
  color: #3c4043;
  margin-top: 0.25rem;
  max-height: 120px;
  overflow-y: auto;
  white-space: pre-wrap;
`;

const Contratacoes = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeProcessId, setActiveProcessId] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [toast, setToast] = useState(null);

  // New candidate form states
  const [candidateName, setCandidateName] = useState('');
  const [candidateCargo, setCandidateCargo] = useState('');
  const [candidatePhone, setCandidatePhone] = useState('');

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  // Fetch Hirings
  const { data: contratacoes = [], isLoading: loadingList } = useQuery({
    queryKey: ['contratacoes'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/contratacoes/');
      return response.data;
    }
  });

  // Fetch Single Hiring Details (poll every 2 seconds when detail panel is open)
  const { data: activeProcess, isLoading: loadingDetail } = useQuery({
    queryKey: ['contratacaoDetail', activeProcessId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/contratacoes/${activeProcessId}`);
      return response.data;
    },
    enabled: !!activeProcessId,
    refetchInterval: !!activeProcessId ? 2000 : false
  });

  // Create Hiring Mutation
  const createMutation = useMutation({
    mutationFn: async (payload) => {
      const response = await axios.post('/api/v1/contratacoes/', payload);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['contratacoes'] });
      setIsCreateModalOpen(false);
      setCandidateName('');
      setCandidateCargo('');
      setCandidatePhone('');
      showToast('Candidato cadastrado com sucesso!');
      // Auto open detailed follow up
      setActiveProcessId(data.id);
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao cadastrar candidato.', 'error');
    }
  });

  // Delete Hiring Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.delete(`/api/v1/contratacoes/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contratacoes'] });
      if (activeProcessId) setActiveProcessId(null);
      showToast('Processo de contratação removido.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao remover contratação.', 'error');
    }
  });

  // Start Onboarding Mutation
  const startMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.post(`/api/v1/contratacoes/${id}/start`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contratacaoDetail', activeProcessId] });
      showToast('Workflow do WhatsApp iniciado com sucesso!');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Falha ao iniciar canal WhatsApp.', 'error');
    }
  });

  // Pause Onboarding Mutation
  const pauseMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.post(`/api/v1/contratacoes/${id}/pause`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contratacaoDetail', activeProcessId] });
      showToast('Workflow pausado. Atendimento em modo manual.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Falha ao pausar workflow.', 'error');
    }
  });

  // Resume Onboarding Mutation
  const resumeMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.post(`/api/v1/contratacoes/${id}/resume`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contratacaoDetail', activeProcessId] });
      showToast('Workflow automatizado retomado.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Falha ao retomar workflow.', 'error');
    }
  });

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (!candidateName || !candidateCargo || !candidatePhone) {
      showToast('Preencha todos os campos obrigatórios.', 'error');
      return;
    }
    // Clean telephone formatting: only numbers
    const cleanPhone = candidatePhone.replace(/\D/g, '');
    createMutation.mutate({
      nome_candidato: candidateName,
      cargo: candidateCargo,
      telefone: cleanPhone
    });
  };

  const handleDownloadZip = (id, name) => {
    // Standard window download for streaming ZIP attachment
    window.open(`/api/v1/contratacoes/${id}/download`, '_blank');
    showToast('Download do arquivo ZIP iniciado.');
  };

  // Stats calculation
  const stats = React.useMemo(() => {
    const running = contratacoes.filter(c => c.status === 'EM_ANDAMENTO').length;
    const completed = contratacoes.filter(c => c.status === 'CONCLUIDO').length;
    const paused = contratacoes.filter(c => c.status === 'INTERROMPIDO_HUMANO').length;
    return { running, completed, paused };
  }, [contratacoes]);

  const filteredData = contratacoes.filter(item => 
    item.nome_candidato.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.cargo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.telefone.includes(searchTerm)
  );

  const getStatusText = (status) => {
    switch (status) {
      case 'PENDENTE': return 'Não Iniciado';
      case 'EM_ANDAMENTO': return 'Em Andamento';
      case 'INTERROMPIDO_HUMANO': return 'Manual (RH)';
      case 'CONCLUIDO': return 'Admitido (Concluído)';
      case 'REJEITADO': return 'Rejeitado';
      default: return status;
    }
  };

  if (loadingList) return <Loader message="Carregando contratações..." />;

  return (
    <Container>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      {activeProcessId && activeProcess ? (
        // ════════════════════════ DETAILED TRACKING VIEW ════════════════════════
        <div>
          <div style={{ marginBottom: '1.25rem' }}>
            <Button variant="secondary" onClick={() => setActiveProcessId(null)} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <ArrowLeft size={16} />
              Voltar para Lista
            </Button>
          </div>

          <Card>
            <DetailHeader>
              <CandidateMeta>
                <h2>{activeProcess.nome_candidato}</h2>
                <p>Cargo Pretendido: <strong>{activeProcess.cargo}</strong></p>
                <p>Número de Contato: <strong>{activeProcess.telefone}</strong></p>
                <p>Data de Registro: <strong>{new Date(activeProcess.created_at).toLocaleDateString()}</strong></p>
              </CandidateMeta>
              
              <ActionsRow>
                <Badge $status={activeProcess.status} style={{ fontSize: '0.85rem', padding: '0.4rem 1rem' }}>
                  {activeProcess.status === 'CONCLUIDO' && <CheckCircle2 size={16} />}
                  {activeProcess.status === 'PENDENTE' && <AlertCircle size={16} />}
                  {activeProcess.status === 'EM_ANDAMENTO' && <Clock size={16} />}
                  {activeProcess.status === 'INTERROMPIDO_HUMANO' && <Pause size={16} />}
                  {activeProcess.status === 'REJEITADO' && <XCircle size={16} />}
                  {getStatusText(activeProcess.status)}
                </Badge>

                {/* Workflow state controllers */}
                {activeProcess.status === 'PENDENTE' && (
                  <Button onClick={() => startMutation.mutate(activeProcess.id)} disabled={startMutation.isPending}>
                    <Play size={16} />
                    Iniciar Contratação
                  </Button>
                )}

                {activeProcess.status === 'EM_ANDAMENTO' && (
                  <Button onClick={() => pauseMutation.mutate(activeProcess.id)} variant="outline" style={{ borderColor: '#e67e22', color: '#e67e22' }} disabled={pauseMutation.isPending}>
                    <Pause size={16} />
                    Interromper (Manual)
                  </Button>
                )}

                {activeProcess.status === 'INTERROMPIDO_HUMANO' && (
                  <Button onClick={() => resumeMutation.mutate(activeProcess.id)} style={{ backgroundColor: '#2ecc71', color: 'white' }} disabled={resumeMutation.isPending}>
                    <Play size={16} />
                    Retomar Robô
                  </Button>
                )}

                <Button 
                  variant="success" 
                  onClick={() => handleDownloadZip(activeProcess.id, activeProcess.nome_candidato)}
                  disabled={activeProcess.documentos.length === 0}
                >
                  <Download size={16} />
                  Baixar ZIP
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={() => { if(window.confirm('Excluir este processo permanentemente?')) deleteMutation.mutate(activeProcess.id); }}
                  style={{ borderColor: '#d93025', color: '#d93025' }}
                >
                  <Trash2 size={16} />
                </Button>
              </ActionsRow>
            </DetailHeader>

            <Grid>
              {/* WhatsApp conversation tracker */}
              <ChatCard>
                <ChatHeader>
                  <MessageSquare size={18} color="#128c7e" />
                  Visualização em Tempo Real (WhatsApp)
                </ChatHeader>
                <ChatBody>
                  {activeProcess.mensagens.length === 0 ? (
                    <EmptyChat>
                      <Clock size={36} color="#9aa0a6" />
                      <p>Nenhuma mensagem enviada ou recebida até o momento.</p>
                      <p style={{ fontSize: '0.75rem', fontStyle: 'italic' }}>Clique em "Iniciar Contratação" para acionar o robô.</p>
                    </EmptyChat>
                  ) : (
                    activeProcess.mensagens.map(msg => (
                      <ChatBubble key={msg.id} $sender={msg.sender}>
                        {msg.text}
                        <ChatTime>{new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</ChatTime>
                      </ChatBubble>
                    ))
                  )}
                </ChatBody>
              </ChatCard>

              {/* Documents Checklist & Extraction result */}
              <ChecklistPanel>
                <div>
                  <SectionHeader>
                    <ShieldCheck size={18} color="#1a73e8" />
                    Validação de Documentos
                  </SectionHeader>
                  <div style={{ fontSize: '0.8rem', color: '#5f6368', marginBottom: '0.75rem' }}>
                    Documentos e qualidade avaliados automaticamente por Inteligência Artificial
                  </div>
                  <DocList>
                    {[
                      { key: 'RG_FRENTE', label: 'RG (Frente)' },
                      { key: 'RG_VERSO', label: 'RG (Verso)' },
                      { key: 'CARTEIRA_TRABALHO', label: 'Carteira de Trabalho' },
                      { key: 'TITULO_ELEITOR', label: 'Título de Eleitor' },
                      { key: 'CERTIDAO_NASCIMENTO', label: 'Certidão de Nascimento' },
                      { key: 'COMPROVANTE_ESCOLARIDADE', label: 'Comprovante de Escolaridade' },
                      { key: 'CARTAO_VACINA', label: 'Cartão de Vacina' }
                    ].map(item => {
                      const doc = activeProcess.documentos.find(d => d.tipo_documento === item.key);
                      return (
                        <DocItem key={item.key}>
                          <DocTop>
                            <DocTitle>{item.label}</DocTitle>
                            {doc ? (
                              <Badge $status={doc.ocr_status === 'APROVADO' ? 'CONCLUIDO' : 'REJEITADO'}>
                                {doc.ocr_status === 'APROVADO' ? 'Validado' : 'Problema'}
                              </Badge>
                            ) : (
                              <span style={{ fontSize: '0.75rem', color: '#9aa0a6', fontStyle: 'italic' }}>Aguardando envio...</span>
                            )}
                          </DocTop>
                          {doc && (
                            <>
                              <QualityGrid>
                                <QualityItem $valid={doc.qualidade_valida}>Qualidade</QualityItem>
                                <QualityItem $valid={doc.validade_valida}>Validade</QualityItem>
                                <QualityItem $valid={doc.legitimidade_valida}>Estrutura</QualityItem>
                              </QualityGrid>
                              
                              {doc.ocr_status === 'REJEITADO' && doc.feedback_recusa && (
                                <DocFeedback>{doc.feedback_recusa}</DocFeedback>
                              )}
                              
                              {doc.ocr_status === 'APROVADO' && doc.extracted_data && doc.extracted_data !== '{}' && (
                                <div>
                                  <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#1a73e8' }}>Dados Extraídos:</span>
                                  <ExtractedDataBox>
                                    {JSON.stringify(JSON.parse(doc.extracted_data), null, 2)}
                                  </ExtractedDataBox>
                                </div>
                              )}
                            </>
                          )}
                        </DocItem>
                      );
                    })}
                  </DocList>
                </div>

                {/* Additional Questionnaire results */}
                <Card style={{ padding: '1rem', marginTop: '0.5rem' }}>
                  <SectionHeader>
                    <FileText size={18} color="#1a73e8" />
                    Respostas ao Questionário
                  </SectionHeader>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem', fontSize: '0.85rem' }}>
                    <div>
                      <span style={{ color: '#5f6368', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>Possui dependentes menores de 14 anos?</span>
                      <strong style={{ color: '#202124' }}>{activeProcess.possui_dependentes_14 || 'Aguardando...'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#5f6368', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>Optante pelo vale transporte?</span>
                      <strong style={{ color: '#202124' }}>{activeProcess.optante_vt || 'Aguardando...'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#5f6368', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>Dados Bancários informados:</span>
                      <pre style={{ margin: 0, fontFamily: 'inherit', fontWeight: 'bold', color: '#202124', whiteSpace: 'pre-wrap' }}>
                        {activeProcess.dados_bancarios || 'Aguardando...'}
                      </pre>
                    </div>
                  </div>
                </Card>
              </ChecklistPanel>
            </Grid>
          </Card>
        </div>
      ) : (
        // ════════════════════════ LIST VIEW ════════════════════════
        <>
          <PageTitle 
            title="Gestão de Contratações" 
            subtitle="Admissão automatizada de novos colaboradores via WhatsApp integrado à inteligência artificial" 
          />

          <StatsGrid>
            <StatCard>
              <StatIcon $bg="#e8f0fe" $color="#1a73e8">
                <UserPlus size={24} />
              </StatIcon>
              <StatInfo>
                <StatValue>{stats.running}</StatValue>
                <StatLabel>Em Andamento (Robô)</StatLabel>
              </StatInfo>
            </StatCard>

            <StatCard>
              <StatIcon $bg="#fef7e0" $color="#b06000">
                <Clock size={24} />
              </StatIcon>
              <StatInfo>
                <StatValue>{stats.paused}</StatValue>
                <StatLabel>Atendimento Manual (RH)</StatLabel>
              </StatInfo>
            </StatCard>

            <StatCard>
              <StatIcon $bg="#e6f4ea" $color="#137333">
                <CheckCircle2 size={24} />
              </StatIcon>
              <StatInfo>
                <StatValue>{stats.completed}</StatValue>
                <StatLabel>Admissões Concluídas</StatLabel>
              </StatInfo>
            </StatCard>
          </StatsGrid>

          <Card>
            <Toolbar>
              <SearchBox>
                <Search size={18} />
                <SearchInput 
                  type="text" 
                  placeholder="Buscar candidato ou cargo..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </SearchBox>

              <Button onClick={() => setIsCreateModalOpen(true)}>
                <Plus size={18} />
                Nova Contratação
              </Button>
            </Toolbar>

            <Table headers={["Candidato", "Cargo Pretendido", "Contato", "Data de Registro", "Status", "Ações"]}>
              {filteredData.map((item) => (
                <Tr key={item.id}>
                  <Td style={{ fontWeight: 600 }}>{item.nome_candidato}</Td>
                  <Td>{item.cargo}</Td>
                  <Td style={{ fontFamily: 'monospace' }}>{item.telefone}</Td>
                  <Td>{new Date(item.created_at).toLocaleDateString()}</Td>
                  <Td>
                    <Badge $status={item.status}>
                      {item.status === 'CONCLUIDO' && <CheckCircle2 size={12} />}
                      {item.status === 'PENDENTE' && <AlertCircle size={12} />}
                      {item.status === 'EM_ANDAMENTO' && <Clock size={12} />}
                      {item.status === 'INTERROMPIDO_HUMANO' && <Pause size={12} />}
                      {item.status === 'REJEITADO' && <XCircle size={12} />}
                      {getStatusText(item.status)}
                    </Badge>
                  </Td>
                  <Td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button variant="outline" onClick={() => setActiveProcessId(item.id)}>
                        Acompanhar
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => { if(window.confirm('Excluir esta contratação permanentemente?')) deleteMutation.mutate(item.id); }}
                        style={{ borderColor: '#d93025', color: '#d93025' }}
                      >
                        <Trash2 size={12} />
                      </Button>
                    </div>
                  </Td>
                </Tr>
              ))}
              {filteredData.length === 0 && (
                <Tr>
                  <Td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#5f6368' }}>
                    Nenhum candidato em contratação registrado.
                  </Td>
                </Tr>
              )}
            </Table>
          </Card>
        </>
      )}

      {/* New Hiring Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Iniciar Novo Processo de Contratação"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleCreateSubmit}>Cadastrar</Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit}>
          <Input 
            label="Nome Completo do Candidato *" 
            placeholder="Ex: João Souza da Silva"
            value={candidateName}
            onChange={(e) => setCandidateName(e.target.value)}
          />
          <Input 
            label="Cargo Pretendido *" 
            placeholder="Ex: Servente de Obras"
            value={candidateCargo}
            onChange={(e) => setCandidateCargo(e.target.value)}
            style={{ marginTop: '0.75rem' }}
          />
          <Input 
            label="WhatsApp (com DDD) *" 
            placeholder="Ex: 79999999999"
            value={candidatePhone}
            onChange={(e) => setCandidatePhone(e.target.value)}
            style={{ marginTop: '0.75rem' }}
          />
          <span style={{ fontSize: '0.75rem', color: '#5f6368', display: 'block', marginTop: '0.5rem', lineHeight: '1.4' }}>
            * Digite o telefone com o código do país (DDI) e DDD. Ex: 5579999999999. O robô enviará a primeira mensagem para este contato assim que o processo for iniciado.
          </span>
        </form>
      </Modal>
    </Container>
  );
};

export default Contratacoes;
