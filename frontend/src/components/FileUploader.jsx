import React, { useRef, useState } from 'react';
import styled from 'styled-components';
import { Upload, File, AlertCircle } from 'lucide-react';
import Button from './Button';

const Dropzone = styled.div`
  border: 2px dashed ${({ $isDragActive, $hasFile }) => ($isDragActive ? '#1a73e8' : $hasFile ? '#0f9d58' : '#dadce0')};
  background-color: ${({ $isDragActive, $hasFile }) => ($isDragActive ? '#f8f9fa' : $hasFile ? '#e6f4ea' : 'white')};
  border-radius: 8px;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s ease-in-out, background-color 0.15s ease-in-out;
  &:hover {
    border-color: #1a73e8;
    background-color: #f8f9fa;
  }
`;

const Title = styled.h4`
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: #202124;
`;

const Subtitle = styled.p`
  font-size: 0.8125rem;
  color: #5f6368;
`;

const FileDetails = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: white;
  border: 1px solid #dadce0;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  max-width: 100%;
`;

const FileName = styled.span`
  font-size: 0.875rem;
  color: #202124;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
`;

const HiddenInput = styled.input`
  display: none;
`;

const FileUploader = ({ onFileSelected, selectedFile, error }) => {
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelected(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelected(e.dataTransfer.files[0]);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      <Dropzone
        $isDragActive={isDragActive}
        $hasFile={!!selectedFile}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <HiddenInput
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".txt,.csv,.xlsx,.xls"
        />
        
        {selectedFile ? (
          <>
            <File size={40} color="#0f9d58" />
            <Title>Arquivo selecionado com sucesso!</Title>
            <FileDetails onClick={(e) => e.stopPropagation()}>
              <File size={16} color="#5f6368" />
              <FileName>{selectedFile.name}</FileName>
              <span style={{ fontSize: '0.75rem', color: '#5f6368' }}>
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </FileDetails>
            <Subtitle>Clique ou arraste outro arquivo para substituir</Subtitle>
          </>
        ) : (
          <>
            <Upload size={40} color="#1a73e8" />
            <Title>Selecione o arquivo de ponto</Title>
            <Subtitle>
              Arraste e solte o arquivo aqui ou clique para navegar.<br />
              Formatos aceitos: <strong>TXT, CSV, XLSX</strong>
            </Subtitle>
          </>
        )}
      </Dropzone>
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem', color: '#d93025' }}>
          <AlertCircle size={14} />
          <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>{error}</span>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
