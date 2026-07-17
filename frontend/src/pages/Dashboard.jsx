import React from 'react';
import styled from 'styled-components';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  Building, 
  UploadCloud, 
  AlertTriangle, 
  Users, 
  Clock, 
  Calendar 
} from 'lucide-react';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import Loader from '../components/Loader';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
`;

const ContentRow = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  
  @media (max-width: 992px) {
    grid-template-columns: 1fr;
  }
`;

const ChartContainer = styled.div`
  background-color: white;
  border-radius: 8px;
  border: 1px solid #dadce0;
  padding: 1.5rem;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.1);
  display: flex;
  flex-direction: column;
  height: 350px;
`;

const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const ChartTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #202124;
`;

const InfoBox = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const DetailItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  background-color: #f8f9fa;
  border: 1px solid #e8eaed;
`;

const DetailLabel = styled.span`
  font-size: 0.8125rem;
  color: #5f6368;
  font-weight: 500;
`;

const DetailValue = styled.span`
  font-size: 0.875rem;
  color: #202124;
  font-weight: 600;
  margin-left: auto;
`;

const Dashboard = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/dashboard/stats');
      return response.data;
    },
    refetchInterval: 10000, // Refresh dashboard metrics every 10 seconds
  });

  if (isLoading) {
    return <Loader message="Carregando métricas do painel..." />;
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#d93025' }}>
        <h3>Falha ao carregar métricas</h3>
        <p>{error.message}</p>
      </div>
    );
  }

  const chartData = stats.upload_graph && stats.upload_graph.length > 0 
    ? stats.upload_graph 
    : [
        { date: 'Sem dados', uploads: 0 }
      ];

  return (
    <div>
      <PageTitle 
        title="Painel de Controle" 
        subtitle="Visão geral da sincronização e processamento de ponto" 
      />

      <Grid>
        <Card 
          title="Obras Ativas" 
          value={stats.total_obras} 
          description="Cadastradas e sincronizando"
          icon={<Building size={20} color="#1a73e8" />}
          hoverable
        />
        <Card 
          title="Uploads Hoje" 
          value={stats.uploads_today} 
          description="Arquivos de ponto processados"
          icon={<UploadCloud size={20} color="#0f9d58" />}
          hoverable
        />
        <Card 
          title="Pendências" 
          value={stats.pending_count} 
          description="Aguardando ajuste de planilha"
          icon={<AlertTriangle size={20} color={stats.pending_count > 0 ? "#f4b400" : "#5f6368"} />}
          hoverable
        />
        <Card 
          title="Colaboradores Ativos" 
          value={stats.active_users} 
          description="Usuários liberados no sistema"
          icon={<Users size={20} color="#1a73e8" />}
          hoverable
        />
      </Grid>

      <ContentRow>
        <ChartContainer>
          <ChartHeader>
            <ChartTitle>Processamentos Recentes</ChartTitle>
            <span style={{ fontSize: '0.75rem', color: '#5f6368', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Calendar size={12} />
              Últimos 7 dias
            </span>
          </ChartHeader>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f3f4" />
              <XAxis dataKey="date" stroke="#5f6368" fontSize={11} tickLine={false} />
              <YAxis stroke="#5f6368" fontSize={11} tickLine={false} allowDecimals={false} />
              <Tooltip cursor={{ fill: '#f8f9fa' }} />
              <Bar dataKey="uploads" fill="#1a73e8" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <InfoBox>
          <Card title="Eficiência do Sistema">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
              <DetailItem>
                <Clock size={16} color="#1a73e8" />
                <DetailLabel>Latência do Google Sheets</DetailLabel>
                <DetailValue>
                  {stats.last_processing_time > 0 
                    ? `${(stats.last_processing_time / 1000).toFixed(2)}s` 
                    : 'Sem registros'}
                </DetailValue>
              </DetailItem>

              <DetailItem>
                <AlertTriangle size={16} color={stats.pending_count > 0 ? "#f4b400" : "#0f9d58"} />
                <DetailLabel>Registros com Alerta</DetailLabel>
                <DetailValue>{stats.pending_count}</DetailValue>
              </DetailItem>

              <DetailItem>
                <Building size={16} color="#1a73e8" />
                <DetailLabel>Taxa de Cobertura</DetailLabel>
                <DetailValue>100%</DetailValue>
              </DetailItem>
            </div>
          </Card>
        </InfoBox>
      </ContentRow>
    </div>
  );
};

export default Dashboard;
