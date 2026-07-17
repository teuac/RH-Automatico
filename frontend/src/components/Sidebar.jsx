import React from 'react';
import { NavLink } from 'react-router-dom';
import styled from 'styled-components';
import { 
  LayoutDashboard, 
  Utensils, 
  Bus,
  ClipboardList, 
  Users, 
  Building, 
  Settings, 
  User, 
  LogOut,
  HardHat
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Container = styled.aside`
  width: 250px;
  background-color: white;
  border-right: 1px solid #dadce0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  padding: 1.5rem 0;
`;

const LogoContainer = styled.div`
  padding: 0 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
`;

const LogoText = styled.h2`
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a73e8;
  letter-spacing: -0.5px;
`;

const LogoSubtext = styled.span`
  font-size: 0.75rem;
  color: #5f6368;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 1px;
  margin-top: 0.25rem;
`;

const NavList = styled.nav`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  padding: 0 0.75rem;
`;

const NavItem = styled(NavLink)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: #5f6368;
  text-decoration: none;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;

  &:hover {
    background-color: #f1f3f4;
    color: #202124;
  }

  &.active {
    background-color: #e8f0fe;
    color: #1a73e8;
  }
`;

const Footer = styled.div`
  padding: 0 0.75rem;
  border-top: 1px solid #e8eaed;
  margin-top: auto;
  padding-top: 1rem;
`;

const LogoutButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  width: 100%;
  border: none;
  background: none;
  color: #d93025;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: left;
  transition: background-color 0.15s;

  &:hover {
    background-color: #fce8e6;
  }
`;

const SectionLabel = styled.div`
  font-family: 'Inter', sans-serif;
  font-size: 0.6875rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #1a73e8;
  background-color: #e8f0fe;
  letter-spacing: 1px;
  padding: 0.5rem 1.75rem;
  margin: 1.25rem -0.75rem 0.5rem -0.75rem;
  display: flex;
  align-items: center;
`;

const Sidebar = () => {
  const { user, logout } = useAuth();
  
  if (!user) return null;
  const userRoles = user.roles || [];
  const isAdmin = userRoles.includes('Administrador');
  const isRH = userRoles.includes('RH') || isAdmin;

  return (
    <Container>
      <LogoContainer>
        <LogoText>RH Automático</LogoText>
      </LogoContainer>
      
      <NavList>
        <SectionLabel>Navegação</SectionLabel>
        
        {isRH && (
          <NavItem to="/alimentacao">
            <Utensils size={18} />
            Controle de Alimentação
          </NavItem>
        )}

        {isRH && (
          <NavItem to="/colaboradores">
            <HardHat size={18} />
            Colaboradores
          </NavItem>
        )}

        <NavItem to="/controle-vt">
          <Bus size={18} />
          Controle VT
        </NavItem>

        <NavItem to="/perfil">
          <User size={18} />
          Meu Perfil
        </NavItem>

        {isAdmin && (
          <>
            <SectionLabel>Segurança</SectionLabel>
            
            <NavItem to="/dashboard">
              <LayoutDashboard size={18} />
              Dashboard
            </NavItem>

            <NavItem to="/obras">
              <Building size={18} />
              Obras
            </NavItem>
            
            <NavItem to="/usuarios">
              <Users size={18} />
              Usuários
            </NavItem>

            <NavItem to="/auditoria">
              <ClipboardList size={18} />
              Auditoria
            </NavItem>

            <NavItem to="/configuracoes">
              <Settings size={18} />
              Configurações
            </NavItem>
          </>
        )}
      </NavList>

      <Footer>
        <LogoutButton onClick={logout}>
          <LogOut size={18} />
          Sair da Conta
        </LogoutButton>
      </Footer>
    </Container>
  );
};

export default Sidebar;
