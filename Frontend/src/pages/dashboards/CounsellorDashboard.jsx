import React, { useState, useEffect } from 'react';
import { 
  Users, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Search, 
  Filter, 
  FileText, 
  ShieldAlert, 
  Activity, 
  PhoneCall, 
  ArrowUpRight 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GButton } from '../../components/common/UX4GButton';
import { RiskBadge, StatusBadge } from '../../components/common/UX4GBadge';
import { UX4GTable } from '../../components/common/UX4GTable';
import { CaseDetailModal } from '../../components/counsellor/CaseDetailModal';
import { caseService } from '../../services/caseService';

export const CounsellorDashboard = () => {
  const { currentUser } = useAuth();
  const [cases, setCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseModalOpen, setCaseModalOpen] = useState(false);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    const data = await caseService.getAllCases();
    setCases(data);
  };

  const handleCaseUpdated = (updatedCase) => {
    setCases(prev => prev.map(c => c.id === updatedCase.id ? updatedCase : c));
    setSelectedCase(updatedCase);
  };

  const openCaseDetails = (c) => {
    setSelectedCase(c);
    setCaseModalOpen(true);
  };

  // Filter calculations
  const filteredCases = cases.filter((c) => {
    const matchesSearch = 
      c.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
      c.beneficiaryName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.district.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRisk = riskFilter === 'ALL' || c.riskLevel.toUpperCase() === riskFilter;
    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    return matchesSearch && matchesRisk && matchesStatus;
  });

  // KPI calculations
  const totalAssigned = cases.length;
  const highRiskCount = cases.filter(c => c.riskLevel === 'High' || c.riskLevel === 'Critical').length;
  const urgentSlaCount = cases.filter(c => c.slaHoursRemaining <= 4 && c.status !== 'COMPLETED').length;
  const completedCount = cases.filter(c => c.status === 'COMPLETED').length;

  const columns = [
    {
      header: 'Case ID & Beneficiary',
      key: 'id',
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{row.id}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>{row.beneficiaryName}</div>
        </div>
      ),
    },
    {
      header: 'District',
      key: 'district',
      render: (_, row) => <span style={{ fontSize: '0.85rem' }}>{row.district}</span>,
    },
    {
      header: 'Distress Score / Trend',
      key: 'distressScore',
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{row.distressScore} / 100</div>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: row.trend.includes('Worsening') ? 'var(--ux4g-danger)' : 'var(--ux4g-success)' }}>
            {row.trend} ({row.baselineDeviation})
          </div>
        </div>
      ),
    },
    {
      header: 'Risk Priority',
      key: 'riskLevel',
      render: (_, row) => <RiskBadge level={row.riskLevel} size="sm" />,
    },
    {
      header: 'Status',
      key: 'status',
      render: (_, row) => <StatusBadge status={row.status} size="sm" />,
    },
    {
      header: 'Statutory SLA',
      key: 'slaHoursRemaining',
      render: (_, row) => (
        <div style={{ fontSize: '0.825rem' }}>
          <span style={{ fontWeight: 700, color: row.slaHoursRemaining <= 4 ? 'var(--ux4g-danger)' : 'var(--ux4g-text-primary)' }}>
            {row.slaHoursRemaining}h remaining
          </span>
          <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>
            {row.slaStatus}
          </div>
        </div>
      ),
    },
    {
      header: 'Actions',
      key: 'actions',
      render: (_, row) => (
        <UX4GButton
          variant="outline"
          size="sm"
          icon={FileText}
          onClick={() => openCaseDetails(row)}
        >
          View Case File
        </UX4GButton>
      ),
    },
  ];

  return (
    <DashboardShell
      title="Clinical Caseload Management"
      subtitle={`Welcome, ${currentUser?.name} • Licensed Clinical Psychologist • South Delhi Atrocity Monitoring Unit`}
    >
      {/* Actionable KPI Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Active Assigned Cases
            </span>
            <Users size={18} color="var(--ux4g-violet-700)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
            {totalAssigned}
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            100% within statutory jurisdiction
          </p>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--ux4g-danger)', fontWeight: 600, textTransform: 'uppercase' }}>
              High-Risk / Critical Triage
            </span>
            <ShieldAlert size={18} color="var(--ux4g-danger)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--ux4g-danger)' }}>
            {highRiskCount}
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-danger-text)', marginTop: '4px' }}>
            Requires clinical attention today
          </p>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', color: '#B45309', fontWeight: 600, textTransform: 'uppercase' }}>
              Urgent SLA Deadlines
            </span>
            <Clock size={18} color="#D97706" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#B45309' }}>
            {urgentSlaCount}
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            &lt; 4 hours remaining to statutory alert
          </p>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--ux4g-success)', fontWeight: 600, textTransform: 'uppercase' }}>
              Completed Outcomes
            </span>
            <CheckCircle2 size={18} color="var(--ux4g-success)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--ux4g-success)' }}>
            {completedCount}
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            Transitioned to monthly check-ins
          </p>
        </UX4GCard>
      </div>

      {/* Case Management Workspace */}
      <UX4GCard elevation={2} liftOnHover={false} style={{ padding: '24px' }}>
        {/* Search & Filter Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
              Assigned Triage Caseload Queue
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>
              Search, filter, and inspect case dossiers with longitudinal distress indicators
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: '240px' }}>
              <Search size={16} color="var(--ux4g-text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search case ID, name, district..."
                className="ux4g-focus-glow"
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 36px',
                  borderRadius: 'var(--radius-md)',
                  border: '1.5px solid var(--ux4g-border)',
                  fontSize: '0.85rem',
                }}
              />
            </div>

            {/* Risk Filter */}
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="ux4g-focus-glow"
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                border: '1.5px solid var(--ux4g-border)',
                fontSize: '0.85rem',
                backgroundColor: '#FFF',
              }}
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical Risk Only</option>
              <option value="HIGH">High Risk Only</option>
              <option value="MEDIUM">Medium Risk Only</option>
              <option value="LOW">Low Risk Only</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="ux4g-focus-glow"
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                border: '1.5px solid var(--ux4g-border)',
                fontSize: '0.85rem',
                backgroundColor: '#FFF',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ESCALATED">Escalated</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>
        </div>

        {/* Caseload Table */}
        <UX4GTable
          columns={columns}
          data={filteredCases}
          caption="Counsellor assigned cases table with distress metrics and triage actions"
        />
      </UX4GCard>

      {/* Case Detail Modal Interface */}
      <CaseDetailModal
        isOpen={caseModalOpen}
        onClose={() => setCaseModalOpen(false)}
        caseData={selectedCase}
        onCaseUpdated={handleCaseUpdated}
      />
    </DashboardShell>
  );
};
