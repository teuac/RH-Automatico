import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import FileUploader from '../components/FileUploader';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Toast, { ToastContainer } from '../components/Toast';
import { Table, Tr, Td } from '../components/Table';
import { Play, ArrowLeft, Check, AlertCircle, RefreshCw, Sparkles, Info, Edit, Stethoscope, FileText, CheckCircle2 } from 'lucide-react';

const ControlsRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
`;

const Label = styled.label`
  font-size: 0.8125rem;
  font-weight: 600;
  color: #3c4043;
`;

const Select = styled.select`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
  &:focus {
    border-color: #1a73e8;
  }
`;

const DateInput = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background-color: white;
  color: #202124;
  &:focus {
    border-color: #1a73e8;
  }
`;

const PreviewActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const StatusBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  
  ${({ $found }) => $found ? `
    background-color: #e6f4ea;
    color: #0f9d58;
  ` : `
    background-color: #fce8e6;
    color: #d93025;
  `}
`;

const PresencaBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  
  ${({ $presenca }) => $presenca === 'A' ? `
    background-color: #e2f0d9;
    color: #385723;
  ` : $presenca === 'J' ? `
    background-color: #e8f0fe;
    color: #1a73e8;
  ` : `
    background-color: #fce8e6;
    color: #c00000;
  `}
`;

const NewTabBadge = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  background: linear-gradient(135deg, #e8f0fe 0%, #e6f4ea 100%);
  border: 1px solid #1a73e8;
  color: #1a73e8;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  margin-top: 0.5rem;
`;

const WizardProgress = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background-color: #f8f9fa;
  padding: 1.25rem 1.5rem;
  border-radius: 12px;
  border: 1px solid #dadce0;
  gap: 1rem;
  flex-wrap: wrap;
`;

const WizardStep = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: ${({ $active }) => $active ? '700' : '500'};
  color: ${({ $active, $completed }) => $active ? '#1a73e8' : $completed ? '#0f9d58' : '#5f6368'};
`;

const StepCircle = styled.span`
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  background-color: ${({ $active, $completed }) => $active ? '#1a73e8' : $completed ? '#0f9d58' : '#dadce0'};
  color: white;
`;

const StepTitle = styled.h3`
  font-family: 'Outfit', sans-serif;
  font-size: 1.125rem;
  font-weight: 700;
  color: #202124;
  margin-bottom: 0.5rem;
  margin-top: 0.5rem;
`;

const StepDesc = styled.p`
  font-size: 0.875rem;
  color: #5f6368;
  margin-bottom: 1.5rem;
  line-height: 1.4;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  margin-top: 1.5rem;
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: #202124;
`;

const EditLink = styled.button`
  font-family: 'Inter', sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #1a73e8;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  &:hover {
    text-decoration: underline;
  }
