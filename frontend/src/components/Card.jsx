import React from 'react';
import styled from 'styled-components';

const StyledCard = styled.div`
  background-color: white;
  border-radius: 8px;
  border: 1px solid #dadce0;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.1);
  padding: 1.5rem;
  margin-bottom: 1rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  
  ${({ $hoverable }) => $hoverable && `
    cursor: pointer;
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px 0 rgba(60, 64, 67, 0.15);
    }
  `}
`;

const CardTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: #5f6368;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const CardValue = styled.span`
  font-family: 'Outfit', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: #202124;
  line-height: 1.2;
`;

const CardDescription = styled.span`
  font-size: 0.75rem;
  color: #5f6368;
  margin-top: 0.5rem;
`;

const Card = ({ title, value, description, icon, hoverable = false, children, ...props }) => {
  return (
    <StyledCard $hoverable={hoverable} {...props}>
      {title && (
        <CardTitle>
          {icon}
          {title}
        </CardTitle>
      )}
      {value && <CardValue>{value}</CardValue>}
      {description && <CardDescription>{description}</CardDescription>}
      {children}
    </StyledCard>
  );
};

export default Card;
