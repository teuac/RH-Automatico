import React from 'react';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import { RoleBadge } from '../components/Header';
import { Mail, Calendar, ShieldCheck, CheckCircle } from 'lucide-react';

const ProfileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  
  @media (max-width: 576px) {
    flex-direction: column;
    text-align: center;
  }
`;

const LargeAvatar = styled.img`
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 3px solid #1a73e8;
  object-fit: cover;
  background-color: #f1f3f4;
`;

const HeaderInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
  
  @media (max-width: 576px) {
    align-items: center;
  }
`;

const ProfileName = styled.h2`
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #202124;
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  background-color: #f8f9fa;
  border: 1px solid #e8eaed;
`;

const MetaLabel = styled.span`
  font-size: 0.8125rem;
  color: #5f6368;
  font-weight: 500;
`;

const MetaValue = styled.span`
  font-size: 0.875rem;
  color: #202124;
  font-weight: 600;
  margin-left: auto;
`;

const SectionTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #202124;
  margin-bottom: 1rem;
`;

const PermissionList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
`;

const PermissionBadge = styled.span`
  font-family: monospace;
  font-size: 0.75rem;
  background-color: #f1f3f4;
  color: #3c4043;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid #dadce0;
`;

const InfoText = styled.p`
  font-size: 0.8125rem;
  color: #5f6368;
  line-height: 1.4;
`;

const MeuPerfil = () => {
  const { user } = useAuth();
  if (!user) return null;

  const role = user.roles && user.roles[0] ? user.roles[0] : 'Consulta';

  return (
    <div>
      <PageTitle 
        title="Meu Perfil" 
        subtitle="Confira suas informações cadastrais e atribuições de permissão" 
      />

      <Card>
        <ProfileHeader>
          <LargeAvatar src={user.picture_url || 'https://www.gravatar.com/avatar/?d=mp'} alt={user.full_name} />
          <HeaderInfo>
            <ProfileName>{user.full_name}</ProfileName>
            <RoleBadge $role={role} style={{ fontSize: '0.8rem', padding: '0.25rem 0.75rem' }}>
              {role}
            </RoleBadge>
          </HeaderInfo>
        </ProfileHeader>

        <InfoGrid>
          <div>
            <SectionTitle>Detalhes Cadastrais</SectionTitle>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <MetaItem>
                <Mail size={16} color="#1a73e8" />
                <MetaLabel>E-mail Corporativo</MetaLabel>
                <MetaValue>{user.email}</MetaValue>
              </MetaItem>

              <MetaItem>
                <CheckCircle size={16} color="#0f9d58" />
                <MetaLabel>Status da Conta</MetaLabel>
                <MetaValue style={{ color: '#0f9d58' }}>ATIVO</MetaValue>
              </MetaItem>

              <MetaItem>
                <Calendar size={16} color="#1a73e8" />
                <MetaLabel>Data de Acesso</MetaLabel>
                <MetaValue>{new Date().toLocaleDateString('pt-BR')}</MetaValue>
              </MetaItem>
            </div>
          </div>

          <div>
            <SectionTitle>Suas Permissões Ativas</SectionTitle>
            <InfoText style={{ fontSize: '0.8rem', color: '#5f6368', marginBottom: '1rem', lineHeight: '1.4' }}>
              Com base no seu perfil corporativo, as seguintes chaves de acesso estão liberadas no sistema para sua conta:
            </InfoText>
            
            <PermissionList>
              {user.permissions && user.permissions.length > 0 ? (
                user.permissions.map((perm, idx) => (
                  <PermissionBadge key={idx}>{perm}</PermissionBadge>
                ))
              ) : role === 'Administrador' ? (
                <PermissionBadge>*</PermissionBadge>
              ) : (
                <span style={{ fontSize: '0.8rem', color: '#5f6368' }}>Visualização padrão</span>
              )}
            </PermissionList>
          </div>
        </InfoGrid>
      </Card>
    </div>
  );
};

export default MeuPerfil;