`;

const Upload = () => {
  const [selectedObraId, setSelectedObraId] = useState('');
  const [selectedPlanilhaId, setSelectedPlanilhaId] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [file, setFile] = useState(null);
  
  const [previewData, setPreviewData] = useState(null);
  const [funcionariosList, setFuncionariosList] = useState([]);
  const [selectedForRegistration, setSelectedForRegistration] = useState([]);
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploaderError, setUploaderError] = useState(null);
  
  const [toastMessage, setToastMessage] = useState(null);
  const [toastVariant, setToastVariant] = useState('success');

  // Load Active Obras
  const { data: obras } = useQuery({
    queryKey: ['activeObras'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/obras/');
      return response.data.filter(o => o.status === 'ATIVO');
    }
  });

  // Load Active Planilhas
  const { data: planilhas } = useQuery({
    queryKey: ['activePlanilhas'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/planilhas/');
      return response.data;
    }
  });

  const handlePreview = async () => {
    if (!file || !selectedObraId || !selectedPlanilhaId) {
      setUploaderError('Preencha a obra, planilha e selecione o arquivo.');
      return;
    }

    setUploaderError(null);
    setIsProcessing(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('obra_id', selectedObraId);
    formData.append('planilha_id', selectedPlanilhaId);
    if (selectedDate) {
      formData.append('override_date', selectedDate);
    }

    try {
      const response = await axios.post('/api/v1/uploads/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPreviewData(response.data);
      const rows = response.data.linhas_preview || response.data.funcionarios || [];
      setFuncionariosList(rows);
      
      // Auto-select unregistered employees by default
      const unregistered = rows.filter(f => f.presenca === 'A' && !f.existe_na_base);
      setSelectedForRegistration(unregistered.map(f => f.matricula));
      
      setStep(1);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao processar prévia do arquivo.';
      setToastMessage(msg);
      setToastVariant('error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePresencaChange = (matricula, newPresenca) => {
    setFuncionariosList(prev => prev.map(f => 
      f.matricula === matricula ? { ...f, presenca: newPresenca } : f
    ));
  };

  const handleRegisterMissingAndNext = async () => {
    if (selectedForRegistration.length > 0) {
      setIsProcessing(true);
      try {
        const selectedEmps = funcionariosList.filter(f => selectedForRegistration.includes(f.matricula));
        for (const emp of selectedEmps) {
          await axios.post('/api/v1/colaboradores/', {
            matricula: emp.matricula,
            nome: emp.nome,
            obra_id: Number(selectedObraId),
            status: 'ATIVO'
          });
        }
        setFuncionariosList(prev => prev.map(f => 
          selectedForRegistration.includes(f.matricula) ? { ...f, existe_na_base: True } : f
        ));
        setToastMessage(`${selectedForRegistration.length} novo(s) colaborador(es) cadastrado(s) na base.`);
        setToastVariant('success');
      } catch (err) {
        setToastMessage('Erro ao cadastrar alguns colaboradores novos.');
        setToastVariant('error');
      } finally {
        setIsProcessing(false);
      }
    }
    setStep(3);
  };

  const handleCommit = async () => {
    setIsProcessing(true);
    try {
      const payload = {
        obra_id: Number(selectedObraId),
        planilha_id: Number(selectedPlanilhaId),
        filename: previewData.filename,
        date: previewData.data,
        funcionarios: funcionariosList.map(f => ({
          matricula: f.matricula,
          nome: f.nome,
          horarios: f.horarios,
          presenca: f.presenca
        }))
      };

      await axios.post('/api/v1/uploads/process', payload);
      setToastMessage('Presenças registradas com sucesso no Google Sheets!');
      setToastVariant('success');
      
      // Reset form
      setPreviewData(null);
      setFile(null);
      setFuncionariosList([]);
      setSelectedForRegistration([]);
      setStep(1);
    } catch (err) {
      setToastMessage(err.response?.data?.detail || 'Erro ao registrar presenças no Google Sheets.');
      setToastVariant('error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancel = () => {
    setPreviewData(null);
    setFile(null);
    setFuncionariosList([]);
    setSelectedForRegistration([]);
    setStep(1);
  };

  const filteredPlanilhas = planilhas?.filter(p => 
    p.obra_id === Number(selectedObraId) && 
    p.automacao === 'ALIMENTACAO' && 
    p.status === 'ATIVO'
  ) || [];

  const unregisteredEmployees = funcionariosList.filter(f => f.presenca === 'A' && !f.existe_na_base);
  const atestadoEmployees = funcionariosList.filter(f => f.presenca === 'J' && (f.situacao || '').includes('Atestado'));
  const faltasEmployees = funcionariosList.filter(f => f.presenca === 'F' || (f.presenca === 'J' && !(f.situacao || '').includes('Atestado')));

  const renderWizardBar = () => {
    return (
      <WizardProgress>
        <WizardStep $active={step === 1} $completed={step > 1}>
          <StepCircle $active={step === 1} $completed={step > 1}>
            {step > 1 ? <Check size={12} /> : "1"}
          </StepCircle>
          Presentes no Ponto
        </WizardStep>

        <WizardStep $active={step === 2} $completed={step > 2}>
          <StepCircle $active={step === 2} $completed={step > 2}>
            {step > 2 ? <Check size={12} /> : "2"}
          </StepCircle>
          Não Cadastrados
        </WizardStep>

        <WizardStep $active={step === 3} $completed={step > 3}>
          <StepCircle $active={step === 3} $completed={step > 3}>
            {step > 3 ? <Check size={12} /> : "3"}
          </StepCircle>
          Atestados Médicos
        </WizardStep>

        <WizardStep $active={step === 4} $completed={step > 4}>
          <StepCircle $active={step === 4} $completed={step > 4}>
            {step > 4 ? <Check size={12} /> : "4"}
          </StepCircle>
          Faltas e Justificativas
        </WizardStep>

        <WizardStep $active={step === 5}>
          <StepCircle $active={step === 5}>
            5
          </StepCircle>
          Revisão Geral
        </WizardStep>
      </WizardProgress>
    );
  };

  if (isProcessing) {
    return <Loader message={previewData ? "Gravando refeições no Google Sheets..." : "Analisando arquivo de refeições..."} />;
  }

  return (
    <div>
      {toastMessage && (
        <ToastContainer>
          <Toast message={toastMessage} variant={toastVariant} onClose={() => setToastMessage(null)} />
        </ToastContainer>
      )}

      <PageTitle 
        title="Controle de Alimentação" 
        subtitle={previewData ? "Confirme as refeições extraídas antes de registrar" : "Selecione o arquivo de refeições exportado pelo relógio de ponto"} 
      />

      {!previewData ? (
        <Card>
          <ControlsRow>
            <FormGroup>
              <Label>Selecione a Obra</Label>
              <Select 
                value={selectedObraId} 
                onChange={(e) => {
                  setSelectedObraId(e.target.value);
                  setSelectedPlanilhaId(''); // Reset selected spreadsheet when work changes
                }}
              >
                <option value="">Selecione...</option>
                {obras?.map(o => (
                  <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
                ))}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Selecione a Planilha Google</Label>
              <Select 
                value={selectedPlanilhaId} 
                onChange={(e) => setSelectedPlanilhaId(e.target.value)}
                disabled={!selectedObraId}
              >
                <option value="">
                  {!selectedObraId ? 'Selecione uma obra primeiro...' : 'Selecione...'}
                </option>
                {selectedObraId && filteredPlanilhas.length === 0 ? (
                  <option value="" disabled>Nenhuma planilha ativa para esta obra</option>
                ) : (
                  filteredPlanilhas.map(p => (
                    <option key={p.id} value={p.id}>{p.nome} ({p.nome_aba})</option>
                  ))
                )}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Data (Opcional - substitui a data detectada no arquivo)</Label>
              <DateInput 
                type="date" 
                value={selectedDate} 
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </FormGroup>
          </ControlsRow>

          <FileUploader 
            onFileSelected={setFile} 
            selectedFile={file} 
            error={uploaderError} 
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <Button onClick={handlePreview} disabled={!file || !selectedObraId || !selectedPlanilhaId}>
              <Play size={16} />
              Analisar Arquivo
            </Button>
          </div>
        </Card>
      ) : (
        <div>
          {renderWizardBar()}

          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid #dadce0', paddingBottom: '1rem' }}>
              <div>
                <strong>Obra:</strong> {previewData.obra_nome}<br />
                <strong>Data da Presença:</strong> {previewData.data}
              </div>
              <div>
                <strong>Planilha Google:</strong> {previewData.planilha_nome}<br />
                <strong>Aba:</strong> {previewData.nome_aba}
                {previewData.aba_criada && (
                  <NewTabBadge>
                    <Sparkles size={13} />
                    Nova aba criada automaticamente
                  </NewTabBadge>
                )}
              </div>
            </div>

            {/* STEP 1: Presentes no Arquivo */}
            {step === 1 && (
              <div>
                <StepTitle>Etapa 1: Colaboradores Presentes no Arquivo</StepTitle>
                <StepDesc>Abaixo estão os colaboradores identificados no arquivo de ponto que já constam cadastrados no banco de dados.</StepDesc>
                
                <Table headers={["Matrícula", "Funcionário", "Status no Arquivo", "Horários Detectados"]}>
                  {funcionariosList.filter(f => f.presenca === 'A' && f.existe_na_base).map((emp, idx) => (
                    <Tr key={idx}>
                      <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                      <Td><strong>{emp.nome}</strong></Td>
                      <Td>
                        <PresencaBadge $presenca={emp.presenca}>ALIMENTOU</PresencaBadge>
                      </Td>
                      <Td>
                        {emp.horarios.length === 0 ? (
                          <span style={{ color: '#9aa0a6', fontStyle: 'italic', fontSize: '0.8rem' }}>
                            Nenhum horário detectado
                          </span>
                        ) : (
                          emp.horarios.map((t, i) => (
                            <span key={i} style={{ backgroundColor: '#f1f3f4', padding: '0.2rem 0.4rem', borderRadius: '4px', marginRight: '0.25rem', fontSize: '0.8rem', fontWeight: 500 }}>
                              {t}
                            </span>
                          ))
                        )}
                      </Td>
                    </Tr>
                  ))}
                </Table>
                
                <PreviewActions>
                  <Button variant="secondary" onClick={handleCancel}>
                    Cancelar
                  </Button>
                  <Button onClick={() => setStep(2)}>
                    Avançar
                  </Button>
                </PreviewActions>
              </div>
            )}

            {/* STEP 2: Colaboradores não cadastrados na base */}
            {step === 2 && (
              <div>
                <StepTitle>Etapa 2: Colaboradores não Cadastrados na Base</StepTitle>
                
                {unregisteredEmployees.length === 0 ? (
                  <div style={{ backgroundColor: '#e8f0fe', border: '1px solid #1a73e8', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <Info size={32} color="#1a73e8" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#1a73e8', marginBottom: '0.25rem' }}>Excelente!</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>Todos os colaboradores presentes no arquivo já estão cadastrados na base do sistema.</p>
                  </div>
                ) : (
                  <div>
                    <StepDesc>Os seguintes funcionários foram encontrados no arquivo de ponto, mas não estão cadastrados na base de colaboradores do sistema. Selecione os que deseja cadastrar:</StepDesc>
                    
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
                      <button 
                        type="button"
                        style={{ border: 'none', background: 'none', color: '#1a73e8', cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => setSelectedForRegistration(unregisteredEmployees.map(f => f.matricula))}
                      >
                        Selecionar Todos
                      </button>
                      <span style={{ color: '#dadce0' }}>|</span>
                      <button 
                        type="button"
                        style={{ border: 'none', background: 'none', color: '#5f6368', cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => setSelectedForRegistration([])}
                      >
                        Limpar Seleção
                      </button>
                    </div>

                    <Table headers={["Selecionar", "Matrícula", "Funcionário", "Status no Arquivo"]}>
                      {unregisteredEmployees.map((emp, idx) => (
                        <Tr key={idx}>
                          <Td>
                            <input 
                              type="checkbox" 
                              checked={selectedForRegistration.includes(emp.matricula)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedForRegistration(prev => [...prev, emp.matricula]);
                                } else {
                                  setSelectedForRegistration(prev => prev.filter(m => m !== emp.matricula));
                                }
                              }}
                              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                            />
                          </Td>
                          <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                          <Td><strong>{emp.nome}</strong></Td>
                          <Td>
                            <PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge>
                          </Td>
                        </Tr>
                      ))}
                    </Table>
                  </div>
                )}
                
                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(1)}>
                    Voltar
                  </Button>
                  <Button onClick={handleRegisterMissingAndNext}>
                    {unregisteredEmployees.length > 0 ? 'Cadastrar Selecionados e Avançar' : 'Avançar'}
                  </Button>
                </PreviewActions>
              </div>
            )}

            {/* STEP 3: Colaboradores em Atestado Médico (NOVA ETAPA DO WORKFLOW) */}
            {step === 3 && (
              <div>
                <StepTitle>Etapa 3: Colaboradores com Atestado Médico Vigente</StepTitle>
                <StepDesc>
                  Consulta automática da base de atestados do sistema para a data <strong>{previewData.data}</strong>. 
                  Os colaboradores abaixo possuem atestado médico homologado vigente na data e foram justificados automaticamente.
                </StepDesc>

                {atestadoEmployees.length === 0 ? (
                  <div style={{ backgroundColor: '#e8f0fe', border: '1px solid #1a73e8', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <Stethoscope size={32} color="#1a73e8" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#1a73e8', marginBottom: '0.25rem' }}>Nenhum Atestado Médico Vigente</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>
                      Nenhum colaborador da obra possui atestado médico cadastrado na base do sistema para a data <strong>{previewData.data}</strong>.
                    </p>
                  </div>
                ) : (
                  <Table headers={["Matrícula", "Funcionário", "Situação no Sistema", "Registro na Planilha"]}>
                    {atestadoEmployees.map((emp, idx) => (
                      <Tr key={idx} style={{ backgroundColor: '#f4f8fd' }}>
                        <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                        <Td><strong>{emp.nome}</strong></Td>
                        <Td>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#1a73e8', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Stethoscope size={14} />
                            {emp.situacao || 'Atestado Médico Vigente (Justificado)'}
                          </span>
                        </Td>
                        <Td>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.6rem', borderRadius: '50px', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                            <CheckCircle2 size={13} />
                            JUSTIFICADA / ATESTADO (J)
                          </span>
                        </Td>
                      </Tr>
                    ))}
                  </Table>
                )}

                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(2)}>
                    Voltar
                  </Button>
                  <Button onClick={() => setStep(4)}>
                    Avançar
                  </Button>
                </PreviewActions>
              </div>
            )}

            {/* STEP 4: Faltas e Justificativas */}
            {step === 4 && (
              <div>
                <StepTitle>Etapa 4: Faltas e Justificativas Manuais</StepTitle>
                <StepDesc>Os colaboradores abaixo constam na base, mas não foram detectados no arquivo de ponto nem possuem atestado ativo (Falta). Você pode alterar manualmente para justificativa (J) se necessário.</StepDesc>
                
                {faltasEmployees.length === 0 ? (
                  <div style={{ backgroundColor: '#e6f4ea', border: '1px solid #0f9d58', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <CheckCircle2 size={32} color="#0f9d58" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#0f9d58', marginBottom: '0.25rem' }}>Nenhuma Falta a Tratar</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>Todos os colaboradores da obra estão presentes ou em atestado médico vigente nesta data.</p>
                  </div>
                ) : (
                  <Table headers={["Matrícula", "Funcionário", "Status da Presença", "Situação"]}>
                    {faltasEmployees.map((emp, idx) => (
                      <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                        <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                        <Td><strong>{emp.nome}</strong></Td>
                        <Td>
                          <Select 
                            value={emp.presenca} 
                            onChange={(e) => handlePresencaChange(emp.matricula, e.target.value)}
                            style={{ minHeight: '32px', padding: '0.25rem 0.5rem', width: '180px' }}
                          >
                            <option value="F">❌ FALTA NORMAL (F)</option>
                            <option value="J">📘 JUSTIFICADA (J)</option>
                          </Select>
                        </Td>
                        <Td>
                          <span style={{ fontSize: '0.8rem', fontWeight: 500, color: emp.presenca === 'J' ? '#1a73e8' : '#c00000' }}>
                            {emp.presenca === 'J' ? 'Falta Justificada Manual (Cor azul)' : 'Falta comum (Cor vermelha)'}
                          </span>
                        </Td>
                      </Tr>
                    ))}
                  </Table>
                )}
                
                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(3)}>
                    Voltar
                  </Button>
                  <Button onClick={() => setStep(5)}>
                    Avançar
                  </Button>
                </PreviewActions>
              </div>
            )}

            {/* STEP 5: Revisão Geral */}
            {step === 5 && (
              <div>
                <StepTitle>Etapa 5: Revisão Geral antes do Registro</StepTitle>
                <StepDesc>Revise o resumo completo antes de gravar na planilha Google Sheets.</StepDesc>
                
                {/* Presentes section */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <SectionHeader>
                    <span>👥 Presentes na Obra ({funcionariosList.filter(f => f.presenca === 'A').length})</span>
                    <EditLink onClick={() => setStep(1)}>
                      <Edit size={12} />
                      Editar Presentes
                    </EditLink>
                  </SectionHeader>
                  <Table headers={["Matrícula", "Funcionário", "Status", "Horários"]}>
                    {funcionariosList.filter(f => f.presenca === 'A').map((emp, idx) => (
                      <Tr key={idx}>
                        <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                        <Td>
                          <strong>{emp.nome}</strong>
                          {!emp.existe_na_base && (
                            <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', padding: '0.1rem 0.3rem', borderRadius: '4px', backgroundColor: '#fef7e0', color: '#b06000', border: '1px solid #ffe0b2' }}>
                              Não cadastrado no banco
                            </span>
                          )}
                        </Td>
                        <Td>
                          <PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge>
                        </Td>
                        <Td>
                          {emp.horarios.length === 0 ? '-' : emp.horarios.join(', ')}
                        </Td>
                      </Tr>
                    ))}
                  </Table>
                </div>

                {/* Atestados section */}
                {atestadoEmployees.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <SectionHeader>
                      <span>🏥 Colaboradores em Atestado Médico ({atestadoEmployees.length})</span>
                      <EditLink onClick={() => setStep(3)}>
                        <Edit size={12} />
                        Editar Atestados
                      </EditLink>
                    </SectionHeader>
                    <Table headers={["Matrícula", "Funcionário", "Situação", "Registro na Planilha"]}>
                      {atestadoEmployees.map((emp, idx) => (
                        <Tr key={idx} style={{ backgroundColor: '#f4f8fd' }}>
                          <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                          <Td><strong>{emp.nome}</strong></Td>
                          <Td>{emp.situacao || 'Atestado Médico Vigente'}</Td>
                          <Td>
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                              JUSTIFICADA (J)
                            </span>
                          </Td>
                        </Tr>
                      ))}
                    </Table>
                  </div>
                )}

                {/* Absent section */}
                <div>
                  <SectionHeader>
                    <span>❌ Faltas e Justificativas ({faltasEmployees.length})</span>
                    <EditLink onClick={() => setStep(4)}>
                      <Edit size={12} />
                      Editar Justificativas
                    </EditLink>
                  </SectionHeader>
                  <Table headers={["Matrícula", "Funcionário", "Status Final", "Registro na Planilha"]}>
                    {faltasEmployees.map((emp, idx) => (
                      <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                        <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                        <Td><strong>{emp.nome}</strong></Td>
                        <Td>
                          {emp.presenca === 'J' ? (
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                              JUSTIFICADA (J)
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#fce8e6', color: '#d93025', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                              FALTA COMUM (F)
                            </span>
                          )}
                        </Td>
                        <Td>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: emp.presenca === 'J' ? '#1a73e8' : '#5f6368' }}>
                            {emp.presenca === 'J' ? 'Gravar "J" (Azul)' : 'Gravar "F" (Vermelho)'}
                          </span>
                        </Td>
                      </Tr>
                    ))}
                  </Table>
                </div>

                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(4)}>
                    Voltar
                  </Button>
                  <Button variant="success" onClick={handleCommit}>
                    <Check size={16} />
                    Registrar no Google Sheets
                  </Button>
                </PreviewActions>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};

export default Upload;
