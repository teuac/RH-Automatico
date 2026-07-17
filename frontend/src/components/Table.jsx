import React from 'react';
import styled from 'styled-components';

const ResponsiveWrapper = styled.div`
  width: 100%;
  overflow-x: auto;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #dadce0;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.1);
  margin-bottom: 1.5rem;
`;

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  color: #202124;
`;

const Th = styled.th`
  background-color: #f8f9fa;
  color: #5f6368;
  font-weight: 600;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #dadce0;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
`;

const Td = styled.td`
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f1f3f4;
  vertical-align: middle;
  color: #3c4043;
`;

const Tr = styled.tr`
  transition: background-color 0.15s ease-in-out;
  &:hover {
    background-color: #f8f9fa;
  }
  &:last-child ${Td} {
    border-bottom: none;
  }
`;

const Table = ({ headers, children }) => {
  return (
    <ResponsiveWrapper>
      <StyledTable>
        <thead>
          <tr>
            {headers.map((header, idx) => (
              <Th key={idx}>{header}</Th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </StyledTable>
    </ResponsiveWrapper>
  );
};

export { Table, Tr, Td };
