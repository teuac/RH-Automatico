import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import Input from '../components/Input';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import Toast, { ToastContainer } from '../components/Toast';
import { Table, Tr, Td } from '../components/Table';
import { Save, ShieldAlert, KeyRound, Globe, Plus, Edit2, Trash2, Check, ExternalLink, FileSpreadsheet, Bus, MessageSquare, Bot } from 'lucide-react';

const TabContainer = styled.div`
  display: flex;
  gap: 1.5rem;
  border-bottom: 2px solid #dadce0;
  margin-bottom: 2rem;
  padding-bottom: 2px;
`;

const TabButton = styled.button`
  font-family: 'Outfit', sans-serif;
  font-size: 0.9375rem;
  font-weight: 600;
  padding: 0.5rem 0.5rem 0.75rem 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  color: ${props => props.$active ? '#1a73e8' : '#5f6368'};
  border-bottom: 3px solid ${props => props.$active ? '#1a73e8' : 'transparent'};
  margin-bottom: -3px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  &:hover {
    color: #1a73e8;
  }
`;


const FormContainer = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 650px;
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #dadce0;
  padding-bottom: 0.5rem;
`;

const SectionTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #202124;
`;

const InfoText = styled.p`
  font-size: 0.8125rem;
  color: #5f6368;
  margin-bottom: 1rem;
  line-height: 1.4;
`;

const StatusBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  
  ${({ $status }) => $status === 'ATIVO' ? `
    background-color: #e6f4ea;
    color: #0f9d58;
  ` : `
    background-color: #f1f3f4;
    color: #5f6368;
  `}
`;

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  @media (max-width: 576px) {
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

const StatusBox = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background-color: ${({ $status }) => {
    if ($status === 'CONECTADO') return '#e6f4ea';
    if ($status === 'NAO_CONFIGURADO') return '#f1f3f4';
    return '#fce8e6';
  }};
  border: 1px solid ${({ $status }) => {
    if ($status === 'CONECTADO') return '#34a853';
    if ($status === 'NAO_CONFIGURADO') return '#dadce0';
    return '#ea4335';
  }};
  color: ${({ $status }) => {
    if ($status === 'CONECTADO') return '#137333';
    if ($status === 'NAO_CONFIGURADO') return '#5f6368';
    return '#c5221f';
  }};
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
`;

const StatusMessage = styled.p`
  font-size: 0.8125rem;
  color: #5f6368;
  line-height: 1.4;
  margin-top: 0.25rem;
`;

