import React, { useState } from 'react';
import styled from 'styled-components';
import { UserPlus, Search, Filter, Plus, FileText, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';

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

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background-color: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #1557b0;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
`;

const Th = styled.th`
  padding: 0.875rem 1rem;
  background-color: #f8f9fa;
  color: #5f6368;
  font-weight: 600;
  border-bottom: 1px solid #e0e0e0;
`;

const Td = styled.td`
  padding: 1rem;
  border-bottom: 1px solid #f1f3f4;
  color: #202124;
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
      case 'APROVADO': return '#e6f4ea';
      case 'PENDENTE': return '#fef7e0';
      case 'EM_ANALISE': return '#e8f0fe';
      default: return '#f1f3f4';
    }
  }};

  color: ${props => {
    switch (props.$type) {
      case 'APROVADO': return '#137333';
      case 'PENDENTE': return '#b06000';
      case 'EM_ANALISE': return '#1a73e8';
      default: return '#5f6368';
    }
  }};
`;

const MockData = [
  { id: 1, nome: 'Carlos Eduardo Mendes', cargo: 'Servente de Obras', obra: 'Residencial Alfa', data: '22/07/2026', status: 'PENDENTE', statusText: 'Doc. Pendentes' },
  { id: 2, nome: 'Ana Paula Ferreira', cargo: 'Técnica de Segurança', obra: 'Condomínio Sol', data: '20/07/2026', status: 'EM_ANALISE', statusText: 'Em Análise' },
  { id: 3, nome: 'Roberto da Silva Costa', cargo: 'Pedreiro', obra: 'Residencial Alfa', data: '18/07/2026', status: 'APROVADO', statusText: 'Admitido' },
  { id: 4, nome: 'Lucas de Oliveira', cargo: 'Encarregado', obra: 'Torre Horizon', data: '15/07/2026', status: 'APROVADO', statusText: 'Admitido' },
];

const Contratacoes = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredData = MockData.filter(item => 
    item.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.cargo.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.obra.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container>
      <PageTitle 
        title="Gestão de Contratações" 
        subtitle="Acompanhamento do processo seletivo, documentação e admissão de novos colaboradores" 
      />

      <StatsGrid>
        <StatCard>
          <StatIcon $bg="#e8f0fe" $color="#1a73e8">
            <UserPlus size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>12</StatValue>
            <StatLabel>Processos em Andamento</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#fef7e0" $color="#b06000">
            <Clock size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>5</StatValue>
            <StatLabel>Documentos Pendentes</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#e6f4ea" $color="#137333">
            <CheckCircle2 size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>18</StatValue>
            <StatLabel>Admissões no Mês</StatLabel>
          </StatInfo>
        </StatCard>
      </StatsGrid>

      <Card>
        <Toolbar>
          <SearchBox>
            <Search size={18} />
            <SearchInput 
              type="text" 
              placeholder="Buscar candidato, cargo ou obra..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchBox>

          <Button>
            <Plus size={18} />
            Nova Contratação
          </Button>
        </Toolbar>

        <Table>
          <thead>
            <tr>
              <Th>Candidato</Th>
              <Th>Cargo Pretendido</Th>
              <Th>Obra Destino</Th>
              <Th>Data Solicitação</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr key={item.id}>
                <Td style={{ fontWeight: 600 }}>{item.nome}</Td>
                <Td>{item.cargo}</Td>
                <Td>{item.obra}</Td>
                <Td>{item.data}</Td>
                <Td>
                  <Badge $type={item.status}>
                    {item.status === 'APROVADO' && <CheckCircle2 size={14} />}
                    {item.status === 'PENDENTE' && <AlertCircle size={14} />}
                    {item.status === 'EM_ANALISE' && <Clock size={14} />}
                    {item.statusText}
                  </Badge>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </Container>
  );
};

export default Contratacoes;
