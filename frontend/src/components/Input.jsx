import React, { forwardRef } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 1rem;
  width: 100%;
`;

const Label = styled.label`
  font-size: 0.8125rem;
  font-weight: 600;
  color: #3c4043;
  font-family: 'Inter', sans-serif;
`;

const StyledInput = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid ${({ $hasError }) => ($hasError ? '#d93025' : '#dadce0')};
  background-color: white;
  color: #202124;
  outline: none;
  min-height: 38px;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;

  &:focus {
    border-color: ${({ $hasError }) => ($hasError ? '#d93025' : '#1a73e8')};
    box-shadow: 0 0 0 2px ${({ $hasError }) => ($hasError ? 'rgba(217, 48, 37, 0.15)' : 'rgba(26, 115, 232, 0.15)')};
  }

  &:disabled {
    background-color: #f1f3f4;
    color: #5f6368;
    cursor: not-allowed;
  }
`;

const ErrorText = styled.span`
  font-size: 0.75rem;
  color: #d93025;
  font-weight: 500;
`;

const Input = forwardRef(({ label, error, ...props }, ref) => {
  return (
    <Container>
      {label && <Label>{label}</Label>}
      <StyledInput ref={ref} $hasError={!!error} {...props} />
      {error && <ErrorText>{error}</ErrorText>}
    </Container>
  );
});

Input.displayName = 'Input';

export default Input;
