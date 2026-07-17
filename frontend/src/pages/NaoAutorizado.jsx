import React from 'react';
import styled from 'styled-components';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Button from '../components/Button';

const Container = styled.div`
  display: flex;
  min-height: calc(100vh - 120px);
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
`;

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 400px;
`;

const IconBg = styled.div`
  background-color: #fce8e6;
  color: #d93025;
  width: 56px;
  height: 56px;
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
  margin-bottom: 0.75rem;
`;

const Message = styled.p`
  font-size: 0.875rem;
  color: #5f6368;
  line-height: 1.5;
  margin-bottom: 1.5rem;
`;

const NaoAutorizado = () => {
  const handleBack = () => {
    window.location.href = '/dashboard';
  };

  return (
    <Container>
      <Wrapper>
        <IconBg>
          <ShieldAlert size={28} />
        </IconBg>
        <Title>Acesso Não Autorizado</Title>
        <Message>
          Você não possui os privilégios necessários para visualizar esta tela. Se você acredita que isto é um erro, entre em contato com o suporte de TI.
        </Message>
        <Button variant="secondary" onClick={handleBack}>
          <ArrowLeft size={16} />
          Voltar ao Painel
        </Button>
      </Wrapper>
    </Container>
  );
};

export default NaoAutorizado;
