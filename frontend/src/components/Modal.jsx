import React, { useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { X } from 'lucide-react';

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const slideUp = keyframes`
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`;

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(32, 33, 36, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: ${fadeIn} 0.2s ease-out;
  padding: 1rem;
`;

const Container = styled.div`
  background-color: white;
  border-radius: 8px;
  width: 100%;
  max-width: ${({ $size }) => ($size === 'large' ? '800px' : $size === 'small' ? '400px' : '600px')};
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  animation: ${slideUp} 0.2s cubic-bezier(0.1, 0.9, 0.2, 1);
  overflow: hidden;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #dadce0;
`;

const Title = styled.h2`
  font-family: 'Outfit', sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: #202124;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  color: #5f6368;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem;
  border-radius: 50%;
  transition: background-color 0.15s;

  &:hover {
    background-color: #f1f3f4;
    color: #202124;
  }
`;

const Body = styled.div`
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
`;

const Footer = styled.div`
  padding: 1rem 1.5rem;
  border-top: 1px solid #dadce0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  background-color: #f8f9fa;
`;

const Modal = ({ isOpen, onClose, title, children, footer, size = 'medium' }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <Overlay onClick={onClose}>
      <Container $size={size} onClick={(e) => e.stopPropagation()}>
        <Header>
          <Title>{title}</Title>
          <CloseButton onClick={onClose}>
            <X size={18} />
          </CloseButton>
        </Header>
        <Body>{children}</Body>
        {footer && <Footer>{footer}</Footer>}
      </Container>
    </Overlay>
  );
};

export default Modal;
export { Body as ModalBody, Footer as ModalFooter };