const Configuracoes = () => {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState(null);
  const [allowedDomain, setAllowedDomain] = useState('');
  const [valorDiarioVT, setValorDiarioVT] = useState('12.00');

  // WhatsApp settings state
  const [evolutionUrl, setEvolutionUrl] = useState('');
  const [evolutionToken, setEvolutionToken] = useState('');
  const [evolutionInstance, setEvolutionInstance] = useState('');
  const [backendExternalUrl, setBackendExternalUrl] = useState('');
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [activeTab, setActiveTab] = useState('planilhas');



  // Planilha CRUD states
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedPlanilha, setSelectedPlanilha] = useState(null);
  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm();
  const watchedAutomacao = watch('automacao', 'ALIMENTACAO');


  // Fetch Settings
  const { data: settings, isLoading: loadingSettings } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/settings/');
      return response.data;
    }
  });

  // Fetch Google Sheets Connection Status
  const { data: connectionStatus, isLoading: loadingStatus } = useQuery({
    queryKey: ['googleSheetsStatus'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/settings/google-sheets-status');
      return response.data;
    }
  });

  // Fetch Planilhas
  const { data: planilhas, isLoading: loadingPlanilhas } = useQuery({
    queryKey: ['adminPlanilhas'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/planilhas/');
      return response.data;
    }
  });

  // Fetch Active Obras
  const { data: obras, isLoading: loadingObras } = useQuery({
    queryKey: ['adminObrasConfig'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/obras/');
      return response.data;
    }
  });

  useEffect(() => {
    if (settings) {
      setAllowedDomain(settings.ALLOWED_DOMAIN || 'acengenharia.com.br');
      setValorDiarioVT(settings.valor_diario_vt || '12.00');
      setEvolutionUrl(settings.EVOLUTION_API_URL || '');
      setEvolutionToken(settings.EVOLUTION_API_TOKEN || '');
      setEvolutionInstance(settings.EVOLUTION_API_INSTANCE || '');
      setBackendExternalUrl(settings.BACKEND_EXTERNAL_URL || '');
    }
  }, [settings]);


  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  // Update Settings Mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async ({ key, value }) => {
      const response = await axios.post(`/api/v1/settings/?key=${key}&value=${value}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemSettings'] });
      showToast('Configuração global salva com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao salvar configuração global.', 'error');
    }
  });

  // Create Planilha Mutation
  const createPlanilhaMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/v1/planilhas/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPlanilhas'] });
      setIsFormModalOpen(false);
      reset();
      showToast('Planilha cadastrada com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao cadastrar planilha.', 'error');
    }
  });

  // Update Planilha Mutation
  const updatePlanilhaMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await axios.put(`/api/v1/planilhas/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPlanilhas'] });
      setIsFormModalOpen(false);
      reset();
      showToast('Planilha atualizada com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao atualizar planilha.', 'error');
    }
  });

  // Delete Planilha Mutation
  const deletePlanilhaMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.delete(`/api/v1/planilhas/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminPlanilhas'] });
      setIsConfirmOpen(false);
      showToast('Planilha excluída com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao excluir planilha.', 'error');
    }
  });

  const handleSaveSettings = (e) => {
    e.preventDefault();
    updateSettingsMutation.mutate({ key: 'ALLOWED_DOMAIN', value: allowedDomain });
  };

  const handleSaveVT = (e) => {
    e.preventDefault();
    updateSettingsMutation.mutate({ key: 'valor_diario_vt', value: valorDiarioVT });
  };


  const handleSaveWhatsappSettings = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/v1/settings/?key=EVOLUTION_API_URL&value=${encodeURIComponent(evolutionUrl)}`);
      await axios.post(`/api/v1/settings/?key=EVOLUTION_API_TOKEN&value=${encodeURIComponent(evolutionToken)}`);
      await axios.post(`/api/v1/settings/?key=EVOLUTION_API_INSTANCE&value=${encodeURIComponent(evolutionInstance)}`);
      await axios.post(`/api/v1/settings/?key=BACKEND_EXTERNAL_URL&value=${encodeURIComponent(backendExternalUrl)}`);
      
      queryClient.invalidateQueries({ queryKey: ['systemSettings'] });
      showToast('Configurações do WhatsApp salvas com sucesso.');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Erro ao salvar credenciais do WhatsApp.', 'error');
    }
  };

  const handleTestWhatsapp = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const response = await axios.post('/api/v1/settings/test-whatsapp');
      setTestResult(response.data);
    } catch (err) {
      setTestResult({
        status: 'ERROR',
        message: err.response?.data?.detail || 'Erro ao comunicar com o servidor.'
      });
    } finally {
      setTestingConnection(false);
    }
  };


  const handleOpenCreatePlanilha = () => {
    setSelectedPlanilha(null);
    reset({
      nome: '',
      planilha_google_id: '',
      nome_aba: '',
      automacao: 'ALIMENTACAO',
      obra_id: '',
      status: 'ATIVO',
      observacoes: ''
    });
    setIsFormModalOpen(true);
  };

  const handleOpenEditPlanilha = (planilha) => {
    setSelectedPlanilha(planilha);
    reset({
      nome: planilha.nome,
      planilha_google_id: planilha.planilha_google_id,
      nome_aba: planilha.nome_aba,
      automacao: planilha.automacao || 'ALIMENTACAO',
      obra_id: planilha.obra_id || '',
      status: planilha.status,
      observacoes: planilha.observacoes || ''
    });
    setIsFormModalOpen(true);
  };

  const handleOpenDeletePlanilha = (planilha) => {
    setSelectedPlanilha(planilha);
    setIsConfirmOpen(true);
  };

  const onPlanilhaSubmit = (data) => {
    const payload = {
      ...data,
      obra_id: data.obra_id ? Number(data.obra_id) : null,
      // Para ALIMENTACAO, nome_aba é gerenciado automaticamente pelo backend
      nome_aba: data.automacao === 'ALIMENTACAO' ? (data.nome_aba || null) : data.nome_aba
    };
    if (selectedPlanilha) {
      updatePlanilhaMutation.mutate({ id: selectedPlanilha.id, data: payload });
    } else {
      createPlanilhaMutation.mutate(payload);
    }
  };

  const handleConfirmDeletePlanilha = () => {
    if (!selectedPlanilha) return;
    deletePlanilhaMutation.mutate(selectedPlanilha.id);
  };

  if (loadingSettings || loadingPlanilhas || loadingObras || loadingStatus) {
    return <Loader message="Carregando configurações..." />;
  }

  return (
    <div>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Configurações do Sistema" 
        subtitle="Gerencie restrições de segurança globais, status de credenciais Google e planilhas integradas" 
      />

      <TabContainer>
        <TabButton $active={activeTab === 'planilhas'} onClick={() => setActiveTab('planilhas')}>
          <FileSpreadsheet size={16} style={{ marginRight: '0.5rem' }} />
          Planilhas Google
        </TabButton>
        <TabButton $active={activeTab === 'seguranca_conexao'} onClick={() => setActiveTab('seguranca_conexao')}>
          <KeyRound size={16} style={{ marginRight: '0.5rem' }} />
          Segurança e Conexão
        </TabButton>
        <TabButton $active={activeTab === 'parametros'} onClick={() => setActiveTab('parametros')}>
          <Bus size={16} style={{ marginRight: '0.5rem' }} />
          Parâmetros
        </TabButton>
        <TabButton $active={activeTab === 'whatsapp'} onClick={() => setActiveTab('whatsapp')}>
          <MessageSquare size={16} style={{ marginRight: '0.5rem' }} />
          WhatsApp (Evolution API)
        </TabButton>
      </TabContainer>


      {activeTab === 'planilhas' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <SectionHeader style={{ border: 'none', marginBottom: 0, paddingBottom: 0 }}>
                <FileSpreadsheet size={20} color="#1a73e8" />
                <SectionTitle>Cadastro de Planilhas Google</SectionTitle>
              </SectionHeader>
              <Button onClick={handleOpenCreatePlanilha}>
                <Plus size={16} />
                Cadastrar Planilha
              </Button>
            </div>

            <Card>
              <Table headers={["Nome Descritivo", "Spreadsheet ID", "Nome da Aba", "Obra Vinculada", "Automação", "Status", "Ações"]}>
                {planilhas?.map(p => (
                  <Tr key={p.id}>
                    <Td><strong>{p.nome}</strong></Td>
                    <Td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#5f6368' }}>
                          {p.planilha_google_id.substring(0, 10)}...
                        </span>
                        <a 
                          href={`https://docs.google.com/spreadsheets/d/${p.planilha_google_id}`} 
                          target="_blank" 
                          rel="noreferrer"
                          style={{ color: '#1a73e8', display: 'flex', alignItems: 'center' }}
                        >
                          <ExternalLink size={12} />
                        </a>
                      </div>
                    </Td>
                    <Td>
                      {p.automacao === 'ALIMENTACAO' ? (
                        <span style={{ color: '#1a73e8', fontSize: '0.8rem', fontStyle: 'italic' }}>Auto (por mês)</span>
                      ) : (
                        p.nome_aba
                      )}
                    </Td>
                    <Td>
                      {p.obra ? (
                        <span style={{ fontWeight: 500, color: '#202124' }}>{p.obra.nome}</span>
                      ) : (
                        <span style={{ color: '#9aa0a6', fontStyle: 'italic' }}>Não vinculada</span>
                      )}
                    </Td>
                    <Td>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#1a73e8' }}>
                        {p.automacao === 'ALIMENTACAO' ? 'Alimentação' : 'Controle VT'}
                      </span>
                    </Td>
                    <Td>
                      <StatusBadge $status={p.status}>{p.status}</StatusBadge>
                    </Td>
                    <Td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button variant="outline" onClick={() => handleOpenEditPlanilha(p)}>
                          <Edit2 size={12} />
                          Editar
                        </Button>
                        <Button variant="outline" onClick={() => handleOpenDeletePlanilha(p)} style={{ borderColor: '#d93025', color: '#d93025' }}>
                          <Trash2 size={12} />
                          Excluir
                        </Button>
                      </div>
                    </Td>
                  </Tr>
                ))}
                {planilhas?.length === 0 && (
                  <Tr>
                    <Td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#5f6368' }}>
                      Nenhuma planilha Google cadastrada até o momento.
                    </Td>
                  </Tr>
                )}
              </Table>
            </Card>
          </div>

          <Card style={{ backgroundColor: '#fdf6f6', borderColor: '#fce8e6' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <ShieldAlert size={20} color="#d93025" style={{ flexShrink: 0, marginTop: '0.125rem' }} />
              <div>
                <strong style={{ color: '#d93025', fontSize: '0.9rem' }}>Atenção sobre Integração de Planilhas</strong>
                <p style={{ fontSize: '0.8rem', color: '#60100b', marginTop: '0.25rem', lineHeight: '1.4' }}>
                  Para que a sincronização funcione perfeitamente, certifique-se de compartilhar cada planilha cadastrada com o e-mail da conta de serviço (Service Account) configurada no seu arquivo <code>.env</code>, atribuindo o perfil de <strong>Editor</strong>.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'seguranca_conexao' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          <Card>
            <FormContainer onSubmit={handleSaveSettings}>
              <div>
                <SectionHeader>
                  <Globe size={18} color="#1a73e8" />
                  <SectionTitle>Segurança de Login</SectionTitle>
                </SectionHeader>
                <InfoText>
                  Limite os cadastros e logins automáticos a e-mails corporativos vinculados a um domínio específico do Google Workspace.
                </InfoText>
                <Input 
                  label="Domínio Google Workspace Permitido" 
                  value={allowedDomain} 
                  onChange={(e) => setAllowedDomain(e.target.value)} 
                  placeholder="Ex: acengenharia.com.br"
                />
              </div>

              <div>
                <SectionHeader>
                  <KeyRound size={18} color="#1a73e8" />
                  <SectionTitle>Conexão com Google Sheets</SectionTitle>
                </SectionHeader>
                <InfoText>
                  As credenciais da conta de serviço (Service Account) são carregadas de forma segura diretamente através do arquivo <code>.env</code> do servidor.
                </InfoText>
                
                {connectionStatus && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <StatusBox $status={connectionStatus.status}>
                      {connectionStatus.status === 'CONECTADO' ? (
                        <>
                          <Check size={16} style={{ strokeWidth: 3 }} />
                          CONECTADO
                        </>
                      ) : (
                        <>
                          <ShieldAlert size={16} />
                          {connectionStatus.status === 'NAO_CONFIGURADO' ? 'NÃO CONFIGURADO' : 'ERRO DE AUTENTICAÇÃO'}
                        </>
                      )}
                    </StatusBox>
                    <StatusMessage>{connectionStatus.message}</StatusMessage>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #dadce0', paddingTop: '1.5rem', marginTop: '1rem' }}>
                <Button type="submit">
                  <Save size={16} />
                  Salvar Configurações
                </Button>
              </div>
            </FormContainer>
          </Card>
        </div>
      )}

      {activeTab === 'parametros' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          <Card>
            <FormContainer onSubmit={handleSaveVT}>
              <div>
                <SectionHeader>
                  <Bus size={18} color="#1a73e8" />
                  <SectionTitle>Parâmetros de Vale Transporte (VT)</SectionTitle>
                </SectionHeader>
                <InfoText>
                  Defina o valor padrão por dia (R$) utilizado para o cálculo dos totais de Vale Transporte.
                </InfoText>
                <Input 
                  label="Valor Padrão por Dia (R$)" 
                  value={valorDiarioVT} 
                  onChange={(e) => setValorDiarioVT(e.target.value)} 
                  placeholder="Ex: 12.00"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #dadce0', paddingTop: '1.5rem', marginTop: '1rem' }}>
                <Button type="submit">
                  <Save size={16} />
                  Salvar Parâmetros
                </Button>
              </div>
            </FormContainer>
          </Card>
        </div>
      )}

      {activeTab === 'whatsapp' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
          <Card>
            <FormContainer onSubmit={handleSaveWhatsappSettings}>
              <div>
                <SectionHeader>
                  <MessageSquare size={18} color="#1a73e8" />
                  <SectionTitle>Credenciais do WhatsApp (Evolution API)</SectionTitle>
                </SectionHeader>
                <InfoText>
                  Configure as chaves de acesso para integração com o WhatsApp da Evolution API. A automação enviará mensagens de onboarding e coletará documentos do candidato automaticamente.
                </InfoText>
                <FormGrid>
                  <FormGroup>
                    <Label>URL da Evolution API</Label>
                    <Input 
                      value={evolutionUrl} 
                      onChange={(e) => setEvolutionUrl(e.target.value)} 
                      placeholder="Ex: https://api.evolution.suaempresa.com"
                    />
                  </FormGroup>
                  <FormGroup>
                    <Label>Instância do WhatsApp</Label>
                    <Input 
                      value={evolutionInstance} 
                      onChange={(e) => setEvolutionInstance(e.target.value)} 
                      placeholder="Ex: rh_onboarding"
                    />
                  </FormGroup>
                </FormGrid>
                <FormGroup style={{ marginTop: '1rem' }}>
                  <Label>Token/API Key da Evolution API</Label>
                  <Input 
                    type="password"
                    value={evolutionToken} 
                    onChange={(e) => setEvolutionToken(e.target.value)} 
                    placeholder="Token de autorização global ou da instância"
                  />
                </FormGroup>
              </div>


              <div>
                <SectionHeader>
                  <Globe size={18} color="#1a73e8" />
                  <SectionTitle>Endereço de Retorno (Webhook)</SectionTitle>
                </SectionHeader>
                <InfoText>
                  URL externa deste servidor para receber mensagens do WhatsApp. O sistema tentará registrar este link automaticamente.
                </InfoText>
                <FormGroup>
                  <Label>URL Externa do Backend</Label>
                  <Input 
                    value={backendExternalUrl} 
                    onChange={(e) => setBackendExternalUrl(e.target.value)} 
                    placeholder="Ex: https://rh.suaempresa.com"
                  />
                </FormGroup>
              </div>

              {testResult && (
                <div style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  backgroundColor: testResult.status === 'SUCCESS' ? '#e6f4ea' : (testResult.status === 'WARNING' ? '#fef7e0' : '#fce8e6'),
                  border: '1px solid',
                  borderColor: testResult.status === 'SUCCESS' ? '#34a853' : (testResult.status === 'WARNING' ? '#fbc02d' : '#ea4335'),
                  color: testResult.status === 'SUCCESS' ? '#137333' : (testResult.status === 'WARNING' ? '#b06000' : '#c5221f'),
                  fontSize: '0.875rem',
                  fontWeight: 500
                }}>
                  {testResult.message}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #dadce0', paddingTop: '1.5rem', marginTop: '1rem' }}>
                <Button type="button" variant="outline" onClick={handleTestWhatsapp} disabled={testingConnection || !evolutionUrl}>
                  {testingConnection ? 'Testando...' : 'Testar Conexão WhatsApp'}
                </Button>
                <Button type="submit">
                  <Save size={16} />
                  Salvar Configurações WhatsApp
                </Button>
              </div>
            </FormContainer>
          </Card>
        </div>
      )}

      {/* Planilha Form Modal */}
      <Modal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        title={selectedPlanilha ? `Editar Planilha: ${selectedPlanilha.nome}` : "Cadastrar Nova Planilha"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsFormModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit(onPlanilhaSubmit)}>
              <Check size={16} />
              Confirmar
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit(onPlanilhaSubmit)}>
          <Input 
            label="Nome Descritivo da Planilha" 
            placeholder="Ex: Planilha de Refeições Sul"
            error={errors.nome?.message}
            {...register('nome', { required: 'Nome descritivo é obrigatório.' })}
          />

          <FormGrid style={{ marginTop: '0.5rem' }}>
            <FormGroup>
              <Label>Obra Vinculada</Label>
              <Select {...register('obra_id', { required: 'Selecione uma obra vinculada.' })}>
                <option value="">Selecione...</option>
                {obras?.map(o => (
                  <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
                ))}
              </Select>
              {errors.obra_id && <span style={{ color: '#d93025', fontSize: '0.75rem' }}>{errors.obra_id.message}</span>}
            </FormGroup>

            <FormGroup>
              <Label>Tipo de Automação</Label>
              <Select {...register('automacao')}>
                <option value="ALIMENTACAO">Controle de Alimentação</option>
                <option value="CONTROLE_VT">Controle VT</option>
              </Select>
            </FormGroup>
          </FormGrid>

          <FormGrid style={{ marginTop: '0.5rem' }}>
            <Input 
              label="Planilha Google ID" 
              placeholder="Ex: 1aB2c3D4e5F6g7..."
              error={errors.planilha_google_id?.message}
              {...register('planilha_google_id', { required: 'Spreadsheet ID é obrigatório.' })}
            />
            {watchedAutomacao !== 'ALIMENTACAO' && (
              <Input 
                label="Nome da Aba" 
                placeholder="Ex: Presenca_Julho"
                error={errors.nome_aba?.message}
                {...register('nome_aba', {
                  required: watchedAutomacao !== 'ALIMENTACAO' ? 'Nome da aba é obrigatório.' : false
                })}
              />
            )}
            {watchedAutomacao === 'ALIMENTACAO' && (
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', paddingBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#3c4043', marginBottom: '0.375rem' }}>Nome da Aba</span>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.5rem 0.75rem', borderRadius: '6px',
                  background: 'linear-gradient(135deg, #e8f0fe, #e6f4ea)',
                  border: '1px solid #1a73e8', color: '#1a73e8',
                  fontSize: '0.8rem', fontWeight: 600, minHeight: '38px'
                }}>
                  ✨ Criada automaticamente por mês
                </div>
              </div>
            )}
          </FormGrid>

          <FormGroup style={{ marginTop: '0.5rem' }}>
            <Label>Status</Label>
            <Select {...register('status')}>
              <option value="ATIVO">ATIVO</option>
              <option value="INATIVO">INATIVO</option>
            </Select>
          </FormGroup>

          <Input 
            label="Observações" 
            placeholder="Informações adicionais..."
            style={{ marginTop: '0.5rem' }}
            {...register('observacoes')}
          />
        </form>
      </Modal>

      {/* Confirm Delete Planilha Dialog */}
      <ConfirmDialog 
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={handleConfirmDeletePlanilha}
        title="Excluir Configuração de Planilha"
        message={`Tem certeza que deseja excluir permanentemente a configuração da planilha '${selectedPlanilha?.nome}'? Isto removerá a integração da automação com esta planilha.`}
        confirmText="Excluir"
        isDanger
      />
    </div>
  );
};

export default Configuracoes;
