import React from 'react';
import styled from 'styled-components';
import { HelpCircle, ArrowLeft } from 'lucide-react';
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
  background-color: #f1f3f4;
  color: #5f6368;
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

const NotFound = () => {
  const handleBack = () => {
    window.location.href = '/dashboard';
  };

  return (
    <Container>
      <Wrapper>
        <IconBg>
          <HelpCircle size={28} />
        </IconBg>
        <Title>Página não encontrada</Title>
        <Message>
          A página que você está tentando acessar não existe ou foi movida temporariamente.
        </Message>
        <Button variant="secondary" onClick={handleBack}>
          <ArrowLeft size={16} />
          Voltar ao Início
        </Button>
      </Wrapper>
    </Container>
  );
};

export default NotFound;
