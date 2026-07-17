import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, AlertCircle } from 'lucide-react';
import Button from '../components/Button';

const Container = styled.div`
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 1rem;
`;

const CardWrapper = styled.div`
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  padding: 2.5rem;
  max-width: 400px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.8);
`;

const Brand = styled.div`
  margin-bottom: 2rem;
`;

const BrandTitle = styled.h1`
  font-family: 'Outfit', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a73e8;
  letter-spacing: -0.5px;
`;

const BrandSubtitle = styled.p`
  font-size: 0.875rem;
  color: #5f6368;
  margin-top: 0.25rem;
`;

const GoogleButtonContainer = styled.div`
  margin: 1.5rem 0;
  width: 100%;
  display: flex;
  justify-content: center;
  min-height: 40px;
`;

const ErrorBox = styled.div`
  background-color: #fce8e6;
  border: 1px solid #d93025;
  color: #d93025;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  width: 100%;
  text-align: left;
`;

const FooterText = styled.p`
  font-size: 0.75rem;
  color: #5f6368;
  line-height: 1.4;
  margin-top: 1.5rem;
`;

const Login = () => {
  const { login } = useAuth();
  const [error, setError] = useState(null);
  const [isGsiLoaded, setIsGsiLoaded] = useState(false);
  const [clientId, setClientId] = useState('');

  const handleCredentialResponse = async (response) => {
    try {
      setError(null);
      await login(response.credential);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao realizar login corporativo.');
    }
  };

  // Fetch client ID dynamically from backend to avoid frontend config files duplicate
  useEffect(() => {
    const fetchClientId = async () => {
      try {
        const response = await axios.get('/api/v1/auth/google-client-id');
        setClientId(response.data.client_id);
      } catch (err) {
        console.error("Failed to fetch Google Client ID from backend settings:", err);
      }
    };
    fetchClientId();
  }, []);

  useEffect(() => {
    // Dynamically load Google Identity Services library
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setIsGsiLoaded(true);
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  useEffect(() => {
    if (!isGsiLoaded || !clientId) return;

    try {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-btn'),
          { 
            theme: 'outline', 
            size: 'large', 
            text: 'signin_with', 
            shape: 'rectangular',
            width: 320
          }
        );
      }
    } catch (err) {
      console.error("Failed to render Google login button", err);
    }
  }, [isGsiLoaded, clientId]);

  // Developer Mock Login for local sandbox execution
  const handleMockLogin = async () => {
    try {
      // Send dummy token
      await login("mock-google-id-token");
      window.location.href = '/dashboard';
    } catch (err) {
      setError("Falha no login simulado.");
    }
  };

  return (
    <Container>
      <CardWrapper>
        <Brand>
          <BrandTitle>Acengenharia</BrandTitle>
          <BrandSubtitle>Automação e Controle de Ponto</BrandSubtitle>
        </Brand>

        {error && (
          <ErrorBox>
            <AlertCircle size={16} />
            <span>{error}</span>
          </ErrorBox>
        )}

        <p style={{ fontSize: '0.875rem', color: '#3c4043', marginBottom: '0.5rem' }}>
          Utilize sua conta institucional para entrar no sistema.
        </p>

        {/* Div where Google will render the button */}
        <GoogleButtonContainer id="google-signin-btn" />

        {/* Mock login button for easy environment testing/evaluations */}
        {(!import.meta.env.PROD || import.meta.env.VITE_DEV_MOCK_LOGIN === "true") && (
          <Button variant="outline" fullWidth onClick={handleMockLogin} style={{ marginTop: '0.5rem' }}>
            <LogIn size={16} />
            Entrar como Admin (Desenvolvimento)
          </Button>
        )}

        <FooterText>
          Este é um portal restrito da Acengenharia. Apenas contas registradas sob o domínio permitido podem acessar estas ferramentas.
        </FooterText>
      </CardWrapper>
    </Container>
  );
};

export default Login;
