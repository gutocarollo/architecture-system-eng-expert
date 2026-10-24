'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { useTheme } from '@/app/contexts/ThemeContext';
import { usePeriod, PeriodRange } from '@/app/contexts/InfoContext';
import { ProposalListItem, ProposalListStatus } from './_data/InsuranceDataManager';
import { useProposalsList, useApprovalStatus } from './_hooks/useInsurance';
import { ExternalLink } from 'lucide-react';
import { FiTrash2, FiSettings } from 'react-icons/fi';
import Card from '@/app/_components/Card';
import Table from '@/app/_components/Table';

const ALL_PROPOSAL_COLUMN_KEYS = [
  'name', 'team_name', 'advisor_name', 'specialist_name',
  'created_date', 'issue_date', 'days_in_stage', 'amount', 'id',
];
import { max } from 'd3';
import { useDetails } from '@/app/contexts/DetailsContext';
import InsuranceProposalDetails from '@/app/details/insurance-proposal/InsuranceProposalDetails';
import { sfPortalInsurancePolicyUrl, sfPortalOpportunityUrl } from '@/lib/salesforce-portal';
import { LoadingState, Skeleton } from '@/app/_components/loading';


interface StatusConfig {
  key: string;
  label: string;
  color: string;
  isHighlighted?: boolean;
}

interface InsuranceProposalsAnalysisCardProps {
  animationDelay?: number;
  /**
   * Período de criação das oportunidades. Afeta os 4 status não-emitidos do
   * grid (Assinatura/Em Análise/Carta/Pagamento) e as propostas não-emitidas
   * da tabela. Vazio/null = atemporal (mostra todas as propostas).
   */
  oppPeriod?: PeriodRange | null;
}

