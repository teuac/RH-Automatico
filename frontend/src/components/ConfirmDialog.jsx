import React from 'react';
import Modal from './Modal';
import Button from './Button';
import styled from 'styled-components';

const Message = styled.p`
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: #3c4043;
  line-height: 1.5;
`;

const ConfirmDialog = ({ isOpen, onClose, onConfirm, title = "Confirmar Ação", message, confirmText = "Confirmar", cancelText = "Cancelar", isDanger = false }) => {
  const footer = (
    <>
      <Button variant="secondary" onClick={onClose}>
        {cancelText}
      </Button>
      <Button variant={isDanger ? "danger" : "primary"} onClick={onConfirm}>
        {confirmText}
      </Button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} footer={footer} size="small">
      <Message>{message}</Message>
    </Modal>
  );
};

export default ConfirmDialog;
