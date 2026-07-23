import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { theme } from './theme';

import ProtectedRoute from './components/ProtectedRoute';
import SidebarLayout from './layouts/SidebarLayout';

// Import Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Auditoria from './pages/Auditoria';
import Usuarios from './pages/Usuarios';
import Obras from './pages/Obras';
import Configuracoes from './pages/Configuracoes';
import MeuPerfil from './pages/MeuPerfil';
import ControleVT from './pages/ControleVT';
import PrimeiroAcesso from './pages/PrimeiroAcesso';
import NaoAutorizado from './pages/NaoAutorizado';
import NotFound from './pages/404';
import Colaboradores from './pages/Colaboradores';
import Contratacoes from './pages/Contratacoes';
import Atestados from './pages/Atestados';

// Initialize React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

// Helper for root path redirection based on roles
const HomeRedirect = () => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  const roles = user.roles || [];
  if (roles.includes('Administrador')) {
    return <Navigate to="/dashboard" replace />;
  }
  if (roles.includes('RH')) {
    return <Navigate to="/alimentacao" replace />;
  }
  return <Navigate to="/perfil" replace />;
};

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/primeiro-acesso" element={<PrimeiroAcesso />} />

              {/* Protected Workspace Layout Routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<SidebarLayout />}>
                  <Route path="/" element={<HomeRedirect />} />
                  <Route path="/perfil" element={<MeuPerfil />} />
                  <Route path="/controle-vt" element={<ControleVT />} />
                  <Route path="/nao-autorizado" element={<NaoAutorizado />} />
                </Route>
              </Route>

              {/* RH & Admin Synchronizer Routes */}
              <Route element={<ProtectedRoute allowedRoles={['Administrador', 'RH']} />}>
                <Route element={<SidebarLayout />}>
                  <Route path="/alimentacao" element={<Upload />} />
                  <Route path="/colaboradores" element={<Colaboradores />} />
                  <Route path="/contratacoes" element={<Contratacoes />} />
                  <Route path="/atestados" element={<Atestados />} />
                </Route>
              </Route>

              {/* Admin Exclusives Settings Routes */}
              <Route element={<ProtectedRoute allowedRoles={['Administrador']} />}>
                <Route element={<SidebarLayout />}>
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/obras" element={<Obras />} />
                  <Route path="/usuarios" element={<Usuarios />} />
                  <Route path="/auditoria" element={<Auditoria />} />
                  <Route path="/configuracoes" element={<Configuracoes />} />
                </Route>
              </Route>

              {/* Fallback 404 Page */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
