import React from 'react';
import styled from 'styled-components';
import { Menu } from 'lucide-react';

const Nav = styled.nav`
  display: none;
  background-color: white;
  border-bottom: 1px solid #dadce0;
  height: 56px;
  align-items: center;
  padding: 0 1rem;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 101;

  @media (max-width: 768px) {
    display: flex;
  }
`;

const NavTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  color: #1a73e8;
  margin-left: 1rem;
`;

const Navbar = ({ onToggleSidebar }) => {
  return (
    <Nav>
      <button 
        onClick={onToggleSidebar}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#5f6368' }}
      >
        <Menu size={24} />
      </button>
      <NavTitle>Automação RH</NavTitle>
    </Nav>
  );
};

export default Navbar;
