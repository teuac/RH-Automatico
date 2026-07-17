import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import { Table, Tr, Td } from '../components/Table';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Modal from '../components/Modal';
import Toast, { ToastContainer } from '../components/Toast';
import { ShieldCheck, ToggleLeft, ToggleRight, Check, X } from 'lucide-react';

const StatusBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  
  ${({ $status }) => {
    if ($status === 'ATIVO') return `
      background-color: #e6f4ea;
      color: #0f9d58;
    `;
    return `
      background-color: #fef7e0;
      color: #b06000;
    `;
  }}
`;

const RoleTag = styled.span`
  font-size: 0.75rem;
  background-color: #f1f3f4;
  color: #3c4043;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin-right: 0.25rem;
  font-weight: 500;
`;

const ModalContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #202124;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  &:hover {
    background-color: #f8f9fa;
  }
`;

const UserAvatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  background-color: #f1f3f4;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const Usuarios = () => {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState(null);
  
  const [editingUser, setEditingUser] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch Users
  const { data: users, isLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/usuarios/');
      return response.data;
    }
  });

  // Mutate Status
  const statusMutation = useMutation({
    mutationFn: async ({ userId, newStatus }) => {
      const response = await axios.put(`/api/v1/usuarios/${userId}/status`, { status: newStatus });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
      setToast({ message: `Status de ${data.email} atualizado para ${data.status}.`, variant: 'success' });
    },
    onError: (err) => {
      setToast({ message: err.response?.data?.detail || 'Erro ao alterar status.', variant: 'error' });
    }
  });

  // Mutate Roles
  const rolesMutation = useMutation({
    mutationFn: async ({ userId, roles }) => {
      const response = await axios.put(`/api/v1/usuarios/${userId}/roles`, { roles });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
      setIsModalOpen(false);
      setToast({ message: 'Perfis atualizados com sucesso.', variant: 'success' });
    },
    onError: (err) => {
      setToast({ message: err.response?.data?.detail || 'Erro ao alterar perfis.', variant: 'error' });
    }
  });

  const handleOpenRolesModal = (user) => {
    setEditingUser(user);
    setSelectedRoles(user.roles.map(r => r.name));
    setIsModalOpen(true);
  };

  const handleRoleToggle = (roleName) => {
    if (selectedRoles.includes(roleName)) {
      setSelectedRoles(selectedRoles.filter(r => r !== roleName));
    } else {
      setSelectedRoles([...selectedRoles, roleName]);
    }
  };

  const handleSaveRoles = () => {
    if (!editingUser) return;
    rolesMutation.mutate({
      userId: editingUser.id,
      roles: selectedRoles
    });
  };

  const handleToggleStatus = (user) => {
    const nextStatus = user.status === 'ATIVO' ? 'PENDENTE' : 'ATIVO';
    statusMutation.mutate({
      userId: user.id,
      newStatus: nextStatus
    });
  };

  if (isLoading) {
    return <Loader message="Carregando usuários..." />;
  }

  return (
    <div>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Gerenciamento de Usuários" 
        subtitle="Aprove novos colaboradores e atribua perfis de acesso" 
      />

      <Card>
        <Table headers={["Usuário", "E-mail", "Perfis", "Status", "Ações"]}>
          {users?.map(u => (
            <Tr key={u.id}>
              <Td>
                <UserInfo>
                  <UserAvatar src={u.picture_url || 'https://www.gravatar.com/avatar/?d=mp'} alt={u.full_name} />
                  <strong>{u.full_name}</strong>
                </UserInfo>
              </Td>
              <Td>{u.email}</Td>
              <Td>
                {u.roles?.map(r => (
                  <RoleTag key={r.id}>{r.name}</RoleTag>
                ))}
                {u.roles?.length === 0 && <span style={{ color: '#5f6368', fontSize: '0.8rem' }}>Sem perfil</span>}
              </Td>
              <Td>
                <StatusBadge $status={u.status}>{u.status}</StatusBadge>
              </Td>
              <Td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button variant="outline" onClick={() => handleOpenRolesModal(u)}>
                    <ShieldCheck size={14} />
                    Perfis
                  </Button>
                  <Button 
                    variant={u.status === 'ATIVO' ? 'danger' : 'success'} 
                    onClick={() => handleToggleStatus(u)}
                  >
                    {u.status === 'ATIVO' ? (
                      <>
                        <ToggleLeft size={14} />
                        Bloquear
                      </>
                    ) : (
                      <>
                        <ToggleRight size={14} />
                        Ativar
                      </>
                    )}
                  </Button>
                </div>
              </Td>
            </Tr>
          ))}
        </Table>
      </Card>

      {/* Roles Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Alterar Perfis de ${editingUser?.full_name}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleSaveRoles}>
              <Check size={16} />
              Salvar
            </Button>
          </>
        }
      >
        <ModalContent>
          <p style={{ fontSize: '0.875rem', color: '#5f6368', marginBottom: '0.5rem' }}>
            Selecione uma ou mais atribuições para este usuário.
          </p>
          <CheckboxLabel>
            <input 
              type="checkbox" 
              checked={selectedRoles.includes('Administrador')} 
              onChange={() => handleRoleToggle('Administrador')} 
            />
            <strong>Administrador</strong> - Controle total do sistema, usuários e logs.
          </CheckboxLabel>
          <CheckboxLabel>
            <input 
              type="checkbox" 
              checked={selectedRoles.includes('RH')} 
              onChange={() => handleRoleToggle('RH')} 
            />
            <strong>RH</strong> - Permissão para importar arquivos de presença e visualizar históricos.
          </CheckboxLabel>
          <CheckboxLabel>
            <input 
              type="checkbox" 
              checked={selectedRoles.includes('Consulta')} 
              onChange={() => handleRoleToggle('Consulta')} 
            />
            <strong>Consulta</strong> - Acesso exclusivo para visualização de relatórios e painéis.
          </CheckboxLabel>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default Usuarios;
