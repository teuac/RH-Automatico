import React from 'react';
import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  ${({ $fullPage }) => $fullPage && `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #f8f9fa;
    z-index: 9999;
  `}
`;

const Spinner = styled.div`
  width: 50px;
  height: 50px;
  border: 4px solid #dadce0;
  border-top: 4px solid #1a73e8;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
  margin-bottom: 1rem;
`;

const Message = styled.span`
  font-size: 0.95rem;
  color: #5f6368;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
`;

const Loader = ({ message = 'Carregando...', fullPage = false }) => {
  return (
    <Container $fullPage={fullPage}>
      <Spinner />
      <Message>{message}</Message>
    </Container>
  );
};

export default Loader;