export default function InsuranceProposalsAnalysisCard({
  animationDelay = 0,
  oppPeriod = null,
}: InsuranceProposalsAnalysisCardProps) {
  const theme = useTheme();
  const { periodRange } = usePeriod();
  const { openDetails } = useDetails();
  const isDarkTheme = theme.theme !== 'light';
  const tableBackgroundColor = isDarkTheme ? theme.hover.medium : theme.background.layer4;
  // TESTE HEADER BG - descomentar a opção desejada:
  // const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer1; // #F1F1F1
  // const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer2; // #FFFFFF (original)
  // const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer3; // #F7F7F7
  // const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer4; // #FFFFFF
  // const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer5; // #F7F7F7
  const tableHeaderColor = isDarkTheme ? theme.hover.lighter : theme.background.layer3; // #E4E4E4
  const tableRowHoverColor = isDarkTheme ? theme.hover.darker : theme.background.layer3;

  // Status filter state (internal)
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);

  // Fixed tab - always show 'realized' (toggle removed)
  const activeTab: ProposalListStatus = 'realized';

  // Column filters state (controlled mode for Table)
  const [columnFilters, setColumnFilters] = useState<Record<string, string[]>>({});

  // Column visibility state (gear icon toggles panel)
  const [columnVisibilityOpen, setColumnVisibilityOpen] = useState(false);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(ALL_PROPOSAL_COLUMN_KEYS);

  // Checkbox selection state
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set());

  // Fetch approval status data
  const { data: approvalData, isLoading: isLoadingStatus } = useApprovalStatus(oppPeriod);

  // Use React Query hook - loads ALL data once, filtering is done locally
  const { data: response, isLoading } = useProposalsList(activeTab, oppPeriod);

  // Filter data LOCALLY based on selectedStatus for instant response
  const data = useMemo(() => {
    const items = response?.items || [];

    // Debug: log unique registration_status values
    if (items.length > 0) {
      const uniqueStatuses = [...new Set(items.map(i => i.registration_status))];
      console.log('[InsuranceProposals] Available registration_status values:', uniqueStatuses);
      console.log('[InsuranceProposals] Selected filter:', selectedStatus);
    }

    if (!selectedStatus) return items; // No filter = show all
    const filtered = items.filter(item => item.registration_status === selectedStatus);
    console.log('[InsuranceProposals] Filtered count:', filtered.length, 'from', items.length);
    return filtered;
  }, [response?.items, selectedStatus]);

  // Meta para Emitidos - R$ 833.333,33 por mês, agregada pelo período selecionado
  const META_MENSAL = 833333.33;
  const metaEmitido = useMemo(() => {
    if (!periodRange) {
      // Se não há período selecionado, usar meta anual (12 meses)
      return META_MENSAL * 12;
    }

    // Calcular número de meses no período selecionado
    const startMonth = periodRange.startMonth;
    const startYear = periodRange.startYear;
    const endMonth = periodRange.endMonth;
    const endYear = periodRange.endYear;

    // Diferença em meses = (anos * 12) + meses
    const monthsDiff = (endYear - startYear) * 12 + (endMonth - startMonth) + 1;

    return META_MENSAL * monthsDiff;
  }, [periodRange]);

  // Status configuration with colors (matching the design)
  const statusConfig: StatusConfig[] = useMemo(() => [
    { key: 'Aguardando assinatura', label: 'Assinatura', color: '#1f2937' }, // gray-900
    { key: 'Em analise', label: 'Em Análise', color: '#fb923c' }, // orange-400
    { key: 'Carta de ajuste', label: 'Carta de Ajuste', color: '#9ca3af' }, // gray-400
    { key: 'Pagamento pendente', label: 'Pagamento', color: '#eab308' }, // yellow-500
    { key: 'Emitido', label: 'Emitido', color: '#2E7AD1', isHighlighted: true },
  ], []);

  // Map API data to status config
  const statusData = useMemo(() => {
    const countMap = new Map(approvalData?.items?.map(item => [item.status, item.count]) || []);
    const amountMap = new Map(approvalData?.items?.map(item => [item.status, item.total_amount]) || []);
    return statusConfig.map(config => ({
      ...config,
      count: countMap.get(config.key) || 0,
      totalAmount: amountMap.get(config.key) || 0
    }));
  }, [approvalData, statusConfig]);

  // Calculate totals from raw API data (includes ALL statuses, not just configured ones)
  const totalVolume = useMemo(() => {
    return approvalData?.items?.reduce((sum, item) => sum + item.count, 0) || 0;
  }, [approvalData]);

  const totalAmount = useMemo(() => {
    return approvalData?.items?.reduce((sum, item) => sum + item.total_amount, 0) || 0;
  }, [approvalData]);

  const formatCurrencyCompact = useCallback((value: number) => {
    if (value >= 1000000) {
      return `R$${(value / 1000000).toFixed(3)}Mi`;
    } else if (value >= 1000) {
      return `R$${(value / 1000).toFixed(3)}K`;
    }
    return `R$${value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  }, []);

  const renderCurrencyCompact = useCallback((value: number) => {
    let num: string;
    if (value >= 1000000) {
      num = `${(value / 1000000).toFixed(3)}Mi`;
    } else if (value >= 1000) {
      num = `${(value / 1000).toFixed(3)}K`;
    } else {
      num = value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }
    return <><span style={{ fontSize: '0.7em' }}>R$</span> {num}</>;
  }, []);

  // Handle status click
  const handleStatusClick = (statusKey: string) => {
    if (selectedStatus === statusKey) {
      setSelectedStatus(null);
    } else {
      setSelectedStatus(statusKey);
    }
  };

  // Handler for selection changes
  const handleSelectionChange = useCallback((newSelectedRows: Set<string | number>) => {
    setSelectedRows(newSelectedRows);
  }, []);

  const handleRowClick = useCallback((item: Record<string, unknown>) => {
    openDetails(<InsuranceProposalDetails item={item as unknown as ProposalListItem} />);
  }, [openDetails]);

  // Compute displayed data based on column filters (for totals and empty state)
  const displayedData = useMemo(() => {
    const hasFilters = Object.values(columnFilters).some(arr => arr.length > 0);
    if (!hasFilters) return data;

    return data.filter(item => {
      for (const [colKey, selectedValues] of Object.entries(columnFilters)) {
        if (selectedValues.length > 0) {
          const itemValue = String(item[colKey as keyof typeof item] ?? '');
          if (!selectedValues.includes(itemValue)) return false;
        }
      }
      return true;
    });
  }, [data, columnFilters]);

  // Initialize all rows as selected when data or filters change
  const displayedDataIds = useMemo(() =>
    displayedData.map(item => item.id).join(','),
    [displayedData]
  );

  useEffect(() => {
    const allIds = new Set(displayedData.map(item => item.id));
    setSelectedRows(allIds);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [displayedDataIds]);

  // Calculate totals based on selected rows
  const totals = useMemo(() => {
    const selectedItems = displayedData.filter(item => selectedRows.has(item.id));
    const count = selectedItems.length || 1;

    const totalAmount = selectedItems.reduce((sum, i) => sum + (i.amount || 0), 0);
    const avgDays = selectedItems.reduce((sum, i) => sum + (i.days_in_stage || 0), 0) / count;

    return {
      totalAmount,
      avgDays,
      selectedCount: selectedItems.length
    };
  }, [displayedData, selectedRows]);

  const formatCurrency = useCallback((value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }, []);

  // Format date for display (DD/MM/YY - compact format)
  const formatDate = useCallback((dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
    } catch {
      return '-';
    }
  }, []);

  const toInitCaps = (str: string) =>
    str.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());

  const formatClientName = (name: string): string => {
    const words = toInitCaps(name.trim()).split(/\s+/);
    if (words.length < 4) return words.join(' ');
    return `${words[0]} ${words[1]} ${words[words.length - 1]}`;
  };

  const formatShortName = (name: string): string => {
    const words = name.trim().split(/\s+/);
    if (words.length <= 1) return name.trim();
    return `${words[0]} ${words[words.length - 1]}`;
  };

  const formatCompactPA = (value: number): string => {
    const abs = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    if (abs >= 1_000_000)
      return `${sign}${(abs / 1_000_000).toFixed(3)}Mi`;
    if (abs >= 1_000)
      return `${sign}${(abs / 1_000).toFixed(3)}K`;
    return `${sign}${Math.round(abs)}`;
  };

  const cellFont = 'clamp(0.7rem, 0.5rem + 0.4cqi, 0.875rem)';
  const headerFont = 'clamp(0.75rem, 0.58rem + 0.4cqi, 1rem)';

  // Dynamic columns based on active tab and selected status
  const columns = useMemo(() => {
    const result = [
      {
        key: 'name',
        title: 'Cliente',
        width: '33%',
        filterable: true,
        align: 'left' as const,
        headerAlign: 'left' as const,
        render: (value: unknown) => {
          const nameValue = value ? String(value).trim() : '';
          if (!nameValue || nameValue.toLowerCase() === 'null') {
            return (
              <span className="pl-2 truncate italic font-light line-clamp-2"
                style={{ color: theme.text.layer1, fontSize: 'clamp(0.8rem, 0.5rem + 0.4cqi, 1rem)' }}>
                (Nome não informado)
              </span>
            );
          }
          return (
            <span className="pl-2 truncate font-light line-clamp-2" style={{ color: theme.text.layer1, fontSize: 'clamp(0.55rem, 0.6rem + 0.4cqi, 1.1rem)' }}>
              {formatClientName(nameValue)}
            </span>
          );
        }
      },
      {
        key: 'team_name',
        title: 'Time',
        width: '14%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'string' as const,
        filterable: true,
        render: (value: unknown) => (
          <span className="pl-1 truncate line-clamp-2 font-semibold " style={{ color: theme.text.layer1, fontSize: 'clamp(0.4rem, 0.48rem + 0.38cqi, 0.8rem)' }}>
            {String(value || '-')}
          </span>
        )
      },
      {
        key: 'advisor_name',
        title: 'Assessor',
        width: '22%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'string' as const,
        filterable: true,
        render: (value: unknown) => (
          <span className="pl-1 truncate line-clamp-2 font-light" style={{ color: theme.text.layer1, fontSize: 'clamp(0.65rem, 0.65rem + 0.4cqi, 1.1rem)' }}>
            {value ? formatShortName(String(value)) : '-'}
          </span>
        )
      },
      {
        key: 'specialist_name',
        title: 'Especialista',
        width: '24%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'string' as const,
        filterable: true,
        render: (value: unknown) => (
          <span className="pl-1 truncate line-clamp-2 font-light" style={{ color: theme.text.layer1, fontSize: 'clamp(0.65rem, 0.65rem + 0.4cqi, 1.1rem)' }}>
            {value ? formatShortName(String(value)) : '-'}
          </span>
        )
      },
      {
        key: 'created_date',
        title: 'Criação',
        width: '15%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'string' as const,
        render: (value: unknown) => (
          <span className="pl-2 truncate line-clamp-2" style={{ color: theme.text.layer1, fontSize: 'clamp(0.75rem, 0.55rem + 0.4cqi, 1rem)' }}>
            {formatDate(value as string | null)}
          </span>
        )
      },
      {
        key: 'issue_date',
        title: 'Emissão',
        width: '15%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'string' as const,
        render: (value: unknown) => (
          <span className="pl-2 truncate line-clamp-2" style={{ color: value ? theme.green.medium : theme.text.layer3, fontSize: 'clamp(0.75rem, 0.55rem + 0.4cqi, 1rem)' }}>
            {formatDate(value as string | null)}
          </span>
        )
      },
      {
        key: 'days_in_stage',
        title: 'Dias',
        width: '11%',
        align: 'left' as const,
        headerAlign: 'left' as const,
        sortable: true,
        sortType: 'number' as const,
        render: (value: unknown) => (
          <span
            className="font-semibold pl-4 truncate line-clamp-2"
            style={{ color: Number(value) > 100 ? theme.red.medium : theme.text.layer1, fontSize: 'clamp(0.75rem, 0.55rem + 0.4cqi, 1rem)' }}
          >
            {String(value)}
          </span>
        )
      },
      {
        key: 'amount',
        title: 'PA',
        width: '12%',
        align: 'center' as const,
        headerAlign: 'center' as const,
        sortable: true,
        sortType: 'number' as const,
        render: (value: unknown) => (
          <span className="pl-2 truncate line-clamp-2 font-medium " style={{ color: theme.green.medium, fontSize: 'clamp(0.45rem, 0.58rem + 0.4cqi, 1rem)' }}>
            {formatCompactPA(Number(value))}
          </span>
        )
      },
      {
        key: 'id',
        title: 'Link',
        width: '7%',
        align: 'center' as const,
        headerAlign: 'left' as const,
        sortable: false,
        render: (_value: unknown, item: Record<string, unknown>) => {
          const typedItem = item as unknown as ProposalListItem;
          const isEmitido = typedItem.registration_status === 'Emitido';
          const slug = (typedItem.name || '').toLowerCase().trim().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
          const url = isEmitido
            ? sfPortalInsurancePolicyUrl(typedItem.id, typedItem.policy_number)
            : sfPortalOpportunityUrl(typedItem.id, slug);
          return (
            <a
              href={url ?? undefined}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center justify-center cursor-pointer hover:opacity-70 transition-opacity"
            >
              <ExternalLink size={14} style={{ color: theme.blue.medium }} />
            </a>
          );
        }
      }
    ];

    if (selectedStatus === 'Emitido') {
      return result.filter(col => col.key !== 'created_date');
    }
    if (selectedStatus !== null) {
      return result.filter(col => col.key !== 'issue_date');
    }
    return result;
  }, [theme, formatCurrency, formatDate, selectedStatus]);

  // Check if any filter is active
  const hasActiveFilters = Object.values(columnFilters).some(arr => arr.length > 0) || selectedStatus !== null;

  // Clear all filters
  const handleClearFilters = () => {
    setColumnFilters({});
    setSelectedStatus(null);
  };

  return (
    <Card fullscreen={false} fullscreenWidth="80%" fullscreenHeight="85%" className="p-0">
      {({ toggleFullscreen }) => (
        <div className="flex flex-col h-full min-h-0" style={{ containerType: 'inline-size' }}>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="absolute top-2 z-20 flex-shrink-0 flex font-semibold items-center justify-center cursor-pointer transition-all ease-in-out duration-400"
              style={{
                right: 'calc(2 * clamp(28px, 26px + 1cqi, 44px) + 1.5rem)',
                padding: 'clamp(6px, 2px + 0.35cqi, 10px)',
                borderWidth: '1px',
                borderStyle: 'solid',
                borderRadius: '8px',
                backgroundColor: theme.background.layer3,
                borderColor: theme.border.layer2,
                color: theme.text.layer2,
                fontSize: '0.75rem',
              }}
            >
              <FiTrash2 className="shrink-0 w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setColumnVisibilityOpen(!columnVisibilityOpen)}
            aria-label="Selecionar colunas visíveis"
            aria-pressed={columnVisibilityOpen}
            className="absolute top-2 z-20 shrink-0 transition-all cursor-pointer flex items-center justify-center"
            style={{
              right: 'calc(clamp(28px, 26px + 1cqi, 44px) + 1rem)',
              backgroundColor: columnVisibilityOpen ? theme.pink.dark : theme.pink.medium,
              padding: 'clamp(6px, 2px + 0.3cqi, 10px)',
              borderRadius: 'clamp(8px, 6px + 0.3cqi, 14px)',
              width: 'clamp(28px, 26px + 1cqi, 44px)',
              height: 'clamp(28px, 26px + 1cqi, 44px)',
              border: 'none',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = theme.pink.dark; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = columnVisibilityOpen ? theme.pink.dark : theme.pink.medium; }}
          >
            <FiSettings size={16} color="white" strokeWidth={2.5} style={{ width: '70%', height: '70%' }} />
          </button>
          <button
            onClick={toggleFullscreen}
            className="absolute top-2 right-2 z-20 shrink-0 transition-all cursor-pointer flex items-center justify-center"
            style={{
              backgroundColor: theme.pink.medium,
              padding: 'clamp(6px, 2px + 0.3cqi, 10px)',
              borderRadius: 'clamp(8px, 6px + 0.3cqi, 14px)',
              width: 'clamp(28px, 26px + 1cqi, 44px)',
              height: 'clamp(28px, 26px + 1cqi, 44px)',
              border: 'none',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = theme.pink.dark; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = theme.pink.medium; }}
          >
            <svg width="100%" height="100%" viewBox="0 0 32 32" fill="none">
              <path
                d="M5.33325 10.6667V8.00004C5.33325 7.2928 5.6142 6.61452 6.1143 6.11442C6.6144 5.61433 7.29267 5.33337 7.99992 5.33337H10.6666M5.33325 21.3334V24C5.33325 24.7073 5.6142 25.3856 6.1143 25.8857C6.6144 26.3858 7.29267 26.6667 7.99992 26.6667H10.6666M21.3333 5.33337H23.9999C24.7072 5.33337 25.3854 5.61433 25.8855 6.11442C26.3856 6.61452 26.6666 7.2928 26.6666 8.00004V10.6667M21.3333 26.6667H23.9999C24.7072 26.6667 25.3854 26.3858 25.8855 25.8857C26.3856 25.3856 26.6666 24.7073 26.6666 24V21.3334M21.3333 21.3334L17.9999 18M10.6666 14.6667C10.6666 15.192 10.77 15.7121 10.9711 16.1974C11.1721 16.6827 11.4667 17.1237 11.8382 17.4951C12.2096 17.8666 12.6505 18.1612 13.1359 18.3622C13.6212 18.5632 14.1413 18.6667 14.6666 18.6667C15.1919 18.6667 15.712 18.5632 16.1973 18.3622C16.6826 18.1612 17.1236 17.8666 17.495 17.4951C17.8664 17.1237 18.1611 16.6827 18.3621 16.1974C18.5631 15.7121 18.6666 15.192 18.6666 14.6667C18.6666 13.6058 18.2452 12.5884 17.495 11.8383C16.7449 11.0881 15.7275 10.6667 14.6666 10.6667C13.6057 10.6667 12.5883 11.0881 11.8382 11.8383C11.088 12.5884 10.6666 13.6058 10.6666 14.6667Z"
                stroke="white"
                strokeWidth="2.66667"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          {/* Header Section - Status de Propostas integrado */}
          <header className="shrink-0 mb-0">
            {/* Status Grid - 5 columns with dividers */}
            <div className="mb-0">
              {isLoadingStatus ? (
                <div className="grid grid-cols-[1fr_1fr_1fr_1fr_2fr]">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className={`flex flex-col px-6 py-2 ${i < 4 ? 'border-r' : ''}`}
                      style={{ borderColor: theme.border.layer1 }}
                    >
                      <Skeleton className="h-4 w-24 mb-2" />
                      <Skeleton className="h-12 w-16" />
                    </div>
                  ))}
                </div>
              ) : (
                <div
                  className="grid grid-cols-[repeat(4,1fr)_1.8fr] relative"
                  style={{ containerType: 'inline-size' }}
                >
                  {statusData.map((status, index) => {
                    const isSelected = selectedStatus === status.key;
                    const isTargetGoal = status.isHighlighted;

                    const rawPercent = isTargetGoal
                      ? (status.totalAmount / metaEmitido) * 100
                      : totalVolume > 0 ? (status.count / totalVolume) * 100 : 0;

                    if (isTargetGoal) {
                      return (
                        <div
                          key={status.key}
                          className={`
                          relative flex items-center group overflow-hidden
                          cursor-pointer hover:opacity-80 transition-opacity
                          ${isSelected ? 'opacity-100' : selectedStatus ? 'opacity-40' : ''}
                        `}
                          style={{
                            animationDelay: `${animationDelay + index * 0.05}s`,
                            backgroundColor: isSelected ? tableRowHoverColor : 'transparent',
                            borderColor: theme.border.layer1,
                            gap: 'clamp(0.125rem, 0.1rem + 0.5cqi, 0.25rem)',
                            paddingTop: 'clamp(0.8rem, 0.8rem + 1.2cqi, 1.2rem)',
                            paddingBottom: 'clamp(0.15rem, 0.05rem + 0.3cqi, 0.25rem)',
                            paddingRight: 'clamp(0.75rem, 0.45rem + 1.5cqi, 1.5rem) ',
                            paddingLeft: 'clamp(0.35rem, 0.15rem + 1cqi, 0.7rem) ',
                          }}
                          onClick={() => handleStatusClick(status.key)}
                        >
                          <div className="flex flex-col min-w-0">
                            <span
                              className="font-normal tracking-wide truncate mb-3"
                              title={status.label}
                              style={{ color: theme.text.layer1, fontSize: 'clamp(0.7rem, 0.35rem + 1cqi, 1rem)' }}
                            >
                              {status.label}
                            </span>
                            <span
                              className="font-bold tabular-nums tracking-tighter whitespace-nowrap leading-none mt-auto"
                              style={{
                                color: '#2E7AD1',
                                fontSize: 'clamp(0.75rem, 0.15rem + 2.8cqi, 1.75rem)'
                              }}
                            >
                              {renderCurrencyCompact(status.totalAmount)}
                            </span>
                            <span
                              className="px-1.5 py-0.5 rounded font-medium w-fit mt-2"
                              style={{
                                color: theme.text.layer2,
                                fontSize: 'clamp(0.6rem, 0.3rem + 0.7cqi, 0.9rem)'
                              }}
                            >
                              <span className="font-bold" style={{ fontSize: 'clamp(0.75rem, 0.3rem + 1cqi, 1.2rem)' }}>{status.count.toLocaleString('pt-BR')}</span> Emissões
                            </span>
                          </div>

                          <div className="flex flex-col self-stretch flex-1 min-w-0 overflow-hidden pt-3" style={{ maxHeight: '6rem' }}>
                            <svg viewBox="0 0 220 140" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
                              <path
                                d="M 30 115 A 90 90 0 0 1 210 115"
                                stroke={theme.border.layer4}
                                strokeWidth="20"
                                fill="none"
                                strokeLinecap="round"
                              />
                              {rawPercent > 0 && (
                                <path
                                  d="M 30 115 A 90 90 0 0 1 210 115"
                                  stroke={rawPercent > 70 ? theme.green.dark : rawPercent > 30 ? theme.yellow.medium : theme.red.dark}
                                  strokeWidth="20"
                                  fill="none"
                                  strokeLinecap="round"
                                  strokeDasharray={Math.PI * 90}
                                  strokeDashoffset={Math.PI * 90 * (1 - Math.min(rawPercent, 100) / 100)}
                                  style={{ transition: 'stroke-dashoffset 0.7s ease-out' }}
                                />
                              )}
                              <text
                                x="120"
                                y="100"
                                textAnchor="middle"
                                className="font-semibold tabular-nums tracking-tighter"
                                style={{ fontSize: '40px', fill: theme.text.layer1 }}
                              >
                                {Math.round(rawPercent)}%
                              </text>
                              <text
                                x="120"
                                y="130"
                                textAnchor="middle"
                                className="font-medium"
                                style={{ fontSize: '17px', fill: theme.text.layer2 }}
                              >
                                Meta: {formatCurrencyCompact(metaEmitido)}
                              </text>
                            </svg>
                          </div>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={status.key}
                        className={`
                        relative flex flex-col group
                        cursor-pointer hover:opacity-80 transition-opacity
                        ${isSelected ? 'opacity-100' : selectedStatus ? 'opacity-40' : ''}
                      `}
                        style={{
                          animationDelay: `${animationDelay + index * 0.05}s`,
                          backgroundColor: isSelected ? tableRowHoverColor : 'transparent',
                          paddingTop: 'clamp(0.8rem, 0.8rem + 1.2cqi, 1.2rem)',
                          paddingRight: 'clamp(0.35rem, 0.15rem + 1cqi, 0.7rem)',
                          paddingBottom: 'clamp(0.15rem, 0.05rem + 0.3cqi, 0.25rem)',
                          paddingLeft: index === 0 ? 'clamp(0.6rem, 0.5rem + 1.2cqi, 1.2rem)' : 'clamp(0.35rem, 0.15rem + 1cqi, 0.7rem)'
                        }}
                        onClick={() => handleStatusClick(status.key)}
                      >
                        {index !== statusData.length - 1 && (
                          <div
                            className="absolute right-0 top-2 bottom-2 w-px"
                            style={{ backgroundColor: theme.border.layer1 }}
                          />
                        )}

                        <span
                          className="font-normal tracking-wide truncate mb-3"
                          title={status.label}
                          style={{ color: theme.text.layer1, fontSize: 'clamp(0.7rem, 0.35rem + 1cqi, 1rem)' }}
                        >
                          {status.label}
                        </span>
                        <span
                          className="font-bold tabular-nums tracking-tighter whitespace-nowrap leading-none mt-auto"
                          style={{
                            color: theme.text.layer1,
                            fontSize: 'clamp(0.75rem, 0.1rem + 2.8cqi, 1.75rem)'
                          }}
                        >
                          {renderCurrencyCompact(status.totalAmount)}
                        </span>
                        <span
                          className="flex items-center gap-1 px-1.5 py-0.5 rounded font-medium w-fit mt-2"
                          style={{
                            color: theme.text.layer2,
                            fontSize: 'clamp(0.6rem, 0.3rem + 0.7cqi, 0.9rem)'
                          }}
                        >
                          <span className="font-bold" style={{ fontSize: 'clamp(0.75rem, 0.3rem + 1cqi, 1.2rem)' }}>{status.count.toLocaleString('pt-BR')}</span> Propostas
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          </header>

          {/* Table */}
          <div className="proposals-table-cq flex-1 min-h-0 overflow-hidden" style={{ containerType: 'inline-size' }}>
            <style>{`.proposals-table-cq th { font-size: ${headerFont} !important; }`}</style>
            {isLoading ? (
              <LoadingState />
            ) : displayedData.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm" style={{ color: theme.text.layer2 }}>
                  Nenhum registro encontrado
                </p>
              </div>
            ) : (
              <Table
                withAnimationDelay={true}
                animationDelayBase={animationDelay}
                animationDelayIncrement={0.03}
                columns={columns}
                items={data.map((item: ProposalListItem, idx: number) => ({
                  ...item,
                  id: item.id ?? `proposal-${idx}`
                }))}
                selectable
                selectedRows={selectedRows}
                onSelectionChange={handleSelectionChange}
                onRowClick={handleRowClick}
                columnFilters={columnFilters}
                onColumnFiltersChange={setColumnFilters}
                customRowBackgroundColor={tableBackgroundColor}
                headerBackgroundColor={tableHeaderColor}
                rowHoverBackgroundColor={tableRowHoverColor}
                headerPaddingX="px-0"
                columnVisibilityOpen={columnVisibilityOpen}
                visibleColumns={visibleColumns}
                onVisibleColumnsChange={setVisibleColumns}
              />
            )}
          </div>

          {/* Totals Row */}
          {!isLoading && displayedData.length > 0 && (
            <footer
              className="flex justify-end items-center px-3 py-2 border-t flex-shrink-0"
              aria-label="Total de propostas"
              style={{
                backgroundColor: theme.background.layer2,
                borderColor: theme.border.layer2,
                color: theme.text.layer1
              }}
            >
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <span
                    className="text-xs font-normal tracking-wider"
                    style={{ color: theme.text.layer2 }}
                  >
                    Propostas:
                  </span>
                  <span
                    className="font-bold text-base leading-none pl-1"
                    style={{ color: theme.text.layer1 }}
                  >
                    {totals.selectedCount.toLocaleString('pt-BR')}
                  </span>
                </div>
                <div
                  className="w-px h-6"
                  style={{ backgroundColor: theme.border.layer1 }}
                />
                <div className="text-right">
                  <span
                    className="text-xs font-medium tracking-wider"
                    style={{ color: theme.text.layer2 }}
                  >
                    Valor Pipeline:
                  </span>
                  <data
                    value={totals.totalAmount}
                    className="font-bold text-base leading-none pl-1"
                    style={{ color: '#10b981' }}
                  >
                    {formatCurrencyCompact(totals.totalAmount)}
                  </data>
                </div>
              </div>
            </footer>
          )}
        </div>
      )}
    </Card>
  );
}
