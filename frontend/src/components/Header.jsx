import React from 'react';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Briefcase, Eye } from 'lucide-react';

const Container = styled.header`
  height: 64px;
  background-color: white;
  border-bottom: 1px solid #dadce0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 2rem;
  position: fixed;
  top: 0;
  right: 0;
  left: 250px; /* Width of Sidebar */
  z-index: 99;
`;

const ProfileContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const Info = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
`;

const Name = styled.span`
  font-size: 0.875rem;
  font-weight: 600;
  color: #202124;
`;

const RoleBadge = styled.span`
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  
  ${({ $role }) => {
    if ($role === 'Administrador') return `
      background-color: #fce8e6;
      color: #d93025;
    `;
    if ($role === 'RH') return `
      background-color: #e6f4ea;
      color: #0f9d58;
    `;
    return `
      background-color: #e8f0fe;
      color: #1a73e8;
    `;
  }}
`;

const Avatar = styled.img`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #dadce0;
  object-fit: cover;
  background-color: #f1f3f4;
`;

const Header = () => {
  const { user } = useAuth();
  if (!user) return null;

  const role = user.roles && user.roles[0] ? user.roles[0] : 'Consulta';

  const getRoleIcon = () => {
    if (role === 'Administrador') return <Shield size={10} />;
    if (role === 'RH') return <Briefcase size={10} />;
    return <Eye size={10} />;
  };

  return (
    <Container>
      <ProfileContainer>
        <Info>
          <Name>{user.full_name}</Name>
          <RoleBadge $role={role}>
            {getRoleIcon()}
            {role}
          </RoleBadge>
        </Info>
        <Avatar src={user.picture_url || 'https://www.gravatar.com/avatar/?d=mp'} alt={user.full_name} />
      </ProfileContainer>
    </Container>
  );
};

export default Header;
export { RoleBadge };
