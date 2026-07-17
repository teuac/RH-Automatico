import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import { Table, Tr, Td } from '../components/Table';
import Button from '../components/Button';
import Input from '../components/Input';
import Loader from '../components/Loader';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import Toast, { ToastContainer } from '../components/Toast';
import { Plus, Edit2, Trash2, Check, ExternalLink } from 'lucide-react';

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

const ActionsHeader = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
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

const Obras = () => {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState(null);
  
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedObra, setSelectedObra] = useState(null);
  
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

  // Fetch Obras
  const { data: obras, isLoading } = useQuery({
    queryKey: ['adminObras'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/obras/');
      return response.data;
    }
  });

  const showToast = (message, variant = 'success') => {
    setToast({ message, variant });
  };

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/v1/obras/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminObras'] });
      setIsFormModalOpen(false);
      reset();
      showToast('Obra cadastrada com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao cadastrar obra.', 'error');
    }
  });

  // Update Mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await axios.put(`/api/v1/obras/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminObras'] });
      setIsFormModalOpen(false);
      reset();
      showToast('Obra atualizada com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao atualizar obra.', 'error');
    }
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await axios.delete(`/api/v1/obras/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminObras'] });
      setIsConfirmOpen(false);
      showToast('Obra excluída com sucesso.');
    },
    onError: (err) => {
      showToast(err.response?.data?.detail || 'Erro ao excluir obra.', 'error');
    }
  });

  const handleOpenCreate = () => {
    setSelectedObra(null);
    reset({
      nome: '',
      codigo: '',
      status: 'ATIVO',
      observacoes: ''
    });
    setIsFormModalOpen(true);
  };

  const handleOpenEdit = (obra) => {
    setSelectedObra(obra);
    reset({
      nome: obra.nome,
      codigo: obra.codigo,
      status: obra.status,
      observacoes: obra.observacoes || ''
    });
    setIsFormModalOpen(true);
  };

  const handleOpenDelete = (obra) => {
    setSelectedObra(obra);
    setIsConfirmOpen(true);
  };

  const onSubmit = (data) => {
    if (selectedObra) {
      updateMutation.mutate({ id: selectedObra.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleConfirmDelete = () => {
    if (!selectedObra) return;
    deleteMutation.mutate(selectedObra.id);
  };

  if (isLoading) {
    return <Loader message="Carregando obras..." />;
  }

  return (
    <div>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Gerenciamento de Obras" 
        subtitle="Cadastre e gerencie os canteiros de obras da empresa" 
      />

      <ActionsHeader>
        <Button onClick={handleOpenCreate}>
          <Plus size={16} />
          Cadastrar Obra
        </Button>
      </ActionsHeader>

      <Card>
        <Table headers={["Código", "Nome da Obra", "Status", "Ações"]}>
          {obras?.map(o => (
            <Tr key={o.id}>
              <Td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{o.codigo}</Td>
              <Td><strong>{o.nome}</strong></Td>
              <Td>
                <StatusBadge $status={o.status}>{o.status}</StatusBadge>
              </Td>
              <Td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button variant="outline" onClick={() => handleOpenEdit(o)}>
                    <Edit2 size={12} />
                    Editar
                  </Button>
                  <Button variant="outline" onClick={() => handleOpenDelete(o)} style={{ borderColor: '#d93025', color: '#d93025' }}>
                    <Trash2 size={12} />
                    Excluir
                  </Button>
                </div>
              </Td>
            </Tr>
          ))}
          {obras?.length === 0 && (
            <Tr>
              <Td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: '#5f6368' }}>
                Nenhuma obra cadastrada até o momento.
              </Td>
            </Tr>
          )}
        </Table>
      </Card>

      {/* Form Modal */}
      <Modal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        title={selectedObra ? `Editar Obra: ${selectedObra.nome}` : "Cadastrar Nova Obra"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsFormModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit(onSubmit)}>
              <Check size={16} />
              Confirmar
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormGrid>
            <Input 
              label="Nome da Obra" 
              placeholder="Ex: Residencial Alfa"
              error={errors.nome?.message}
              {...register('nome', { required: 'Nome da obra é obrigatório.' })}
            />
            <Input 
              label="Código da Obra" 
              placeholder="Ex: 002"
              error={errors.codigo?.message}
              disabled={!!selectedObra}
              {...register('codigo', { required: 'Código da obra é obrigatório.' })}
            />
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

      {/* Confirm Delete Dialog */}
      <ConfirmDialog 
        isOpen={isConfirmOpen}
        onClose={() => setIsConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Excluir Configuração de Obra"
        message={`Tem certeza que deseja excluir permanentemente a obra '${selectedObra?.nome}'? Isto não apagará nenhuma planilha no Google Drive, mas removerá o mapeamento interno.`}
        confirmText="Excluir"
        isDanger
      />
    </div>
  );
};

export default Obras;
