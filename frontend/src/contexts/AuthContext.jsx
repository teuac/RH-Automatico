import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

// Configure axios base url to match our proxy/backend URL
axios.defaults.baseURL = import.meta.env.VITE_API_URL || '';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Set global authorization header
  const setAuthHeader = (token) => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const login = async (googleIdToken) => {
    try {
      setIsLoading(true);
      const response = await axios.post('/api/v1/auth/login', { token: googleIdToken });
      
      const { access_token, refresh_token, user: userData } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setAuthHeader(access_token);
      setUser(userData);
      setIsAuthenticated(true);
      
      return userData;
    } catch (error) {
      logout();
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setAuthHeader(null);
    setUser(null);
    setIsAuthenticated(false);
    setIsLoading(false);
  };

  const checkCurrentUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      logout();
      return;
    }
    
    try {
      setAuthHeader(token);
      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // If unauthorized, attempt refresh
      await attemptRefresh();
    } finally {
      setIsLoading(false);
    }
  };

  const attemptRefresh = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) {
      logout();
      return;
    }
    
    try {
      const response = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh });
      const { access_token, refresh_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setAuthHeader(access_token);
      
      // Fetch user detail again
      const userResponse = await axios.get('/api/v1/auth/me');
      setUser(userResponse.data);
      setIsAuthenticated(true);
    } catch (error) {
      logout();
    }
  };

  // Initial check
  useEffect(() => {
    checkCurrentUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout, checkCurrentUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider');
  }
  return context;
};
