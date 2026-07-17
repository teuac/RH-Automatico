import React from 'react';
import styled from 'styled-components';
import { Search } from 'lucide-react';

const Wrapper = styled.div`
  position: relative;
  width: 100%;
  max-width: 400px;
`;

const IconWrapper = styled.div`
  position: absolute;
  top: 50%;
  left: 0.75rem;
  transform: translateY(-50%);
  color: #5f6368;
  display: flex;
  align-items: center;
  pointer-events: none;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
  transition: border-color 0.15s ease-in-out;

  &:focus {
    border-color: #1a73e8;
    box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.15);
  }
`;

const SearchBar = ({ placeholder = "Pesquisar...", value, onChange, ...props }) => {
  return (
    <Wrapper>
      <IconWrapper>
        <Search size={16} />
      </IconWrapper>
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        {...props}
      />
    </Wrapper>
  );
};

export default SearchBar;
