import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Loader from './Loader';

const ProtectedRoute = ({ allowedRoles = [] }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <Loader fullPage />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Handle auto-registered users waiting for approval
  const userRoles = user?.roles || [];
  const isAdmin = userRoles.includes('Administrador');

  if (user && user.status === 'PENDENTE' && !isAdmin) {
    return <Navigate to="/primeiro-acesso" replace />;
  }

  // Handle deactivated users
  if (user && !user.is_active) {
    return <Navigate to="/login" replace />;
  }

  // RBAC validation: Admins bypass all limits
  if (allowedRoles.length > 0 && user) {
    const userRoles = user.roles || [];
    const hasRole = userRoles.includes('Administrador') || allowedRoles.some((role) => userRoles.includes(role));
    if (!hasRole) {
      return <Navigate to="/nao-autorizado" replace />;
    }
  }

  return <Outlet />;
};

export default ProtectedRoute;
