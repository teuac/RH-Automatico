import React, { useState } from 'react';
import styled from 'styled-components';
import { FileCheck, Search, Plus, Calendar, CheckCircle2, Clock, FileText, Stethoscope } from 'lucide-react';
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
      case 'HOMOLOGADO': return '#e6f4ea';
      case 'PENDENTE': return '#fef7e0';
      default: return '#f1f3f4';
    }
  }};

  color: ${props => {
    switch (props.$type) {
      case 'HOMOLOGADO': return '#137333';
      case 'PENDENTE': return '#b06000';
      default: return '#5f6368';
    }
  }};
`;

const MockData = [
  { id: 1, colaborador: 'José Carlos dos Santos', matricula: '001798', dias: 2, cid: 'J11 (Gripe)', inicio: '21/07/2026', status: 'HOMOLOGADO', statusText: 'Homologado' },
  { id: 2, colaborador: 'Maria Oliveira', matricula: '001799', dias: 1, cid: 'M54 (Lumbago)', inicio: '20/07/2026', status: 'HOMOLOGADO', statusText: 'Homologado' },
  { id: 3, colaborador: 'Antônio Ferreira', matricula: '001802', dias: 3, cid: 'K29 (Gastrite)', inicio: '19/07/2026', status: 'PENDENTE', statusText: 'Em Validação' },
];

const Atestados = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredData = MockData.filter(item => 
    item.colaborador.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.matricula.includes(searchTerm) ||
    item.cid.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container>
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
            <StatValue>14</StatValue>
            <StatLabel>Atestados no Mês</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#fef7e0" $color="#b06000">
            <Clock size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>1</StatValue>
            <StatLabel>Pendente de Validação</StatLabel>
          </StatInfo>
        </StatCard>

        <StatCard>
          <StatIcon $bg="#e6f4ea" $color="#137333">
            <Calendar size={24} />
          </StatIcon>
          <StatInfo>
            <StatValue>24</StatValue>
            <StatLabel>Dias de Afastamento</StatLabel>
          </StatInfo>
        </StatCard>
      </StatsGrid>

      <Card>
        <Toolbar>
          <SearchBox>
            <Search size={18} />
            <SearchInput 
              type="text" 
              placeholder="Buscar colaborador, matrícula ou CID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchBox>

          <Button>
            <Plus size={18} />
            Lançar Atestado
          </Button>
        </Toolbar>

        <Table>
          <thead>
            <tr>
              <Th>Matrícula</Th>
              <Th>Colaborador</Th>
              <Th>Motivo / CID</Th>
              <Th>Data Início</Th>
              <Th>Dias</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr key={item.id}>
                <Td style={{ fontWeight: 600 }}>{item.matricula}</Td>
                <Td style={{ fontWeight: 600 }}>{item.colaborador}</Td>
                <Td>{item.cid}</Td>
                <Td>{item.inicio}</Td>
                <Td>{item.dias} dia(s)</Td>
                <Td>
                  <Badge $type={item.status}>
                    {item.status === 'HOMOLOGADO' ? <CheckCircle2 size={14} /> : <Clock size={14} />}
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

export default Atestados;
