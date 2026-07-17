import React, { useState } from 'react';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/Button';
import { Clock, LogOut, RefreshCw } from 'lucide-react';
import Toast, { ToastContainer } from '../components/Toast';

const Container = styled.div`
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  padding: 1.5rem;
`;

const ContentWrapper = styled.div`
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(60, 64, 67, 0.1);
  padding: 3rem;
  max-width: 450px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid #dadce0;
`;

const IconWrapper = styled.div`
  background-color: #fef7e0;
  color: #f4b400;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
`;

const Title = styled.h1`
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #202124;
  margin-bottom: 1rem;
`;

const Message = styled.p`
  font-size: 0.875rem;
  color: #5f6368;
  line-height: 1.5;
  margin-bottom: 2rem;
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 1rem;
  width: 100%;
`;

const PrimeiroAcesso = () => {
  const { user, logout, checkCurrentUser } = useAuth();
  const [toast, setToast] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await checkCurrentUser();
      if (user && user.status === 'ATIVO') {
        window.location.href = '/dashboard';
      } else {
        setToast({ message: 'Seu acesso ainda está pendente de liberação.', variant: 'warning' });
      }
    } catch {
      setToast({ message: 'Falha ao atualizar dados de acesso.', variant: 'error' });
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <Container>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <ContentWrapper>
        <IconWrapper>
          <Clock size={32} />
        </IconWrapper>
        
        <Title>Aguarde a liberação</Title>
        
        <Message>
          Olá, <strong>{user?.full_name || 'Colaborador'}</strong>. Seu cadastro automático foi realizado com sucesso. 
          <br /><br />
          No entanto, por motivos de segurança corporativa, seu acesso deve ser explicitamente liberado por um administrador. Por favor, aguarde a liberação.
        </Message>

        <ButtonRow>
          <Button variant="outline" fullWidth onClick={logout} style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
            <LogOut size={16} />
            Sair
          </Button>
          <Button fullWidth onClick={handleRefresh} disabled={isRefreshing} style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
            <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
            Atualizar
          </Button>
        </ButtonRow>
      </ContentWrapper>
    </Container>
  );
};

export default PrimeiroAcesso;
