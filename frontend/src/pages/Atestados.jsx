import React, { useState, useMemo } from 'react';
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
import { FileCheck, Search, Plus, Calendar, CheckCircle2, Clock, Stethoscope, Edit2, Trash2, XCircle, FileText, Eye, Paperclip } from 'lucide-react';

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

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;

  background-color: ${props => {
    switch (props.$type) {
      case 'HOMOLOGADO': return '#e6f4ea';
      case 'PENDENTE': return '#fef7e0';
      case 'CANCELADO': return '#fce8e6';
      default: return '#f1f3f4';
    }
  }};

  color: ${props => {
    switch (props.$type) {
      case 'HOMOLOGADO': return '#137333';
      case 'PENDENTE': return '#b06000';
      case 'CANCELADO': return '#c5221f';
      default: return '#5f6368';
    }
  }};
`;

const FormContainer = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
`;

const FormRow = styled.div`
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

const ActionButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  color: ${props => props.$color || '#5f6368'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s;

  &:hover {
    background-color: #f1f3f4;
  }
`;

const getDocumentUrl = (url) => {
  if (!url) return '#';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  return `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;
};

const Atestados = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('TODOS');
  const [toast, setToast] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedAtestado, setSelectedAtestado] = useState(null);
  const [docFile, setDocFile] = useState(null);

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm();
  const watchStart = watch('data_inicio');
  const watchEnd = watch('data_fim');

  // Fetch Atestados
  const { data: atestados, isLoading } = useQuery({
    queryKey: ['atestadosList'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/atestados/');
      return response.data;
    }
  });

  // Fetch Active Colaboradores for dropdown
  const { data: colaboradores } = useQuery({
    queryKey: ['colaboradoresForAtestado'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/colaboradores/');
      return response.data;
    }
  });

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  // Calculate days dynamically
  const calculatedDays = useMemo(() => {
    if (watchStart && watchEnd) {
      const s = new Date(watchStart);
      const e = new Date(watchEnd);
      if (!isNaN(s) && !isNaN(e) && e >= s) {
        const diffTime = Math.abs(e - s);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      }
    }
    return 1;
  }, [watchStart, watchEnd]);

  // Document Upload helper
  const uploadDocumentFile = async (atestadoId, fileToUpload) => {
    if (!fileToUpload) return;
    const formData = new FormData();
    formData.append('file', fileToUpload);
    await axios.post(`/api/v1/atestados/${atestadoId}/documento`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  };

  // Mutations
  const createMutation = useMutation({
    mutationFn: async ({ payload, fileToUpload }) => {
      const response = await axios.post('/api/v1/atestados/', payload);
      const newAtestado = response.data;
      if (fileToUpload) {
        await uploadDocumentFile(newAtestado.id, fileToUpload);
      }
      return newAtestado;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atestadosList'] });
      setIsModalOpen(false);
      setDocFile(null);
      reset();
      showToast('Atestado médico e comprovante cadastrados com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao cadastrar atestado.', 'error');
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload, fileToUpload }) => {
      const response = await axios.put(`/api/v1/atestados/${id}`, payload);
      if (fileToUpload) {
        await uploadDocumentFile(id, fileToUpload);
      }
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atestadosList'] });
      setIsModalOpen(false);
      setDocFile(null);
      reset();
      showToast('Atestado atualizado com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao atualizar atestado.', 'error');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.delete(`/api/v1/atestados/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atestadosList'] });
      setIsConfirmOpen(false);
      showToast('Atestado removido com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao remover atestado.', 'error');
    }
  });

  const handleOpenCreate = () => {
    setSelectedAtestado(null);
    setDocFile(null);
    const today = new Date().toISOString().split('T')[0];
    reset({
      colaborador_id: '',
      data_inicio: today,
      data_fim: today,
      cid: '',
      motivo: '',
      status: 'HOMOLOGADO',
      observacoes: ''
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (atestado) => {
    setSelectedAtestado(atestado);
    setDocFile(null);
    reset({
      colaborador_id: atestado.colaborador_id,
      data_inicio: atestado.data_inicio,
      data_fim: atestado.data_fim,
      cid: atestado.cid || '',
      motivo: atestado.motivo || '',
      status: atestado.status,
      observacoes: atestado.observacoes || ''
    });
    setIsModalOpen(true);
  };

  const handleOpenDelete = (atestado) => {
    setSelectedAtestado(atestado);
    setIsConfirmOpen(true);
  };

  const onSubmit = (data) => {
    const payload = {
      ...data,
      colaborador_id: Number(data.colaborador_id),
      dias: calculatedDays
    };
    if (selectedAtestado) {
      updateMutation.mutate({ id: selectedAtestado.id, payload, fileToUpload: docFile });
    } else {
      createMutation.mutate({ payload, fileToUpload: docFile });
    }
  };

  const handleConfirmDelete = () => {
    if (selectedAtestado) {
      deleteMutation.mutate(selectedAtestado.id);
    }
  };

  // Filtered List & Stats
  const filteredData = useMemo(() => {
    if (!atestados) return [];
    return atestados.filter(item => {
      const matchesStatus = statusFilter === 'TODOS' || item.status === statusFilter;
      const colabName = item.colaborador?.nome || '';
      const colabMat = item.colaborador?.matricula || '';
      const cidStr = item.cid || '';
      const matchesSearch = 
        colabName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        colabMat.includes(searchTerm) ||
        cidStr.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [atestados, searchTerm, statusFilter]);

  const stats = useMemo(() => {
    if (!atestados) return { total: 0, pendentes: 0, diasAfastamento: 0 };
    const homologados = atestados.filter(a => a.status === 'HOMOLOGADO');
    const pendentes = atestados.filter(a => a.status === 'PENDENTE');
    const totalDias = homologados.reduce((acc, curr) => acc + (curr.dias || 0), 0);

    return {
      total: atestados.length,
      pendentes: pendentes.length,
      diasAfastamento: totalDias
    };
  }, [atestados]);

  if (isLoading) {
    return <Loader message="Carregando registros de atestados..." />;
  }

  return (
    <Container>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Gestão de Atestados Médicos" 
        subtitle="Lançamento, validação e controle de afastamentos de saúde dos colaboradores" 
      />

      <StatsGrid>
        <StatCard>
          <StatIcon $bg="#e8f0fe" $color="#1a73e8">
            <Stethoscope size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.total}</StatValue>
            <StatLabel>Atestados Cadastrados</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#fef7e0" $color="#b06000">
            <Clock size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.pendentes}</StatValue>
            <StatLabel>Pendentes de Validação</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#e6f4ea" $color="#137333">
            <Calendar size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.diasAfastamento}</StatValue>
            <StatLabel>Dias de Afastamento</StatLabel>
          </StatInfo>
        </StatCard>
      </StatsGrid>

      <Card>
        <Toolbar>
          <div style={{ display: 'flex', gap: '1rem', flex: 1, flexWrap: 'wrap' }}>
            <SearchBox>
              <Search size={18} />
              <SearchInput 
                type="text" 
                placeholder="Buscar colaborador, matrícula ou CID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </SearchBox>

            <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="TODOS">Todos os Status</option>
              <option value="HOMOLOGADO">Homologados</option>
              <option value="PENDENTE">Pendentes</option>
              <option value="CANCELADO">Cancelados</option>
            </Select>
          </div>

          <Button onClick={handleOpenCreate}>
            <Plus size={18} />
            Lançar Atestado
          </Button>
        </Toolbar>

        <Table headers={["Matrícula", "Colaborador", "Obra", "CID / Motivo", "Período de Afastamento", "Dias", "Status", "Documento", "Ações"]}>
          {filteredData.map((item) => (
            <Tr key={item.id}>
              <Td style={{ fontWeight: 600 }}>{item.colaborador?.matricula || '-'}</Td>
              <Td style={{ fontWeight: 600 }}>{item.colaborador?.nome || '-'}</Td>
              <Td style={{ fontSize: '0.8rem', color: '#5f6368' }}>
                {item.colaborador?.obra?.nome ? `${item.colaborador.obra.nome} (${item.colaborador.obra.codigo})` : 'Sem Obra'}
              </Td>
              <Td>{item.cid ? `CID: ${item.cid}` : (item.motivo || '-')}</Td>
              <Td>{item.data_inicio} a {item.data_fim}</Td>
              <Td style={{ fontWeight: 600, color: '#1a73e8' }}>{item.dias} dia(s)</Td>
              <Td>
                <Badge $type={item.status}>
                  {item.status === 'HOMOLOGADO' && <CheckCircle2 size={14} />}
                  {item.status === 'PENDENTE' && <Clock size={14} />}
                  {item.status === 'CANCELADO' && <XCircle size={14} />}
                  {item.status}
                </Badge>
              </Td>
              <Td>
                {item.documento_url ? (
                  <a 
                    href={getDocumentUrl(item.documento_url)} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{ 
                      display: 'inline-flex', 
                      alignItems: 'center', 
                      gap: '0.35rem', 
                      color: '#1a73e8', 
                      fontWeight: 600, 
                      textDecoration: 'none', 
                      fontSize: '0.8rem',
                      backgroundColor: '#e8f0fe',
                      padding: '0.25rem 0.625rem',
                      borderRadius: '4px'
                    }}
                  >
                    <FileText size={14} />
                    Ver Documento
                  </a>
                ) : (
                  <span style={{ color: '#9aa0a6', fontSize: '0.8rem' }}>Sem anexo</span>
                )}
              </Td>
              <Td>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <ActionButton title="Editar Atestado" onClick={() => handleOpenEdit(item)}>
                    <Edit2 size={16} />
                  </ActionButton>
                  <ActionButton title="Excluir Atestado" $color="#d93025" onClick={() => handleOpenDelete(item)}>
                    <Trash2 size={16} />
                  </ActionButton>
                </div>
              </Td>
            </Tr>
          ))}
        </Table>
      </Card>

      {/* Create/Edit Modal */}
      {isModalOpen && (
        <Modal 
          isOpen={isModalOpen} 
          onClose={() => setIsModalOpen(false)}
          title={selectedAtestado ? 'Editar Atestado Médico' : 'Lançar Novo Atestado Médico'}
        >
          <FormContainer onSubmit={handleSubmit(onSubmit)}>
            <FormGroup>
              <Label>Colaborador *</Label>
              <Select 
                {...register('colaborador_id', { required: 'Selecione o colaborador' })}
              >
                <option value="">-- Selecione o Colaborador --</option>
                {colaboradores?.filter(c => c.status === 'ATIVO').map(c => (
                  <option key={c.id} value={c.id}>
                    {c.nome} ({c.matricula}) {c.obra?.nome ? `- ${c.obra.nome}` : ''}
                  </option>
                ))}
              </Select>
              {errors.colaborador_id && <span style={{ color: '#d93025', fontSize: '0.75rem' }}>{errors.colaborador_id.message}</span>}
            </FormGroup>

            <FormRow>
              <FormGroup>
                <Label>Data de Início *</Label>
                <Input 
                  type="date" 
                  {...register('data_inicio', { required: 'Selecione a data inicial' })} 
                />
              </FormGroup>

              <FormGroup>
                <Label>Data de Fim *</Label>
                <Input 
                  type="date" 
                  {...register('data_fim', { required: 'Selecione a data final' })} 
                />
              </FormGroup>
            </FormRow>

            <div style={{ backgroundColor: '#e8f0fe', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '0.85rem', color: '#1a73e8', fontWeight: 600 }}>
              Duração Calculada: {calculatedDays} dia(s) de afastamento
            </div>

            <FormRow>
              <FormGroup>
                <Label>Código CID (Opcional)</Label>
                <Input 
                  placeholder="Ex: M54.5" 
                  {...register('cid')} 
                />
              </FormGroup>

              <FormGroup>
                <Label>Status *</Label>
                <Select {...register('status')}>
                  <option value="HOMOLOGADO">Homologado</option>
                  <option value="PENDENTE">Pendente de Validação</option>
                  <option value="CANCELADO">Cancelado</option>
                </Select>
              </FormGroup>
            </FormRow>

            <FormGroup>
              <Label>Motivo / Descrição</Label>
              <Input 
                placeholder="Ex: Lombalgia aguda" 
                {...register('motivo')} 
              />
            </FormGroup>

            <FormGroup>
              <Label>Anexar Foto ou PDF do Atestado</Label>
              <input 
                type="file" 
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setDocFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
                style={{ 
                  fontFamily: 'Inter, sans-serif', 
                  fontSize: '0.85rem', 
                  padding: '0.5rem', 
                  borderRadius: '6px', 
                  border: '1px solid #dadce0',
                  backgroundColor: '#f8f9fa'
                }}
              />
              {selectedAtestado?.documento_url && !docFile && (
                <div style={{ marginTop: '0.375rem', fontSize: '0.8rem' }}>
                  <a 
                    href={getDocumentUrl(selectedAtestado.documento_url)} 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ color: '#1a73e8', fontWeight: 600, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                  >
                    <Paperclip size={14} />
                    Ver comprovante atualmente cadastrado
                  </a>
                </div>
              )}
            </FormGroup>

            <FormGroup>
              <Label>Observações Adicionais</Label>
              <textarea 
                rows="3" 
                style={{ 
                  fontFamily: 'Inter, sans-serif', 
                  fontSize: '0.875rem', 
                  padding: '0.5rem 0.75rem', 
                  borderRadius: '6px', 
                  border: '1px solid #dadce0', 
                  outline: 'none',
                  resize: 'vertical'
                }}
                {...register('observacoes')} 
              />
            </FormGroup>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit">
                {selectedAtestado ? 'Salvar Alterações' : 'Cadastrar Atestado'}
              </Button>
            </div>
          </FormContainer>
        </Modal>
      )}

      {/* Delete Confirm Dialog */}
      {isConfirmOpen && (
        <ConfirmDialog 
          isOpen={isConfirmOpen}
          onClose={() => setIsConfirmOpen(false)}
          onConfirm={handleConfirmDelete}
          title="Excluir Atestado Médico"
          message={`Tem certeza de que deseja remover o atestado de ${selectedAtestado?.colaborador?.nome}?`}
        />
      )}
    </Container>
  );
};

export default Atestados;
