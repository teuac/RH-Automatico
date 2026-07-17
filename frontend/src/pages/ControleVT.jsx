import React from 'react';
import styled, { keyframes } from 'styled-components';
import { Bus, Clock } from 'lucide-react';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';

const bounce = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
`;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  text-align: center;
  min-height: 50vh;
`;

const IconBg = styled.div`
  background-color: #e8f0fe;
  color: #1a73e8;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  animation: ${bounce} 2s ease-in-out infinite;
`;

const Title = styled.h2`
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #202124;
  margin-bottom: 0.75rem;
`;

const Message = styled.p`
  font-size: 0.9rem;
  color: #5f6368;
  line-height: 1.5;
  max-width: 400px;
  margin-bottom: 2rem;
`;

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  background-color: #fef7e0;
  color: #b06000;
  padding: 0.25rem 0.75rem;
  border-radius: 50px;
  border: 1px solid #fce8e6;
`;

const ControleVT = () => {
  return (
    <div>
      <PageTitle 
        title="Controle de Vale Transporte" 
        subtitle="Portal de solicitação, aprovação e recarga de VT corporativo" 
      />

      <Card>
        <Container>
          <IconBg>
            <Bus size={36} />
          </IconBg>
          <Title>Módulo em Desenvolvimento</Title>
          <Message>
            Este recurso está sendo implementado para centralizar a gestão de benefícios de transporte dos colaboradores da Acengenharia.
          </Message>
          <Badge>
            <Clock size={12} />
            Disponível em breve
          </Badge>
        </Container>
      </Card>
    </div>
  );
};

export default ControleVT;
