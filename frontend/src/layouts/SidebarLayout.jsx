import React from 'react';
import styled from 'styled-components';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';

const LayoutContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: #f8f9fa;
`;

const MainContent = styled.main`
  flex-grow: 1;
  padding: 88px 2rem 2rem 2rem; /* 64px header height + 24px padding */
  margin-left: 250px; /* Width of Sidebar */
  min-height: 100vh;
  box-sizing: border-box;

  @media (max-width: 768px) {
    margin-left: 0;
    padding-top: 76px;
  }
`;

const SidebarLayout = () => {
  return (
    <LayoutContainer>
      <Sidebar />
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
        <Header />
        <MainContent>
          <Outlet />
        </MainContent>
      </div>
    </LayoutContainer>
  );
};

export default SidebarLayout;
