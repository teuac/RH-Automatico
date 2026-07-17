import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const Title = styled.h1`
  font-family: 'Outfit', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: #202124;
`;

const Subtitle = styled.p`
  font-size: 0.875rem;
  color: #5f6368;
  font-weight: 400;
`;

const PageTitle = ({ title, subtitle }) => {
  return (
    <Container>
      <Title>{title}</Title>
      {subtitle && <Subtitle>{subtitle}</Subtitle>}
    </Container>
  );
};

export default PageTitle;
