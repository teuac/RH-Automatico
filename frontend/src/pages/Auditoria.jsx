import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import { Table, Tr, Td } from '../components/Table';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Modal, { ModalBody, ModalFooter } from '../components/Modal';
import SearchBar from '../components/SearchBar';
import { Eye, Filter, Calendar, ShieldAlert } from 'lucide-react';

const FiltersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: flex-end;
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
`;

const DateInput = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
`;

const ResultBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  
  ${({ $result }) => {
    if ($result === 'SUCESSO') return `
      background-color: #e6f4ea;
      color: #0f9d58;
    `;
    if ($result === 'SUCESSO_COM_PENDENCIAS') return `
      background-color: #fef7e0;
      color: #b06000;
    `;
    return `
      background-color: #fce8e6;
      color: #d93025;
    `;
  }}
`;

const Pre = styled.pre`
  background-color: #f1f3f4;
  padding: 1rem;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.8rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
`;

const DetailRow = styled.div`
  display: flex;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  line-height: 1.4;
`;

const DetailLabel = styled.span`
  font-weight: 600;
  color: #3c4043;
  width: 150px;
  flex-shrink: 0;
`;

const DetailValue = styled.span`
  color: #202124;
`;

const Auditoria = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  
  const [selectedLog, setSelectedLog] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Fetch logs
  const { data: logs, isLoading, refetch } = useQuery({
    queryKey: ['auditLogs', startDate, endDate, userEmail, actionFilter, moduleFilter],
    queryFn: async () => {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (userEmail) params.user_email = userEmail;
      if (actionFilter) params.action = actionFilter;
      if (moduleFilter) params.module = moduleFilter;

      const response = await axios.get('/api/v1/auditoria/', { params });
      return response.data;
    }
  });

  const handleOpenDetails = (log) => {
    setSelectedLog(log);
    setIsModalOpen(true);
  };

  const formatJson = (jsonStr) => {
    if (!jsonStr) return 'Sem dados';
    try {
      const obj = JSON.parse(jsonStr);
      return JSON.stringify(obj, null, 2);
    } catch {
      return jsonStr;
    }
  };

  return (
    <div>
      <PageTitle 
        title="Trilha de Auditoria" 
        subtitle="Rastreabilidade completa de todas as ações e alterações realizadas no portal" 
      />

      <Card>
        <FiltersGrid>
          <FormGroup>
            <Label>Data Inicial</Label>
            <DateInput 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)} 
            />
          </FormGroup>
          <FormGroup>
            <Label>Data Final</Label>
            <DateInput 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)} 
            />
          </FormGroup>
          <FormGroup>
            <Label>Filtrar por Usuário (Email)</Label>
            <DateInput 
              type="text" 
              placeholder="Ex: joao@..."
              value={userEmail} 
              onChange={(e) => setUserEmail(e.target.value)} 
            />
          </FormGroup>
          <FormGroup>
            <Label>Ação</Label>
            <Select 
              value={actionFilter} 
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <option value="">Todas</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
              <option value="IMPORT">IMPORT</option>
            </Select>
          </FormGroup>
          <FormGroup>
            <Label>Módulo</Label>
            <Select 
              value={moduleFilter} 
              onChange={(e) => setModuleFilter(e.target.value)}
            >
              <option value="">Todos</option>
              <option value="Upload">Upload</option>
              <option value="Configuracoes">Configurações / Cadastro</option>
            </Select>
          </FormGroup>
        </FiltersGrid>

        {isLoading ? (
          <Loader message="Carregando auditoria..." />
        ) : (
          <Table headers={["Data / Hora", "Usuário", "Módulo", "Ação", "Descrição", "Resultado", "Detalhes"]}>
            {logs?.map((log) => (
              <Tr key={log.id}>
                <Td style={{ whiteSpace: 'nowrap' }}>
                  {log.action_date} {log.action_time}
                </Td>
                <Td>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <strong>{log.user_name}</strong>
                    <span style={{ fontSize: '0.75rem', color: '#5f6368' }}>{log.user_email}</span>
                  </div>
                </Td>
                <Td>{log.module}</Td>
                <Td><strong>{log.action}</strong></Td>
                <Td>{log.description}</Td>
                <Td>
                  <ResultBadge $result={log.result}>{log.result}</ResultBadge>
                </Td>
                <Td>
                  <Button variant="outline" onClick={() => handleOpenDetails(log)}>
                    <Eye size={14} />
                    Ver
                  </Button>
                </Td>
              </Tr>
            ))}
            {logs?.length === 0 && (
              <Tr>
                <Td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#5f6368' }}>
                  <ShieldAlert size={32} style={{ marginBottom: '0.5rem' }} />
                  <br />Nenhum registro de auditoria encontrado.
                </Td>
              </Tr>
            )}
          </Table>
        )}
      </Card>

      {/* Audit Detail Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Detalhes do Log de Auditoria"
        size="large"
        footer={
          <Button onClick={() => setIsModalOpen(false)}>Fechar</Button>
        }
      >
        {selectedLog && (
          <div>
            <DetailRow>
              <DetailLabel>ID do Log:</DetailLabel>
              <DetailValue>{selectedLog.id}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Data/Hora:</DetailLabel>
              <DetailValue>{selectedLog.action_date} às {selectedLog.action_time}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Colaborador:</DetailLabel>
              <DetailValue>{selectedLog.user_name} ({selectedLog.user_email})</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Endereço IP:</DetailLabel>
              <DetailValue style={{ fontFamily: 'monospace' }}>{selectedLog.ip_address}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>User Agent:</DetailLabel>
              <DetailValue style={{ fontSize: '0.8rem' }}>{selectedLog.user_agent}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Módulo / Tela:</DetailLabel>
              <DetailValue>{selectedLog.module} / {selectedLog.screen}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Ação Realizada:</DetailLabel>
              <DetailValue><strong>{selectedLog.action}</strong></DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Descrição:</DetailLabel>
              <DetailValue>{selectedLog.description}</DetailValue>
            </DetailRow>
            <DetailRow>
              <DetailLabel>Objeto / ID:</DetailLabel>
              <DetailValue>{selectedLog.object_changed} (ID: {selectedLog.object_id})</DetailValue>
            </DetailRow>
            
            <hr style={{ border: 'none', borderTop: '1px solid #dadce0', margin: '1.5rem 0' }} />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#5f6368' }}>Estado Anterior (Antes)</h4>
                <Pre>{formatJson(selectedLog.before_state)}</Pre>
              </div>
              <div>
                <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#5f6368' }}>Estado Posterior (Depois)</h4>
                <Pre>{formatJson(selectedLog.after_state)}</Pre>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Auditoria;
