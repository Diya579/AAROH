import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  ArrowUpRight,
  Shield,
  HeartHandshake,
  Calendar,
  Sparkles,
  CheckSquare,
  AlertTriangle,
  Scale
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GButton } from '../../components/common/UX4GButton';
import { RiskBadge, StatusBadge } from '../../components/common/UX4GBadge';
import { UX4GTable } from '../../components/common/UX4GTable';
import { CaseDetailModal } from '../../components/counsellor/CaseDetailModal';
import { OutcomeRecordModal } from '../../components/counsellor/OutcomeRecordModal';
import { InterventionActionModal } from '../../components/counsellor/InterventionActionModal';
import { caseService } from '../../services/caseService';

export const CounsellorDashboard = () => {
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };

  const [cases, setCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseModalOpen, setCaseModalOpen] = useState(false);
  const [outcomeModalOpen, setOutcomeModalOpen] = useState(false);
  const [interventionModalOpen, setInterventionModalOpen] = useState(false);

  // Outcome recording state for outcomes tab
  const [selectedCaseForOutcome, setSelectedCaseForOutcome] = useState('');
  const [newOutcomeType, setNewOutcomeType] = useState('Counselling provided');
  const [newOutcomeNotes, setNewOutcomeNotes] = useState('');
  const [followUpDate, setFollowUpDate] = useState('2026-09-12');
  const [outcomeSuccessAlert, setOutcomeSuccessAlert] = useState(false);

  // Historical recorded outcomes log
  const [recordedOutcomes, setRecordedOutcomes] = useState([
    {
      id: 'OUT-9821-01',
      caseId: 'AAROH-DEL-2026-001',
      beneficiary: 'Meera Sharma',
      type: 'Counselling provided',
      date: 'Today, 11:30 AM',
      notes: 'Conducted 45-min somatic grounding. Distress stabilized from score 82 to 54. Beneficiary confirmed safe housing.',
      status: 'Stabilized',
      officer: 'Dr. Rajesh Verma'
    },
    {
      id: 'OUT-9818-04',
      caseId: 'AAROH-DEL-2026-004',
      beneficiary: 'Geeta Devi',
      type: 'Referred for Medical Care',
      date: 'Yesterday, 04:15 PM',
      notes: 'Referred to AIIMS Clinical Psychiatry for acute sleep disruption evaluation. DM cell notified.',
      status: 'Referred',
      officer: 'Dr. Rajesh Verma'
    },
    {
      id: 'OUT-9815-02',
      caseId: 'AAROH-DEL-2026-002',
      beneficiary: 'Sita Ram',
      type: 'Follow-up required',
      date: '04 Sep 2026',
      notes: 'Scheduled follow-up with DLSA counsel regarding witness intimidation report.',
      status: 'In Progress',
      officer: 'Dr. Rajesh Verma'
    },
  ]);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    const data = await caseService.getAllCases();
    setCases(data);
    if (data.length > 0 && !selectedCaseForOutcome) {
      setSelectedCaseForOutcome(data[0].id);
    }
  };

  const handleCaseUpdated = (updatedCase) => {
    setCases(prev => prev.map(c => c.id === updatedCase.id ? updatedCase : c));
    setSelectedCase(updatedCase);
  };

  const openCaseDetails = (c) => {
    setSelectedCase(c);
    setCaseModalOpen(true);
  };

  const handleRecordOutcomeSubmit = (e) => {
    e.preventDefault();
    const targetCase = cases.find(c => c.id === selectedCaseForOutcome);
    if (!targetCase) return;

    const newEntry = {
      id: `OUT-${Math.floor(1000 + Math.random() * 9000)}`,
      caseId: targetCase.id,
      beneficiary: targetCase.beneficiaryName,
      type: newOutcomeType,
      date: 'Just Now',
      notes: newOutcomeNotes || 'Standard clinical intervention session recorded under AAROH statutory protocol.',
      status: newOutcomeType === 'Counselling provided' ? 'Stabilized' : 'In Progress',
      officer: 'Dr. Rajesh Verma'
    };

    setRecordedOutcomes(prev => [newEntry, ...prev]);
    setOutcomeSuccessAlert(true);
    setNewOutcomeNotes('');
    setTimeout(() => setOutcomeSuccessAlert(false), 3500);

    // Update case status to COMPLETED if resolved
    if (newOutcomeType === 'Counselling provided' || newOutcomeType === 'Resolved') {
      const updated = { ...targetCase, status: 'COMPLETED' };
      handleCaseUpdated(updated);
    }
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
      subtitle={`Welcome, ${currentUser?.name} • Lead Clinical Counsellor • South Delhi Atrocity Monitoring Unit`}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: CASELOAD OVERVIEW
          ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Actionable KPI Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
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
              <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-warning-text)', marginTop: '4px' }}>
                Window expiring &lt; 4 hours
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
                {completedCount + recordedOutcomes.length}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                Stabilized &amp; verified this cycle
              </p>
            </UX4GCard>
          </div>

          {/* Urgent Clinical Alert Banner */}
          <div style={{ backgroundColor: '#FEF2F2', border: '1.5px solid #FCA5A5', borderRadius: 'var(--radius-md)', padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <ShieldAlert size={22} color="#DC2626" style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>
                <strong style={{ fontSize: '0.92rem', color: '#991B1B' }}>
                  Statutory Escalation Alert: Case #AAROH-DEL-2026-001 (Meera Sharma)
                </strong>
                <p style={{ fontSize: '0.82rem', color: '#B91C1C', marginTop: '2px' }}>
                  Acoustic distress score increased to 82 (+24 from baseline). Linguistic markers flag acute anxiety. SLA requires mandatory clinical review by 19:00 IST.
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <UX4GButton variant="danger" size="sm" onClick={() => {
                const target = cases.find(c => c.id === 'AAROH-DEL-2026-001') || cases[0];
                openCaseDetails(target);
              }}>
                Open Case Dossier
              </UX4GButton>
              <UX4GButton variant="outline" size="sm" onClick={() => handleTabChange('interventions')}>
                Review Interventions
              </UX4GButton>
            </div>
          </div>

          {/* Priority Caseload Quick Roster */}
          <UX4GCard elevation={1} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Today's Clinical Triage Priority Queue
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-muted)' }}>
                  Cases sorted by statutory escalation severity and SLA countdown
                </p>
              </div>
              <UX4GButton variant="outline" size="sm" onClick={() => handleTabChange('cases')}>
                View All {cases.length} Cases
              </UX4GButton>
            </div>

            <UX4GTable
              columns={columns}
              data={cases.slice(0, 4)}
              caption="Clinical triage priority cases"
            />
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 2: ASSIGNED CASES (FULL CASELOAD & FILTERING)
          ========================================================================= */}
      {activeTab === 'cases' && (
        <UX4GCard elevation={1} padding="24px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                Assigned Clinical Caseload ({filteredCases.length} Cases)
              </h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                Filter and inspect all beneficiaries assigned to your clinical care unit under South Delhi jurisdiction.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
              <div style={{ position: 'relative' }}>
                <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--ux4g-text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search by ID, Name or District..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    padding: '8px 12px 8px 32px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--ux4g-border)',
                    fontSize: '0.85rem',
                    width: '240px',
                  }}
                />
              </div>

              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.85rem' }}
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Priority</option>
                <option value="HIGH">High Priority</option>
                <option value="MEDIUM">Medium Priority</option>
                <option value="LOW">Low Priority</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.85rem' }}
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending Review</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
              </select>
            </div>
          </div>

          <UX4GTable
            columns={columns}
            data={filteredCases}
            emptyMessage="No assigned cases match the selected filter criteria."
            caption="Complete filtered caseload table"
          />
        </UX4GCard>
      )}

      {/* =========================================================================
          TAB 3: INTERVENTIONS & SLA (HUMAN DECISION WORKFLOW)
          ========================================================================= */}
      {activeTab === 'interventions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Statutory Rule Notice */}
          <div style={{ backgroundColor: 'var(--ux4g-violet-100)', border: '1.5px solid #3A2312', boxShadow: '2px 2px 0px #3A2312', borderRadius: 'var(--radius-md)', padding: '18px 22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Scale size={18} color="var(--ux4g-violet-700)" />
              <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)' }}>
                Rule 5 Compliance: AI Recommends • Human Decides &amp; Sanctions
              </strong>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.5 }}>
              The AAROH platform algorithmically flags distress deviations and generates intervention suggestions. Certified clinical counsellors and district magistrates maintain absolute authority over final care decisions.
            </p>
          </div>

          {/* Active Interventions Board */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
            {cases.filter(c => c.status !== 'COMPLETED').map((c) => (
              <UX4GCard key={c.id} elevation={1} padding="22px">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>{c.id}</div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                      {c.beneficiaryName}
                    </h4>
                  </div>
                  <RiskBadge level={c.riskLevel} size="sm" />
                </div>

                <div style={{ backgroundColor: 'var(--ux4g-bg)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '14px', fontSize: '0.82rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--ux4g-text-secondary)' }}>AI Recommended Action:</span>
                    <strong style={{ color: 'var(--ux4g-violet-950)' }}>{c.recommendedIntervention || 'Psychological Counselling'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--ux4g-text-secondary)' }}>Statutory SLA Remaining:</span>
                    <strong style={{ color: c.slaHoursRemaining <= 4 ? 'var(--ux4g-danger)' : 'var(--ux4g-text-primary)' }}>
                      {c.slaHoursRemaining} Hours ({c.slaStatus})
                    </strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--ux4g-text-secondary)' }}>Primary Assignee:</span>
                    <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600 }}>Dr. Rajesh Verma</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <UX4GButton
                    variant="primary"
                    size="sm"
                    fullWidth
                    icon={CheckSquare}
                    onClick={() => {
                      setSelectedCase(c);
                      setInterventionModalOpen(true);
                    }}
                  >
                    Manage Intervention
                  </UX4GButton>

                  <UX4GButton
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedCase(c);
                      setOutcomeModalOpen(true);
                    }}
                  >
                    Record Outcome
                  </UX4GButton>
                </div>
              </UX4GCard>
            ))}
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: OUTCOMES & NOTES (STATUTORY OUTCOME RECORDING)
          ========================================================================= */}
      {activeTab === 'outcomes' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {outcomeSuccessAlert && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1.5px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success-text)', fontWeight: 700 }}>
              <CheckCircle2 size={18} />
              <span>Intervention outcome successfully recorded and synced with District Nodal Oversight.</span>
            </div>
          )}

          {/* Outcome Recording Console Form */}
          <UX4GCard elevation={1} padding="24px">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
              Record Clinical Intervention Outcome
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)', marginBottom: '20px' }}>
              As per Section 14 of AAROH Implementation Protocol, all interventions must feed verified human outcomes back into the monitoring system.
            </p>

            <form onSubmit={handleRecordOutcomeSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px', alignItems: 'flex-start' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  Target Monitored Case:
                </label>
                <select
                  value={selectedCaseForOutcome}
                  onChange={(e) => setSelectedCaseForOutcome(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.88rem', backgroundColor: '#FFFFFF' }}
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} — {c.beneficiaryName} ({c.riskLevel} Risk)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  Statutory Outcome Category:
                </label>
                <select
                  value={newOutcomeType}
                  onChange={(e) => setNewOutcomeType(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.88rem', backgroundColor: '#FFFFFF' }}
                >
                  <option value="Counselling provided">Counselling Provided (Grounding &amp; Psychosocial Relief)</option>
                  <option value="Contacted & Confirmed Safe">Contacted &amp; Physical Safety Confirmed</option>
                  <option value="Follow-up required">Follow-up Required (Needs Scheduled Escalation)</option>
                  <option value="Referred for Medical Care">Referred for Specialized Medical/Psychiatric Care</option>
                  <option value="Witness Protection Coordination">Witness Protection Coordinated with Police</option>
                  <option value="Resolved">Resolved (Longitudinal Equilibrium Restored)</option>
                </select>
              </div>

              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  Authorized Clinical Observations &amp; Action Notes:
                </label>
                <textarea
                  rows="3"
                  value={newOutcomeNotes}
                  onChange={(e) => setNewOutcomeNotes(e.target.value)}
                  placeholder="Record clinical assessment, safety confirmation, grounding techniques utilized, and multi-agency coordination details..."
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.85rem', resize: 'vertical' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <UX4GButton variant="primary" size="md" icon={CheckCircle2} type="submit">
                  Save &amp; Commit Outcome
                </UX4GButton>
              </div>
            </form>
          </UX4GCard>

          {/* Historical Outcomes Roster Table */}
          <UX4GCard elevation={1} padding="24px">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '14px' }}>
              Historical Clinical Outcomes Log
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recordedOutcomes.map((out) => (
                <div key={out.id} style={{ padding: '16px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--ux4g-violet-700)', fontWeight: 700 }}>{out.id}</span>
                      <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)', marginLeft: '8px' }}>
                        {out.caseId} • {out.beneficiary}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.72rem' }}>{out.type}</span>
                      <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.72rem' }}>{out.status}</span>
                    </div>
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.5, margin: '4px 0 8px' }}>
                    {out.notes}
                  </p>
                  <div style={{ fontSize: '0.74rem', color: 'var(--ux4g-text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Logged by: {out.officer}</span>
                    <span>{out.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </UX4GCard>
        </div>
      )}

      {/* Case Detail Modal */}
      {selectedCase && (
        <CaseDetailModal
          isOpen={caseModalOpen}
          onClose={() => setCaseModalOpen(false)}
          caseData={selectedCase}
          onCaseUpdated={handleCaseUpdated}
        />
      )}

      {/* Outcome Recording Modal */}
      {selectedCase && (
        <OutcomeRecordModal
          isOpen={outcomeModalOpen}
          onClose={() => setOutcomeModalOpen(false)}
          caseData={selectedCase}
          onOutcomeSaved={handleCaseUpdated}
        />
      )}

      {/* Intervention Action Modal */}
      {selectedCase && (
        <InterventionActionModal
          isOpen={interventionModalOpen}
          onClose={() => setInterventionModalOpen(false)}
          caseData={selectedCase}
          onActionSaved={handleCaseUpdated}
        />
      )}
    </DashboardShell>
  );
};
