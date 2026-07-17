import React, { useState, useCallback } from 'react';
import styled from 'styled-components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import axios from 'axios';
import PageTitle from '../components/PageTitle';
import Card from '../components/Card';
import Input from '../components/Input';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import Toast, { ToastContainer } from '../components/Toast';
import { Table, Tr, Td } from '../components/Table';
import {
  Plus, Edit2, Trash2, Check, Upload, Download,
  ArrowRightLeft, Search, X, AlertCircle, CheckSquare
} from 'lucide-react';

// ─── Styled Components ──────────────────────────────────────────────────────

const ToolbarRow = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
`;

const SearchWrapper = styled.div`
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 340px;
`;

const SearchIcon = styled.span`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9aa0a6;
  display: flex;
  align-items: center;
`;

const SearchInput = styled.input`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  border-radius: 8px;
  border: 1px solid #dadce0;
  outline: none;
  width: 100%;
  background: white;
  color: #202124;
  &:focus { border-color: #1a73e8; }
`;

const FilterSelect = styled.select`
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: 1px solid #dadce0;
  outline: none;
  min-height: 38px;
  background: white;
  color: #202124;
  &:focus { border-color: #1a73e8; }
`;

const SelectionBar = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, #e8f0fe, #f1f8e9);
  border: 1px solid #1a73e8;
  border-radius: 10px;
  padding: 0.625rem 1rem;
  margin-bottom: 1rem;
  animation: slideIn 0.2s ease;
  @keyframes slideIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
`;

const SelectionCount = styled.span`
  font-weight: 700;
  color: #1a73e8;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
`;

const StatusBadge = styled.span`
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  ${({ $status }) => $status === 'ATIVO'
    ? 'background:#e6f4ea; color:#0f9d58;'
    : 'background:#f1f3f4; color:#5f6368;'
  }
`;

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  @media (max-width: 576px) { grid-template-columns: 1fr; }
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
  background: white;
  color: #202124;
  &:focus { border-color: #1a73e8; }
`;

const Checkbox = styled.input.attrs({ type: 'checkbox' })`
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #1a73e8;
`;

const UploadZone = styled.label`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  border: 2px dashed #dadce0;
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  background: #fafafa;
  &:hover { border-color: #1a73e8; background: #f0f5ff; }
`;

const ImportResultBox = styled.div`
  background: ${({ $ok }) => $ok ? '#e6f4ea' : '#fce8e6'};
  border: 1px solid ${({ $ok }) => $ok ? '#34a853' : '#ea4335'};
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  font-size: 0.85rem;
`;

const ErrorList = styled.ul`
  margin-top: 0.5rem;
  padding-left: 1.25rem;
  color: #c5221f;
  font-size: 0.8rem;
  line-height: 1.6;
`;

// ─── Component ──────────────────────────────────────────────────────────────

const Colaboradores = () => {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState(null);
  const [search, setSearch] = useState('');
  const [filterObra, setFilterObra] = useState('');
  const [filterStatus, setFilterStatus] = useState('ATIVO');

  // Seleção de checkboxes
  const [selectedIds, setSelectedIds] = useState([]);

  // Modais
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [isMigrarOpen, setIsMigrarOpen] = useState(false);
  const [selectedColab, setSelectedColab] = useState(null);

  // Import state
  const [importFile, setImportFile] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [isImporting, setIsImporting] = useState(false);

  // Migração state
  const [migrarObraDestino, setMigrarObraDestino] = useState('');

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  const showToast = (message, variant = 'success') => setToast({ message, variant });

  // ─── Queries ───────────────────────────────────────────────────────────

  const { data: colaboradores = [], isLoading } = useQuery({
    queryKey: ['colaboradores', search, filterObra, filterStatus],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: 500 });
      if (search) params.set('search', search);
      if (filterObra) params.set('obra_id', filterObra);
      if (filterStatus) params.set('status', filterStatus);
      const res = await axios.get(`/api/v1/colaboradores/?${params}`);
      return res.data;
    }
  });

  const { data: obras = [] } = useQuery({
    queryKey: ['activeObras'],
    queryFn: async () => (await axios.get('/api/v1/obras/')).data
  });

  // ─── Mutations ─────────────────────────────────────────────────────────

  const createMutation = useMutation({
    mutationFn: (data) => axios.post('/api/v1/colaboradores/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['colaboradores'] });
      setIsFormOpen(false); reset();
      showToast('Colaborador cadastrado com sucesso.');
    },
    onError: (e) => showToast(e.response?.data?.detail || 'Erro ao cadastrar.', 'error')
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => axios.put(`/api/v1/colaboradores/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['colaboradores'] });
      setIsFormOpen(false); reset();
      showToast('Colaborador atualizado com sucesso.');
    },
    onError: (e) => showToast(e.response?.data?.detail || 'Erro ao atualizar.', 'error')
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => axios.delete(`/api/v1/colaboradores/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['colaboradores'] });
      setIsDeleteOpen(false);
      showToast('Colaborador removido.');
    },
    onError: (e) => showToast(e.response?.data?.detail || 'Erro ao remover.', 'error')
  });

  const migrarMutation = useMutation({
    mutationFn: ({ ids, nova_obra_id }) =>
      axios.post('/api/v1/colaboradores/migrar-obra', { ids, nova_obra_id }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['colaboradores'] });
      setIsMigrarOpen(false);
      setSelectedIds([]);
      setMigrarObraDestino('');
      showToast(res.data.detail);
    },
    onError: (e) => showToast(e.response?.data?.detail || 'Erro na migração.', 'error')
  });

  // ─── Handlers ──────────────────────────────────────────────────────────

  const handleOpenCreate = () => {
    setSelectedColab(null);
    reset({ matricula: '', nome: '', funcao: '', obra_id: '', status: 'ATIVO' });
    setIsFormOpen(true);
  };

  const handleOpenEdit = (c) => {
    setSelectedColab(c);
    reset({ matricula: c.matricula, nome: c.nome, funcao: c.funcao || '', obra_id: c.obra_id || '', status: c.status });
    setIsFormOpen(true);
  };

  const onFormSubmit = (data) => {
    const payload = { ...data, obra_id: data.obra_id ? Number(data.obra_id) : null };
    if (selectedColab) {
      updateMutation.mutate({ id: selectedColab.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Checkboxes
  const toggleSelect = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === colaboradores.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(colaboradores.map(c => c.id));
    }
  };

  // Import
  const handleImport = async () => {
    if (!importFile) return;
    setIsImporting(true);
    setImportResult(null);
    const fd = new FormData();
    fd.append('file', importFile);
    try {
      const res = await axios.post('/api/v1/colaboradores/import', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setImportResult(res.data);
      queryClient.invalidateQueries({ queryKey: ['colaboradores'] });
    } catch (e) {
      showToast(e.response?.data?.detail || 'Erro na importação.', 'error');
    } finally {
      setIsImporting(false);
    }
  };

  const handleDownloadTemplate = async () => {
    const res = await axios.get('/api/v1/colaboradores/template', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'modelo_importacao_colaboradores.xlsx';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleConfirmMigrar = () => {
    if (!migrarObraDestino) return;
    migrarMutation.mutate({ ids: selectedIds, nova_obra_id: Number(migrarObraDestino) });
  };

  if (isLoading) return <Loader message="Carregando colaboradores..." />;

  const allSelected = colaboradores.length > 0 && selectedIds.length === colaboradores.length;
  const someSelected = selectedIds.length > 0;

  return (
    <div>
      {toast && (
        <ToastContainer>
          <Toast message={toast.message} variant={toast.variant} onClose={() => setToast(null)} />
        </ToastContainer>
      )}

      <PageTitle
        title="Colaboradores"
        subtitle="Gerencie os colaboradores vinculados às obras, importe em lote e migre entre obras"
      />

      {/* Toolbar */}
      <ToolbarRow>
        <SearchWrapper>
          <SearchIcon><Search size={15} /></SearchIcon>
          <SearchInput
            placeholder="Buscar por nome ou matrícula..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </SearchWrapper>

        <FilterSelect value={filterObra} onChange={e => setFilterObra(e.target.value)}>
          <option value="">Todas as obras</option>
          {obras.map(o => <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>)}
        </FilterSelect>

        <FilterSelect value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">Todos os status</option>
          <option value="ATIVO">Ativo</option>
          <option value="INATIVO">Inativo</option>
        </FilterSelect>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <Button variant="outline" onClick={() => { setImportFile(null); setImportResult(null); setIsImportOpen(true); }}>
            <Upload size={15} />
            Importar Excel
          </Button>
          <Button onClick={handleOpenCreate}>
            <Plus size={15} />
            Novo Colaborador
          </Button>
        </div>
      </ToolbarRow>

      {/* Barra de seleção */}
      {someSelected && (
        <SelectionBar>
          <CheckSquare size={18} color="#1a73e8" />
          <SelectionCount>{selectedIds.length} selecionado(s)</SelectionCount>
          <Button
            onClick={() => { setMigrarObraDestino(''); setIsMigrarOpen(true); }}
            style={{ marginLeft: '0.5rem', padding: '0.375rem 0.875rem', fontSize: '0.8rem' }}
          >
            <ArrowRightLeft size={14} />
            Migrar Obra ({selectedIds.length})
          </Button>
          <Button
            variant="outline"
            onClick={() => setSelectedIds([])}
            style={{ padding: '0.375rem 0.75rem', fontSize: '0.8rem' }}
          >
            <X size={14} />
            Limpar
          </Button>
        </SelectionBar>
      )}

      {/* Tabela */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <Table headers={[
          <Checkbox
            checked={allSelected}
            onChange={toggleSelectAll}
            title="Selecionar todos"
          />,
          'Matrícula', 'Nome', 'Função', 'Obra Vinculada', 'Status', 'Ações'
        ]}>
          {colaboradores.length === 0 ? (
            <Tr>
              <Td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: '#9aa0a6' }}>
                Nenhum colaborador encontrado.
              </Td>
            </Tr>
          ) : colaboradores.map(c => (
            <Tr key={c.id} style={{ background: selectedIds.includes(c.id) ? '#f0f5ff' : undefined }}>
              <Td>
                <Checkbox
                  checked={selectedIds.includes(c.id)}
                  onChange={() => toggleSelect(c.id)}
                />
              </Td>
              <Td style={{ fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 600 }}>{c.matricula}</Td>
              <Td><strong style={{ color: '#202124' }}>{c.nome}</strong></Td>
              <Td style={{ color: '#5f6368' }}>{c.funcao || <em style={{ color: '#bbb' }}>—</em>}</Td>
              <Td>
                {c.obra ? (
                  <span style={{ fontWeight: 500 }}>{c.obra.nome} <span style={{ color: '#9aa0a6', fontWeight: 400 }}>({c.obra.codigo})</span></span>
                ) : (
                  <span style={{ color: '#bbb', fontStyle: 'italic' }}>Sem obra</span>
                )}
              </Td>
              <Td><StatusBadge $status={c.status}>{c.status}</StatusBadge></Td>
              <Td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button variant="outline" onClick={() => handleOpenEdit(c)} style={{ padding: '0.3rem 0.6rem' }}>
                    <Edit2 size={13} />
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => { setSelectedColab(c); setIsDeleteOpen(true); }}
                    style={{ padding: '0.3rem 0.6rem', borderColor: '#d93025', color: '#d93025' }}
                  >
                    <Trash2 size={13} />
                  </Button>
                </div>
              </Td>
            </Tr>
          ))}
        </Table>
      </Card>

      <p style={{ textAlign: 'right', marginTop: '0.5rem', fontSize: '0.8rem', color: '#9aa0a6' }}>
        {colaboradores.length} colaborador(es) exibido(s)
      </p>

      {/* ── Modal CRUD ──────────────────────────────────────────────────── */}
      <Modal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        title={selectedColab ? `Editar: ${selectedColab.nome}` : 'Novo Colaborador'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsFormOpen(false)}>Cancelar</Button>
            <Button onClick={handleSubmit(onFormSubmit)}>
              <Check size={15} />
              Confirmar
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <FormGrid>
            <Input
              label="Matrícula *"
              placeholder="Ex: 001234"
              error={errors.matricula?.message}
              {...register('matricula', { required: 'Matrícula é obrigatória.' })}
            />
            <Input
              label="Nome Completo *"
              placeholder="Ex: João da Silva"
              error={errors.nome?.message}
              {...register('nome', { required: 'Nome é obrigatório.' })}
            />
          </FormGrid>

          <FormGrid style={{ marginTop: '0.75rem' }}>
            <Input
              label="Função"
              placeholder="Ex: Pedreiro, Encarregado..."
              {...register('funcao')}
            />
            <FormGroup>
              <Label>Obra Vinculada</Label>
              <Select {...register('obra_id')}>
                <option value="">Sem obra vinculada</option>
                {obras.map(o => (
                  <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
                ))}
              </Select>
            </FormGroup>
          </FormGrid>

          <FormGroup style={{ marginTop: '0.75rem' }}>
            <Label>Status</Label>
            <Select {...register('status')}>
              <option value="ATIVO">ATIVO</option>
              <option value="INATIVO">INATIVO</option>
            </Select>
          </FormGroup>
        </form>
      </Modal>

      {/* ── Modal Confirmar Delete ──────────────────────────────────────── */}
      <ConfirmDialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={() => deleteMutation.mutate(selectedColab?.id)}
        title="Remover Colaborador"
        message={`Tem certeza que deseja remover '${selectedColab?.nome}' (${selectedColab?.matricula})?`}
        confirmText="Remover"
        isDanger
      />

      {/* ── Modal Importação Excel ──────────────────────────────────────── */}
      <Modal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        title="Importar Colaboradores via Excel"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsImportOpen(false)}>Fechar</Button>
            <Button onClick={handleImport} disabled={!importFile || isImporting}>
              <Upload size={15} />
              {isImporting ? 'Importando...' : 'Importar'}
            </Button>
          </>
        }
      >
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <p style={{ fontSize: '0.875rem', color: '#5f6368', margin: 0 }}>
              Baixe o modelo, preencha e faça o upload.
            </p>
            <Button variant="outline" onClick={handleDownloadTemplate}>
              <Download size={14} />
              Baixar Modelo
            </Button>
          </div>

          <UploadZone htmlFor="excel-upload">
            <Upload size={32} color="#1a73e8" />
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontWeight: 600, color: '#202124', margin: 0 }}>
                {importFile ? importFile.name : 'Clique ou arraste o arquivo .xlsx aqui'}
              </p>
              <p style={{ fontSize: '0.8rem', color: '#9aa0a6', marginTop: '0.25rem' }}>
                Formatos aceitos: .xlsx, .xls
              </p>
            </div>
            <input
              id="excel-upload"
              type="file"
              accept=".xlsx,.xls"
              style={{ display: 'none' }}
              onChange={e => { setImportFile(e.target.files[0]); setImportResult(null); }}
            />
          </UploadZone>

          {importResult && (
            <ImportResultBox $ok={importResult.importados > 0}>
              <strong>
                {importResult.importados > 0
                  ? `✅ ${importResult.importados} colaborador(es) importado(s) com sucesso!`
                  : '⚠️ Nenhum colaborador importado.'}
              </strong>
              <p style={{ margin: '0.25rem 0 0', color: '#5f6368', fontSize: '0.8rem' }}>
                Total no arquivo: {importResult.total} | Importados: {importResult.importados} | Ignorados: {importResult.ignorados}
              </p>
              {importResult.erros?.length > 0 && (
                <ErrorList>
                  {importResult.erros.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ErrorList>
              )}
            </ImportResultBox>
          )}
        </div>
      </Modal>

      {/* ── Modal Migrar Obra ───────────────────────────────────────────── */}
      <Modal
        isOpen={isMigrarOpen}
        onClose={() => setIsMigrarOpen(false)}
        title={`Migrar ${selectedIds.length} Colaborador(es) de Obra`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsMigrarOpen(false)}>Cancelar</Button>
            <Button onClick={handleConfirmMigrar} disabled={!migrarObraDestino || migrarMutation.isPending}>
              <ArrowRightLeft size={15} />
              Confirmar Migração
            </Button>
          </>
        }
      >
        <div>
          <div style={{
            background: '#fff8e1', border: '1px solid #f9ab00', borderRadius: '8px',
            padding: '0.75rem 1rem', marginBottom: '1rem', fontSize: '0.875rem', color: '#7b5800',
            display: 'flex', gap: '0.5rem', alignItems: 'flex-start'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
            <span>
              Os <strong>{selectedIds.length}</strong> colaborador(es) selecionado(s) serão transferidos para a obra escolhida.
              Esta ação afeta registros de todos os selecionados.
            </span>
          </div>

          <FormGroup>
            <Label>Obra de Destino *</Label>
            <Select value={migrarObraDestino} onChange={e => setMigrarObraDestino(e.target.value)}>
              <option value="">Selecione a obra destino...</option>
              {obras.map(o => (
                <option key={o.id} value={o.id}>{o.nome} ({o.codigo})</option>
              ))}
            </Select>
          </FormGroup>
        </div>
      </Modal>
    </div>
  );
};

export default Colaboradores;
