import React, { useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';

const slideIn = keyframes`
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`;

const Wrapper = styled.div`
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 350px;
  width: 100%;
  pointer-events: none;
`;

const Container = styled.div`
  pointer-events: auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(60, 64, 67, 0.15);
  border: 1px solid #dadce0;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  animation: ${slideIn} 0.25s cubic-bezier(0, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  /* Indicator strip */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 4px;
    background-color: ${({ $variant }) => {
      if ($variant === 'success') return '#0f9d58';
      if ($variant === 'error') return '#d93025';
      if ($variant === 'warning') return '#f4b400';
      return '#1a73e8';
    }};
  }
`;

const IconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 0.125rem;
  color: ${({ $variant }) => {
    if ($variant === 'success') return '#0f9d58';
    if ($variant === 'error') return '#d93025';
    if ($variant === 'warning') return '#f4b400';
    return '#1a73e8';
  }};
`;

const Content = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const Message = styled.p`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: #202124;
  line-height: 1.4;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  color: #5f6368;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.125rem;
  border-radius: 50%;
  margin-top: 0.125rem;
  &:hover {
    background-color: #f1f3f4;
  }
`;

const Toast = ({ message, variant = 'success', onClose, duration = 4000 }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const getIcon = () => {
    if (variant === 'success') return <CheckCircle size={18} />;
    if (variant === 'error') return <AlertCircle size={18} />;
    if (variant === 'warning') return <AlertTriangle size={18} />;
    return <Info size={18} />;
  };

  return (
    <Container $variant={variant}>
      <IconWrapper $variant={variant}>{getIcon()}</IconWrapper>
      <Content>
        <Message>{message}</Message>
      </Content>
      <CloseButton onClick={onClose}>
        <X size={14} />
      </CloseButton>
    </Container>
  );
};

export { Wrapper as ToastContainer };
export default Toast;
