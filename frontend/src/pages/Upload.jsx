import React, { useState, useMemo } from 'react';
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
import {
  Play, ArrowLeft, Check, AlertCircle, RefreshCw, Sparkles,
  Info, Edit, Stethoscope, FileText, CheckCircle2, Calendar,
  CalendarDays, ChevronLeft, ChevronRight, Layers
} from 'lucide-react';

// ─── Styled Components ────────────────────────────────────────────────────────

const ControlsRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  @media (max-width: 768px) { grid-template-columns: 1fr; }
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
  &:focus { border-color: #1a73e8; }
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
  &:focus { border-color: #1a73e8; }
`;

const PreviewActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const PresencaBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  ${({ $presenca }) => $presenca === 'A' ? `
    background-color: #e2f0d9; color: #385723;
  ` : $presenca === 'J' ? `
    background-color: #e8f0fe; color: #1a73e8;
  ` : `
    background-color: #fce8e6; color: #c00000;
  `}
`;

const NewTabBadge = styled.div`
  display: inline-flex; align-items: center; gap: 0.375rem;
  background: linear-gradient(135deg, #e8f0fe 0%, #e6f4ea 100%);
  border: 1px solid #1a73e8; color: #1a73e8; font-size: 0.8rem;
  font-weight: 600; padding: 0.375rem 0.75rem; border-radius: 20px; margin-top: 0.5rem;
`;

// ── Auto-detected date banner ──────────────────────────────────────────────────
const DateDetectedBanner = styled.div`
  display: flex; align-items: flex-start; gap: 0.75rem;
  background: linear-gradient(135deg, #e8f0fe 0%, #e6f4ea 100%);
  border: 1px solid #1a73e8; border-radius: 10px; padding: 0.875rem 1.25rem;
  margin-bottom: 1.25rem;
`;

const DateDetectedTitle = styled.div`
  font-size: 0.8125rem; font-weight: 700; color: #1a73e8; margin-bottom: 0.25rem;
`;

const DateChipsRow = styled.div`
  display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.375rem;
`;

const DateChip = styled.button`
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem; font-weight: 600;
  padding: 0.2rem 0.65rem; border-radius: 20px; cursor: pointer;
  border: 2px solid ${({ $active }) => $active ? '#1a73e8' : '#dadce0'};
  background: ${({ $active }) => $active ? '#1a73e8' : 'white'};
  color: ${({ $active }) => $active ? 'white' : '#5f6368'};
  transition: all 0.15s ease;
  &:hover { border-color: #1a73e8; color: ${({ $active }) => $active ? 'white' : '#1a73e8'}; }
`;

const DateAllChip = styled(DateChip)`
  border: 2px dashed ${({ $active }) => $active ? '#1a73e8' : '#dadce0'};
  background: ${({ $active }) => $active ? '#e8f0fe' : 'white'};
  color: ${({ $active }) => $active ? '#1a73e8' : '#5f6368'};
`;

// ── Multi-day toggle ──────────────────────────────────────────────────────────
const MultiDayToggle = styled.label`
  display: inline-flex; align-items: center; gap: 0.5rem;
  cursor: pointer; font-size: 0.875rem; font-weight: 600; color: #3c4043;
  user-select: none;
`;

const ToggleSwitch = styled.div`
  width: 40px; height: 22px; border-radius: 11px; position: relative;
  background: ${({ $on }) => $on ? '#1a73e8' : '#dadce0'};
  transition: background 0.2s;
  &::after {
    content: ''; position: absolute; top: 3px; left: ${({ $on }) => $on ? '21px' : '3px'};
    width: 16px; height: 16px; border-radius: 50%; background: white;
    transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
`;

const MultiDaySection = styled.div`
  background: #f8f9fa; border: 1px solid #e8f0fe; border-radius: 8px;
  padding: 1rem 1.25rem; margin-bottom: 1.25rem;
`;

const MultiDayRow = styled.div`
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.75rem;
  @media (max-width: 640px) { grid-template-columns: 1fr; }
`;

const DateRangeHint = styled.p`
  font-size: 0.8125rem; color: #5f6368; margin-top: 0.5rem;
`;

// ── Wizard ────────────────────────────────────────────────────────────────────
const WizardProgress = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.5rem; background-color: #f8f9fa; padding: 1rem 1.5rem;
  border-radius: 12px; border: 1px solid #dadce0; gap: 1rem; flex-wrap: wrap;
`;

const WizardStep = styled.div`
  display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;
  font-weight: ${({ $active }) => $active ? '700' : '500'};
  color: ${({ $active, $completed }) => $active ? '#1a73e8' : $completed ? '#0f9d58' : '#5f6368'};
`;

const StepCircle = styled.span`
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700;
  background-color: ${({ $active, $completed }) => $active ? '#1a73e8' : $completed ? '#0f9d58' : '#dadce0'};
  color: white;
`;

// ── Wizard date selector (shown when multi-day) ───────────────────────────────
const WizardDateBar = styled.div`
  display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
  padding: 0.75rem 1rem; background: white; border: 1px solid #dadce0;
  border-radius: 8px; margin-bottom: 1.25rem;
`;

const WizardDateLabel = styled.span`
  font-size: 0.8125rem; font-weight: 700; color: #3c4043;
  display: flex; align-items: center; gap: 0.4rem;
`;

const WizardDatePill = styled.button`
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem; font-weight: 600; padding: 0.25rem 0.75rem;
  border-radius: 20px; cursor: pointer;
  border: 2px solid ${({ $active }) => $active ? '#1a73e8' : '#dadce0'};
  background: ${({ $active }) => $active ? '#1a73e8' : 'white'};
  color: ${({ $active }) => $active ? 'white' : '#5f6368'};
  transition: all 0.15s ease;
  &:hover { border-color: #1a73e8; }
`;

const StepTitle = styled.h3`
  font-family: 'Outfit', sans-serif; font-size: 1.125rem;
  font-weight: 700; color: #202124; margin-bottom: 0.5rem; margin-top: 0.5rem;
`;

const StepDesc = styled.p`
  font-size: 0.875rem; color: #5f6368; margin-bottom: 1.5rem; line-height: 1.4;
`;

const SectionHeader = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.75rem; margin-top: 1.5rem;
  font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 700; color: #202124;
`;

const EditLink = styled.button`
  font-family: 'Inter', sans-serif; font-size: 0.8125rem; font-weight: 600;
  color: #1a73e8; background: none; border: none; cursor: pointer;
  display: flex; align-items: center; gap: 0.25rem;
  &:hover { text-decoration: underline; }
`;

// ── Day group header in review ─────────────────────────────────────────────────
const DayGroupHeader = styled.div`
  display: flex; align-items: center; gap: 0.5rem;
  background: #f1f3f4; border-radius: 6px; padding: 0.5rem 0.75rem;
  margin-top: 1.25rem; margin-bottom: 0.5rem;
  font-size: 0.8125rem; font-weight: 700; color: #3c4043;
`;

// ── Helpers ──────────────────────────────────────────────────────────────────
const formatDateBR = (iso) => {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
};

const buildDateRange = (start, end) => {
  if (!start || !end) return [];
  const dates = [];
  const cur = new Date(start + 'T00:00:00');
  const fin = new Date(end + 'T00:00:00');
  while (cur <= fin) {
    dates.push(cur.toISOString().slice(0, 10));
    cur.setDate(cur.getDate() + 1);
  }
  return dates;
};

// ─── Main Component ───────────────────────────────────────────────────────────
const Upload = () => {
  const [selectedObraId, setSelectedObraId] = useState('');
  const [selectedPlanilhaId, setSelectedPlanilhaId] = useState('');
  const [selectedDate, setSelectedDate] = useState('');

  // Multi-day mode
  const [multiDayMode, setMultiDayMode] = useState(false);
  const [rangeStart, setRangeStart] = useState('');
  const [rangeEnd, setRangeEnd] = useState('');

  const [file, setFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [funcionariosList, setFuncionariosList] = useState([]);
  const [selectedForRegistration, setSelectedForRegistration] = useState([]);
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploaderError, setUploaderError] = useState(null);

  // Active day filter inside wizard (null = all days)
  const [wizardDay, setWizardDay] = useState(null);

  const [toastMessage, setToastMessage] = useState(null);
  const [toastVariant, setToastVariant] = useState('success');

  // ── Queries ────────────────────────────────────────────────────────────────
  const { data: obras } = useQuery({
    queryKey: ['activeObras'],
    queryFn: async () => (await axios.get('/api/v1/obras/')).data.filter(o => o.status === 'ATIVO')
  });

  const { data: planilhas } = useQuery({
    queryKey: ['activePlanilhas'],
    queryFn: async () => (await axios.get('/api/v1/planilhas/')).data
  });

  // ── Derived data ───────────────────────────────────────────────────────────
  const filteredPlanilhas = planilhas?.filter(p =>
    p.obra_id === Number(selectedObraId) &&
    p.automacao === 'ALIMENTACAO' &&
    p.status === 'ATIVO'
  ) || [];

  // All unique dates available in the current preview
  const availableDates = useMemo(() => {
    if (!previewData) return [];
    const fromData = previewData.datas_detectadas || [];
    // Also collect from funcionariosList
    const fromList = [...new Set(funcionariosList.map(f => f.date).filter(Boolean))];
    const merged = [...new Set([...fromData, ...fromList])].sort();
    return merged.length > 0 ? merged : (previewData.data ? [previewData.data] : []);
  }, [previewData, funcionariosList]);

  const isMultiDate = availableDates.length > 1;

  // Employees visible in current wizard day filter
  const visibleEmployees = useMemo(() => {
    if (!wizardDay) return funcionariosList;
    return funcionariosList.filter(f => !f.date || f.date === wizardDay);
  }, [funcionariosList, wizardDay]);

  const unregisteredEmployees = visibleEmployees.filter(f => f.presenca === 'A' && !f.existe_na_base);
  const unregisteredVisible = unregisteredEmployees; // alias used in step 2 JSX
  const atestadoEmployees = visibleEmployees.filter(f => f.presenca === 'J' && (f.situacao || '').includes('Atestado'));
  const faltasEmployees = visibleEmployees.filter(f => f.presenca === 'F' || (f.presenca === 'J' && !(f.situacao || '').includes('Atestado')));

  // ── Handlers ────────────────────────────────────────────────────────────────
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
    // Override date: use single-day date or range start
    const overrideDate = multiDayMode ? rangeStart : selectedDate;
    if (overrideDate) formData.append('override_date', overrideDate);

    try {
      const response = await axios.post('/api/v1/uploads/preview', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const data = response.data;
      setPreviewData(data);

      // Build rows — inject date field per employee if multi-day
      let rows = data.linhas_preview || data.funcionarios || [];

      // If multi-day mode with range, expand employees to cover each requested date
      if (multiDayMode && rangeStart && rangeEnd) {
        const requestedDates = buildDateRange(rangeStart, rangeEnd);
        // Only expand if file has a single detected date (typical single-day export)
        const fileDates = data.datas_detectadas || [];
        if (fileDates.length <= 1) {
          const baseDate = fileDates[0] || data.data;
          const expanded = [];
          for (const d of requestedDates) {
            expanded.push(...rows.map(r => ({ ...r, date: d, _originalDate: baseDate })));
          }
          rows = expanded;
        }
      }

      setFuncionariosList(rows);
      const unregistered = rows.filter(f => f.presenca === 'A' && !f.existe_na_base);
      setSelectedForRegistration(unregistered.map(f => f.matricula));

      // Set first detected date as default filter
      const detectedDates = data.datas_detectadas || [];
      setWizardDay(detectedDates.length > 1 ? detectedDates[0] : null);

      setStep(1);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao processar prévia do arquivo.';
      setToastMessage(msg);
      setToastVariant('error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePresencaChange = (matricula, date, newPresenca) => {
    setFuncionariosList(prev => prev.map(f =>
      f.matricula === matricula && (!date || f.date === date) ? { ...f, presenca: newPresenca } : f
    ));
  };

  const handleRegisterMissingAndNext = async () => {
    if (selectedForRegistration.length > 0) {
      setIsProcessing(true);
      try {
        const selectedEmps = funcionariosList.filter(f =>
          selectedForRegistration.includes(f.matricula) && f.presenca === 'A' && !f.existe_na_base
        );
        // Deduplicate by matricula for registration
        const unique = [...new Map(selectedEmps.map(e => [e.matricula, e])).values()];
        for (const emp of unique) {
          await axios.post('/api/v1/colaboradores/', {
            matricula: emp.matricula,
            nome: emp.nome,
            obra_id: Number(selectedObraId),
            status: 'ATIVO'
          });
        }
        setFuncionariosList(prev => prev.map(f =>
          selectedForRegistration.includes(f.matricula) ? { ...f, existe_na_base: true } : f
        ));
        setToastMessage(`${unique.length} novo(s) colaborador(es) cadastrado(s) na base.`);
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
          presenca: f.presenca,
          // Pass individual date so backend groups correctly
          date: f.date || previewData.data,
          data: f.date || previewData.data,
        }))
      };

      await axios.post('/api/v1/uploads/process', payload);
      setToastMessage('Presenças registradas com sucesso no Google Sheets!');
      setToastVariant('success');
      setPreviewData(null);
      setFile(null);
      setFuncionariosList([]);
      setSelectedForRegistration([]);
      setWizardDay(null);
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
    setWizardDay(null);
    setStep(1);
  };


  // ── Wizard bar ─────────────────────────────────────────────────────────────
  const renderWizardBar = () => (
    <WizardProgress>
      {[
        { n: 1, label: 'Presentes no Ponto' },
        { n: 2, label: 'Não Cadastrados' },
        { n: 3, label: 'Atestados Médicos' },
        { n: 4, label: 'Faltas e Justificativas' },
        { n: 5, label: 'Revisão Geral' },
      ].map(({ n, label }) => (
        <WizardStep key={n} $active={step === n} $completed={step > n}>
          <StepCircle $active={step === n} $completed={step > n}>
            {step > n ? <Check size={12} /> : n}
          </StepCircle>
          {label}
        </WizardStep>
      ))}
    </WizardProgress>
  );

  // ── Wizard day filter bar ──────────────────────────────────────────────────
  const renderDayBar = () => {
    if (!isMultiDate) return null;
    return (
      <WizardDateBar>
        <WizardDateLabel><CalendarDays size={15} />Filtrar por dia:</WizardDateLabel>
        <WizardDatePill $active={!wizardDay} onClick={() => setWizardDay(null)}>
          Todos os dias ({availableDates.length})
        </WizardDatePill>
        {availableDates.map(d => (
          <WizardDatePill key={d} $active={wizardDay === d} onClick={() => setWizardDay(d)}>
            {formatDateBR(d)}
          </WizardDatePill>
        ))}
      </WizardDateBar>
    );
  };

  // ── Grouping employees by date for review step ─────────────────────────────
  const groupByDate = (emps) => {
    const map = {};
    for (const e of emps) {
      const d = e.date || previewData?.data || '';
      if (!map[d]) map[d] = [];
      map[d].push(e);
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b));
  };

  if (isProcessing) {
    return <Loader message={previewData ? 'Gravando refeições no Google Sheets...' : 'Analisando arquivo de refeições...'} />;
  }

  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div>
      {toastMessage && (
        <ToastContainer>
          <Toast message={toastMessage} variant={toastVariant} onClose={() => setToastMessage(null)} />
        </ToastContainer>
      )}

      <PageTitle
        title="Controle de Alimentação"
        subtitle={previewData
          ? 'Confirme as refeições extraídas antes de registrar'
          : 'Selecione o arquivo de refeições exportado pelo relógio de ponto'}
      />

      {!previewData ? (
        // ══════════════════ UPLOAD FORM ══════════════════
        <Card>
          <ControlsRow>
            <FormGroup>
              <Label>Selecione a Obra</Label>
              <Select
                value={selectedObraId}
                onChange={(e) => { setSelectedObraId(e.target.value); setSelectedPlanilhaId(''); }}
              >
                <option value="">Selecione...</option>
                {obras?.map(o => <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>)}
              </Select>
            </FormGroup>

            <FormGroup>
              <Label>Selecione a Planilha Google</Label>
              <Select
                value={selectedPlanilhaId}
                onChange={(e) => setSelectedPlanilhaId(e.target.value)}
                disabled={!selectedObraId}
              >
                <option value="">{!selectedObraId ? 'Selecione uma obra primeiro...' : 'Selecione...'}</option>
                {selectedObraId && filteredPlanilhas.length === 0
                  ? <option value="" disabled>Nenhuma planilha ativa para esta obra</option>
                  : filteredPlanilhas.map(p => <option key={p.id} value={p.id}>{p.nome} ({p.nome_aba})</option>)
                }
              </Select>
            </FormGroup>
          </ControlsRow>

          {/* ── Multi-day toggle ─────────────────────────────────────────── */}
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Layers size={16} color="#5f6368" />
            <MultiDayToggle>
              <ToggleSwitch $on={multiDayMode} onClick={() => setMultiDayMode(v => !v)} />
              Processar múltiplos dias de uma vez
            </MultiDayToggle>
          </div>

          {multiDayMode ? (
            // ── Multi-day range inputs ──────────────────────────────────────
            <MultiDaySection>
              <Label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#1a73e8' }}>
                <CalendarDays size={15} /> Intervalo de datas a processar
              </Label>
              <MultiDayRow>
                <FormGroup>
                  <Label>Data de início</Label>
                  <DateInput type="date" value={rangeStart} onChange={e => setRangeStart(e.target.value)} />
                </FormGroup>
                <FormGroup>
                  <Label>Data de fim</Label>
                  <DateInput
                    type="date"
                    value={rangeEnd}
                    min={rangeStart}
                    onChange={e => setRangeEnd(e.target.value)}
                  />
                </FormGroup>
              </MultiDayRow>
              {rangeStart && rangeEnd && (
                <DateRangeHint>
                  📅 Serão processados <strong>{buildDateRange(rangeStart, rangeEnd).length}</strong> dia(s):&nbsp;
                  {buildDateRange(rangeStart, rangeEnd).map(formatDateBR).join(', ')}
                </DateRangeHint>
              )}
            </MultiDaySection>
          ) : (
            // ── Single-day date override ────────────────────────────────────
            <FormGroup style={{ marginBottom: '1.25rem', maxWidth: '320px' }}>
              <Label>Data manual (opcional — substitui a data detectada no arquivo)</Label>
              <DateInput type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
            </FormGroup>
          )}

          <FileUploader onFileSelected={setFile} selectedFile={file} error={uploaderError} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <Button onClick={handlePreview} disabled={!file || !selectedObraId || !selectedPlanilhaId}>
              <Play size={16} />
              Analisar Arquivo
            </Button>
          </div>
        </Card>
      ) : (
        // ══════════════════ WIZARD ══════════════════
        <div>
          {renderWizardBar()}

          {/* ── Auto-detected dates banner ─────────────────────────────── */}
          {availableDates.length > 0 && (
            <DateDetectedBanner>
              <Calendar size={20} color="#1a73e8" style={{ flexShrink: 0, marginTop: '0.1rem' }} />
              <div style={{ flex: 1 }}>
                <DateDetectedTitle>
                  {availableDates.length === 1
                    ? `📅 Data detectada automaticamente: ${formatDateBR(availableDates[0])}`
                    : `📅 ${availableDates.length} datas detectadas no arquivo`}
                </DateDetectedTitle>
                {availableDates.length > 1 && (
                  <DateChipsRow>
                    <DateAllChip $active={!wizardDay} onClick={() => setWizardDay(null)}>
                      Todos os dias
                    </DateAllChip>
                    {availableDates.map(d => (
                      <DateChip key={d} $active={wizardDay === d} onClick={() => setWizardDay(d)}>
                        {formatDateBR(d)}
                      </DateChip>
                    ))}
                  </DateChipsRow>
                )}
              </div>
            </DateDetectedBanner>
          )}

          <Card>
            {/* Summary header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid #dadce0', paddingBottom: '1rem' }}>
              <div>
                <strong>Obra:</strong> {previewData.obra_nome}<br />
                <strong>Data da Presença:</strong>{' '}
                {wizardDay ? formatDateBR(wizardDay) : (availableDates.length > 1 ? `${availableDates.length} dias` : formatDateBR(previewData.data))}
              </div>
              <div>
                <strong>Planilha Google:</strong> {previewData.planilha_nome}<br />
                <strong>Aba:</strong> {previewData.nome_aba}
                {previewData.aba_criada && (
                  <NewTabBadge><Sparkles size={13} />Nova aba criada automaticamente</NewTabBadge>
                )}
              </div>
            </div>

            {/* Day filter bar */}
            {renderDayBar()}

            {/* ── STEP 1: Presentes ─────────────────────────────────────── */}
            {step === 1 && (
              <div>
                <StepTitle>Etapa 1: Colaboradores Presentes no Arquivo</StepTitle>
                <StepDesc>
                  Colaboradores identificados no arquivo de ponto que já constam cadastrados no banco de dados.
                  {wizardDay && <> — <strong>Dia: {formatDateBR(wizardDay)}</strong></>}
                </StepDesc>

                {isMultiDate && !wizardDay
                  ? groupByDate(visibleEmployees.filter(f => f.presenca === 'A' && f.existe_na_base)).map(([d, emps]) => (
                    <div key={d}>
                      <DayGroupHeader><Calendar size={14} />{formatDateBR(d)} — {emps.length} presente(s)</DayGroupHeader>
                      <Table headers={['Matrícula', 'Funcionário', 'Status', 'Horários']}>
                        {emps.map((emp, idx) => (
                          <Tr key={idx}>
                            <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                            <Td><strong>{emp.nome}</strong></Td>
                            <Td><PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge></Td>
                            <Td>
                              {emp.horarios.length === 0
                                ? <span style={{ color: '#9aa0a6', fontStyle: 'italic', fontSize: '0.8rem' }}>Nenhum horário detectado</span>
                                : emp.horarios.map((t, i) => (
                                  <span key={i} style={{ backgroundColor: '#f1f3f4', padding: '0.2rem 0.4rem', borderRadius: '4px', marginRight: '0.25rem', fontSize: '0.8rem', fontWeight: 500 }}>{t}</span>
                                ))}
                            </Td>
                          </Tr>
                        ))}
                      </Table>
                    </div>
                  ))
                  : (
                    <Table headers={['Matrícula', 'Funcionário', 'Status no Arquivo', 'Horários Detectados']}>
                      {visibleEmployees.filter(f => f.presenca === 'A' && f.existe_na_base).map((emp, idx) => (
                        <Tr key={idx}>
                          <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                          <Td><strong>{emp.nome}</strong></Td>
                          <Td><PresencaBadge $presenca={emp.presenca}>ALIMENTOU</PresencaBadge></Td>
                          <Td>
                            {emp.horarios.length === 0
                              ? <span style={{ color: '#9aa0a6', fontStyle: 'italic', fontSize: '0.8rem' }}>Nenhum horário detectado</span>
                              : emp.horarios.map((t, i) => (
                                <span key={i} style={{ backgroundColor: '#f1f3f4', padding: '0.2rem 0.4rem', borderRadius: '4px', marginRight: '0.25rem', fontSize: '0.8rem', fontWeight: 500 }}>{t}</span>
                              ))}
                          </Td>
                        </Tr>
                      ))}
                    </Table>
                  )}

                <PreviewActions>
                  <Button variant="secondary" onClick={handleCancel}>Cancelar</Button>
                  <Button onClick={() => setStep(2)}>Avançar</Button>
                </PreviewActions>
              </div>
            )}

            {/* ── STEP 2: Não Cadastrados ───────────────────────────────── */}
            {step === 2 && (
              <div>
                <StepTitle>Etapa 2: Colaboradores não Cadastrados na Base</StepTitle>

                {unregisteredVisible.length === 0 ? (
                  <div style={{ backgroundColor: '#e8f0fe', border: '1px solid #1a73e8', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <Info size={32} color="#1a73e8" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#1a73e8', marginBottom: '0.25rem' }}>Excelente!</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>Todos os colaboradores presentes no arquivo já estão cadastrados na base do sistema.</p>
                  </div>
                ) : (
                  <div>
                    <StepDesc>Os seguintes funcionários foram encontrados no arquivo de ponto, mas não estão cadastrados na base. Selecione os que deseja cadastrar:</StepDesc>
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', fontSize: '0.875rem' }}>
                      <button type="button" style={{ border: 'none', background: 'none', color: '#1a73e8', cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => setSelectedForRegistration(unregisteredVisible.map(f => f.matricula))}>
                        Selecionar Todos
                      </button>
                      <span style={{ color: '#dadce0' }}>|</span>
                      <button type="button" style={{ border: 'none', background: 'none', color: '#5f6368', cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => setSelectedForRegistration([])}>
                        Limpar Seleção
                      </button>
                    </div>
                    <Table headers={['Selecionar', 'Matrícula', 'Funcionário', 'Status no Arquivo']}>
                      {unregisteredVisible.map((emp, idx) => (
                        <Tr key={idx}>
                          <Td>
                            <input
                              type="checkbox"
                              checked={selectedForRegistration.includes(emp.matricula)}
                              onChange={(e) => {
                                if (e.target.checked) setSelectedForRegistration(prev => [...prev, emp.matricula]);
                                else setSelectedForRegistration(prev => prev.filter(m => m !== emp.matricula));
                              }}
                              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                            />
                          </Td>
                          <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                          <Td><strong>{emp.nome}</strong></Td>
                          <Td><PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge></Td>
                        </Tr>
                      ))}
                    </Table>
                  </div>
                )}

                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(1)} disabled={isProcessing}>Voltar</Button>
                  <Button onClick={handleRegisterMissingAndNext} disabled={isProcessing}>
                    {isProcessing ? 'Processando...' : (unregisteredVisible.length > 0 ? 'Cadastrar Selecionados e Avançar' : 'Avançar')}
                  </Button>
                </PreviewActions>
              </div>
            )}

            {/* ── STEP 3: Atestados ─────────────────────────────────────── */}
            {step === 3 && (
              <div>
                <StepTitle>Etapa 3: Colaboradores com Atestado Médico Vigente</StepTitle>
                <StepDesc>
                  Consulta automática da base de atestados para a data <strong>{wizardDay ? formatDateBR(wizardDay) : formatDateBR(previewData.data)}</strong>.
                  Os colaboradores abaixo possuem atestado homologado vigente e foram justificados automaticamente.
                </StepDesc>

                {atestadoEmployees.length === 0 ? (
                  <div style={{ backgroundColor: '#e8f0fe', border: '1px solid #1a73e8', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <Stethoscope size={32} color="#1a73e8" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#1a73e8', marginBottom: '0.25rem' }}>Nenhum Atestado Médico Vigente</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>
                      Nenhum colaborador possui atestado médico cadastrado para a data <strong>{wizardDay ? formatDateBR(wizardDay) : formatDateBR(previewData.data)}</strong>.
                    </p>
                  </div>
                ) : (
                  <Table headers={['Matrícula', 'Funcionário', 'Situação no Sistema', 'Registro na Planilha']}>
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
                  <Button variant="secondary" onClick={() => setStep(2)}>Voltar</Button>
                  <Button onClick={() => setStep(4)}>Avançar</Button>
                </PreviewActions>
              </div>
            )}

            {/* ── STEP 4: Faltas ────────────────────────────────────────── */}
            {step === 4 && (
              <div>
                <StepTitle>Etapa 4: Faltas e Justificativas Manuais</StepTitle>
                <StepDesc>
                  Colaboradores que constam na base, mas não foram detectados no arquivo de ponto nem possuem atestado ativo.
                  Você pode alterar manualmente para justificativa (J) se necessário.
                </StepDesc>

                {faltasEmployees.length === 0 ? (
                  <div style={{ backgroundColor: '#e6f4ea', border: '1px solid #0f9d58', borderRadius: '8px', padding: '1.5rem', textAlign: 'center', margin: '1rem 0' }}>
                    <CheckCircle2 size={32} color="#0f9d58" style={{ marginBottom: '0.5rem' }} />
                    <p style={{ fontWeight: 600, color: '#0f9d58', marginBottom: '0.25rem' }}>Nenhuma Falta a Tratar</p>
                    <p style={{ fontSize: '0.875rem', color: '#3c4043' }}>Todos os colaboradores estão presentes ou em atestado médico vigente.</p>
                  </div>
                ) : (
                  isMultiDate && !wizardDay
                    ? groupByDate(faltasEmployees).map(([d, emps]) => (
                      <div key={d}>
                        <DayGroupHeader><Calendar size={14} />{formatDateBR(d)} — {emps.length} falta(s)</DayGroupHeader>
                        <Table headers={['Matrícula', 'Funcionário', 'Status da Presença', 'Situação']}>
                          {emps.map((emp, idx) => (
                            <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                              <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                              <Td><strong>{emp.nome}</strong></Td>
                              <Td>
                                <Select value={emp.presenca} onChange={(e) => handlePresencaChange(emp.matricula, emp.date, e.target.value)}
                                  style={{ minHeight: '32px', padding: '0.25rem 0.5rem', width: '180px' }}>
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
                      </div>
                    ))
                    : (
                      <Table headers={['Matrícula', 'Funcionário', 'Status da Presença', 'Situação']}>
                        {faltasEmployees.map((emp, idx) => (
                          <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                            <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                            <Td><strong>{emp.nome}</strong></Td>
                            <Td>
                              <Select value={emp.presenca} onChange={(e) => handlePresencaChange(emp.matricula, emp.date, e.target.value)}
                                style={{ minHeight: '32px', padding: '0.25rem 0.5rem', width: '180px' }}>
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
                    )
                )}

                <PreviewActions>
                  <Button variant="secondary" onClick={() => setStep(3)}>Voltar</Button>
                  <Button onClick={() => setStep(5)}>Avançar</Button>
                </PreviewActions>
              </div>
            )}

            {/* ── STEP 5: Revisão Geral ─────────────────────────────────── */}
            {step === 5 && (() => {
              const allPresentes = funcionariosList.filter(f => f.presenca === 'A');
              const allAtestados = funcionariosList.filter(f => f.presenca === 'J' && (f.situacao || '').includes('Atestado'));
              const allFaltas = funcionariosList.filter(f => f.presenca === 'F' || (f.presenca === 'J' && !(f.situacao || '').includes('Atestado')));

              return (
                <div>
                  <StepTitle>Etapa 5: Revisão Geral antes do Registro</StepTitle>
                  <StepDesc>
                    Revise o resumo completo antes de gravar na planilha Google Sheets.
                    {isMultiDate && <> <strong>{availableDates.length} dias</strong> serão processados.</>}
                  </StepDesc>

                  {/* Presentes */}
                  <div style={{ marginBottom: '1.5rem' }}>
                    <SectionHeader>
                      <span>👥 Presentes na Obra ({allPresentes.length})</span>
                      <EditLink onClick={() => setStep(1)}><Edit size={12} />Editar Presentes</EditLink>
                    </SectionHeader>
                    {isMultiDate
                      ? groupByDate(allPresentes).map(([d, emps]) => (
                        <div key={d}>
                          <DayGroupHeader><Calendar size={14} />{formatDateBR(d)} — {emps.length} presente(s)</DayGroupHeader>
                          <Table headers={['Matrícula', 'Funcionário', 'Status', 'Horários']}>
                            {emps.map((emp, idx) => (
                              <Tr key={idx}>
                                <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                                <Td>
                                  <strong>{emp.nome}</strong>
                                  {!emp.existe_na_base && <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', padding: '0.1rem 0.3rem', borderRadius: '4px', backgroundColor: '#fef7e0', color: '#b06000', border: '1px solid #ffe0b2' }}>Não cadastrado</span>}
                                </Td>
                                <Td><PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge></Td>
                                <Td>{emp.horarios.length === 0 ? '-' : emp.horarios.join(', ')}</Td>
                              </Tr>
                            ))}
                          </Table>
                        </div>
                      ))
                      : (
                        <Table headers={['Matrícula', 'Funcionário', 'Status', 'Horários']}>
                          {allPresentes.map((emp, idx) => (
                            <Tr key={idx}>
                              <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                              <Td>
                                <strong>{emp.nome}</strong>
                                {!emp.existe_na_base && <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', padding: '0.1rem 0.3rem', borderRadius: '4px', backgroundColor: '#fef7e0', color: '#b06000', border: '1px solid #ffe0b2' }}>Não cadastrado</span>}
                              </Td>
                              <Td><PresencaBadge $presenca="A">ALIMENTOU</PresencaBadge></Td>
                              <Td>{emp.horarios.length === 0 ? '-' : emp.horarios.join(', ')}</Td>
                            </Tr>
                          ))}
                        </Table>
                      )}
                  </div>

                  {/* Atestados */}
                  {allAtestados.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <SectionHeader>
                        <span>🏥 Colaboradores em Atestado Médico ({allAtestados.length})</span>
                        <EditLink onClick={() => setStep(3)}><Edit size={12} />Editar Atestados</EditLink>
                      </SectionHeader>
                      {isMultiDate
                        ? groupByDate(allAtestados).map(([d, emps]) => (
                          <div key={d}>
                            <DayGroupHeader><Calendar size={14} />{formatDateBR(d)}</DayGroupHeader>
                            <Table headers={['Matrícula', 'Funcionário', 'Situação', 'Registro']}>
                              {emps.map((emp, idx) => (
                                <Tr key={idx} style={{ backgroundColor: '#f4f8fd' }}>
                                  <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                                  <Td><strong>{emp.nome}</strong></Td>
                                  <Td>{emp.situacao || 'Atestado Médico Vigente'}</Td>
                                  <Td><span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>JUSTIFICADA (J)</span></Td>
                                </Tr>
                              ))}
                            </Table>
                          </div>
                        ))
                        : (
                          <Table headers={['Matrícula', 'Funcionário', 'Situação', 'Registro na Planilha']}>
                            {allAtestados.map((emp, idx) => (
                              <Tr key={idx} style={{ backgroundColor: '#f4f8fd' }}>
                                <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                                <Td><strong>{emp.nome}</strong></Td>
                                <Td>{emp.situacao || 'Atestado Médico Vigente'}</Td>
                                <Td><span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>JUSTIFICADA (J)</span></Td>
                              </Tr>
                            ))}
                          </Table>
                        )}
                    </div>
                  )}

                  {/* Faltas */}
                  <div>
                    <SectionHeader>
                      <span>❌ Faltas e Justificativas ({allFaltas.length})</span>
                      <EditLink onClick={() => setStep(4)}><Edit size={12} />Editar Justificativas</EditLink>
                    </SectionHeader>
                    {isMultiDate
                      ? groupByDate(allFaltas).map(([d, emps]) => (
                        <div key={d}>
                          <DayGroupHeader><Calendar size={14} />{formatDateBR(d)} — {emps.length} falta(s)</DayGroupHeader>
                          <Table headers={['Matrícula', 'Funcionário', 'Status Final', 'Registro']}>
                            {emps.map((emp, idx) => (
                              <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                                <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                                <Td><strong>{emp.nome}</strong></Td>
                                <Td>
                                  {emp.presenca === 'J'
                                    ? <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>JUSTIFICADA (J)</span>
                                    : <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#fce8e6', color: '#d93025', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>FALTA COMUM (F)</span>}
                                </Td>
                                <Td><span style={{ fontSize: '0.8rem', fontWeight: 600, color: emp.presenca === 'J' ? '#1a73e8' : '#5f6368' }}>{emp.presenca === 'J' ? 'Gravar "J" (Azul)' : 'Gravar "F" (Vermelho)'}</span></Td>
                              </Tr>
                            ))}
                          </Table>
                        </div>
                      ))
                      : (
                        <Table headers={['Matrícula', 'Funcionário', 'Status Final', 'Registro na Planilha']}>
                          {allFaltas.map((emp, idx) => (
                            <Tr key={idx} style={emp.presenca === 'J' ? { backgroundColor: '#f4f8fd' } : {}}>
                              <Td style={{ fontFamily: 'monospace' }}>{emp.matricula}</Td>
                              <Td><strong>{emp.nome}</strong></Td>
                              <Td>
                                {emp.presenca === 'J'
                                  ? <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#e8f0fe', color: '#1a73e8', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>JUSTIFICADA (J)</span>
                                  : <span style={{ fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#fce8e6', color: '#d93025', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>FALTA COMUM (F)</span>}
                              </Td>
                              <Td><span style={{ fontSize: '0.8rem', fontWeight: 600, color: emp.presenca === 'J' ? '#1a73e8' : '#5f6368' }}>{emp.presenca === 'J' ? 'Gravar "J" (Azul)' : 'Gravar "F" (Vermelho)'}</span></Td>
                            </Tr>
                          ))}
                        </Table>
                      )}
                  </div>

                  <PreviewActions>
                    <Button variant="secondary" onClick={() => setStep(4)} disabled={isProcessing}>Voltar</Button>
                    <Button variant="success" onClick={handleCommit} disabled={isProcessing}>
                      <Check size={16} />
                      {isProcessing ? 'Registrando...' : (isMultiDate ? `Registrar ${availableDates.length} dias no Google Sheets` : 'Registrar no Google Sheets')}
                    </Button>
                  </PreviewActions>
                </div>
              );
            })()}
          </Card>
        </div>
      )}
    </div>
  );
};

export default Upload;
