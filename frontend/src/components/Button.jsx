import React from 'react';
import styled, { css } from 'styled-components';

const StyledButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  min-height: 38px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
  transition: all 0.15s ease-in-out;
  width: ${({ $fullWidth }) => ($fullWidth ? '100%' : 'auto')};

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Variants */
  ${({ $variant, theme }) => {
    switch ($variant) {
      case 'secondary':
        return css`
          background-color: #f1f3f4;
          color: #3c4043;
          border-color: #dadce0;
          &:hover:not(:disabled) {
            background-color: #e8eaed;
          }
        `;
      case 'danger':
        return css`
          background-color: #d93025;
          color: white;
          &:hover:not(:disabled) {
            background-color: #c5221f;
          }
        `;
      case 'success':
        return css`
          background-color: #0f9d58;
          color: white;
          &:hover:not(:disabled) {
            background-color: #0b8043;
          }
        `;
      case 'outline':
        return css`
          background-color: transparent;
          color: #1a73e8;
          border-color: #dadce0;
          &:hover:not(:disabled) {
            background-color: #f4b40011;
            border-color: #1a73e8;
          }
        `;
      case 'primary':
      default:
        return css`
          background-color: #1a73e8;
          color: white;
          &:hover:not(:disabled) {
            background-color: #1557b0;
          }
        `;
    }
  }}
`;

const Button = ({ children, variant = 'primary', fullWidth = false, ...props }) => {
  return (
    <StyledButton $variant={variant} $fullWidth={fullWidth} {...props}>
      {children}
    </StyledButton>
  );
};

export default Button;
