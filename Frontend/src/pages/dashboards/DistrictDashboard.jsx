import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ShieldCheck, 
  Users, 
  Eye, 
  ArrowUpRight, 
  Activity,
  AlertCircle,
  AlertTriangle,
  ShieldAlert,
  Clock,
  CheckCircle2,
  Scale,
  RefreshCw,
  Send,
  FileCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';
import { UX4GButton } from '../../components/common/UX4GButton';
import { RiskBadge, StatusBadge } from '../../components/common/UX4GBadge';
import { 
  RiskDistributionChart, 
  LongitudinalTrendChart, 
  InterventionMetricsChart, 
  ResponseTimeChart, 
  OutcomeDistributionChart 
} from '../../components/analytics';
import { CaseDetailModal } from '../../components/counsellor/CaseDetailModal';
import { caseService } from '../../services/caseService';
import { analyticsService } from '../../services/analyticsService';

export const DistrictDashboard = () => {
  const { currentUser } = useAuth();
  const districtName = currentUser?.district || 'South Delhi';

  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };

  const [analytics, setAnalytics] = useState(null);
  const [districtCases, setDistrictCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseModalOpen, setCaseModalOpen] = useState(false);
  const [rebalanceAlert, setRebalanceAlert] = useState(false);
  const [escalationActionAlert, setEscalationActionAlert] = useState('');

  // Counsellors list with rebalancing capability
  const [counsellors, setCounsellors] = useState([
    { id: 'CNS-01', name: 'Dr. Rajesh Verma', specialization: 'Trauma & PTSD', activeCaseload: 18, capacity: '90%', avgResponse: '1.4 hrs', status: 'Optimal' },
    { id: 'CNS-02', name: 'Dr. Sunita Rao', specialization: 'Adolescent & Child Atrocity Relief', activeCaseload: 14, capacity: '70%', avgResponse: '1.8 hrs', status: 'Optimal' },
    { id: 'CNS-03', name: 'Shri Vikram Malhotra', specialization: 'Rehabilitation & Legal Aid Liaison', activeCaseload: 19, capacity: '95%', avgResponse: '2.1 hrs', status: 'Near Limit' },
    { id: 'CNS-04', name: 'Dr. Priya Nambiar', specialization: 'Crisis De-escalation', activeCaseload: 12, capacity: '60%', avgResponse: '1.1 hrs', status: 'Optimal' },
  ]);

  useEffect(() => {
    loadDistrictData();
  }, [districtName]);

  const loadDistrictData = async () => {
    const data = await analyticsService.getDistrictAnalytics(districtName);
    setAnalytics(data);
    const cases = await caseService.getCasesByDistrict(districtName);
    setDistrictCases(cases);
  };

  const handleCaseUpdated = (updatedCase) => {
    setDistrictCases(prev => prev.map(c => c.id === updatedCase.id ? updatedCase : c));
    setSelectedCase(updatedCase);
    analyticsService.getDistrictAnalytics(districtName).then(setAnalytics);
  };

  const openCaseDetails = (c) => {
    setSelectedCase(c);
    setCaseModalOpen(true);
  };

  const handleRebalanceWorkload = () => {
    // Rebalance cases: move 2 from Vikram to Priya
    setCounsellors(prev => prev.map(c => {
      if (c.id === 'CNS-03') return { ...c, activeCaseload: 17, capacity: '85%', status: 'Optimal' };
      if (c.id === 'CNS-04') return { ...c, activeCaseload: 14, capacity: '70%', status: 'Optimal' };
      return c;
    }));
    setRebalanceAlert(true);
    setTimeout(() => setRebalanceAlert(false), 4000);
  };

  const handleTriggerEscalation = (actionText) => {
    setEscalationActionAlert(actionText);
    setTimeout(() => setEscalationActionAlert(''), 4000);
  };

  // 6 Statutory KPI Cards
  const districtKPIs = [
    { title: 'Total Monitored Cases', value: analytics?.totalCases || '142', sub: `${districtName} Jurisdiction`, color: 'var(--ux4g-violet-700)' },
    { title: 'High & Critical Risk', value: (analytics?.criticalCount + analytics?.highCount) || '11', sub: 'Immediate clinical review', color: 'var(--ux4g-danger)' },
    { title: 'Worsening Trends', value: analytics?.worseningCount || '7', sub: 'Algorithmic escalation alerts', color: 'var(--ux4g-warning)' },
    { title: 'Pending Interventions', value: analytics?.pendingInterventions || '5', sub: 'Within 24-hr SLA window', color: 'var(--ux4g-info)' },
    { title: 'Overdue Interventions', value: analytics?.overdueInterventions || '0', sub: '100% SLA compliance', color: 'var(--ux4g-success)' },
    { title: 'Completed Interventions', value: analytics?.completedInterventions || '126', sub: 'Successfully stabilized', color: 'var(--ux4g-violet-950)' },
  ];

  const counsellorColumns = [
    {
      header: 'Counsellor Name',
      key: 'name',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{val}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>{row.specialization}</div>
        </div>
      ),
    },
    {
      header: 'Active Caseload',
      key: 'activeCaseload',
      render: (val) => <span style={{ fontWeight: 700 }}>{val} cases</span>,
    },
    {
      header: 'Capacity Indicator',
      key: 'capacity',
      render: (val) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '80px', height: '8px', backgroundColor: 'var(--ux4g-border)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: val, height: '100%', backgroundColor: parseInt(val) > 90 ? 'var(--ux4g-danger)' : 'var(--ux4g-violet-700)' }} />
          </div>
          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{val}</span>
        </div>
      ),
    },
    {
      header: 'Avg Response SLA',
      key: 'avgResponse',
      render: (val) => <span style={{ fontSize: '0.85rem' }}>{val}</span>,
    },
    {
      header: 'Workload Status',
      key: 'status',
      render: (val) => (
        <span className={`ux4g-badge ${val === 'Optimal' ? 'ux4g-badge-low' : 'ux4g-badge-medium'}`}>
          {val}
        </span>
      ),
    },
  ];

  const filteredCases = districtCases.filter((c) => {
    const matchesSearch = 
      c.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
      c.beneficiaryName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRisk = riskFilter === 'ALL' || c.riskLevel.toUpperCase() === riskFilter;
    return matchesSearch && matchesRisk;
  });

  const caseColumns = [
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
      header: 'Priority & Risk',
      key: 'riskLevel',
      render: (_, row) => <RiskBadge level={row.riskLevel} size="sm" />,
    },
    {
      header: 'Distress Score / Trend',
      key: 'distressScore',
      render: (_, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{row.distressScore} / 100</div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: row.trend?.includes('Worsening') ? 'var(--ux4g-danger)' : 'var(--ux4g-success)' }}>
            {row.trend} ({row.baselineDeviation})
          </div>
        </div>
      ),
    },
    {
      header: 'Assigned Official',
      key: 'assignedOfficial',
      render: (val, row) => (
        <div style={{ fontSize: '0.825rem' }}>
          <div style={{ fontWeight: 600, color: 'var(--ux4g-violet-950)' }}>{row.primaryAssignee || val}</div>
          {row.backupAssignee && (
            <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>Backup: {row.backupAssignee}</div>
          )}
        </div>
      ),
    },
    {
      header: 'SLA Countdown',
      key: 'slaHoursRemaining',
      render: (val, row) => (
        <div>
          <span style={{ fontWeight: 700, color: val <= 2 ? 'var(--ux4g-danger)' : 'var(--ux4g-text-primary)' }}>
            {val}h remaining
          </span>
          <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>{row.slaStatus}</div>
        </div>
      ),
    },
    {
      header: 'Status',
      key: 'status',
      render: (val) => <StatusBadge status={val} size="sm" />,
    },
    {
      header: 'Action',
      key: 'actions',
      render: (_, row) => (
        <UX4GButton
          variant="outline"
          size="sm"
          icon={Eye}
          onClick={() => openCaseDetails(row)}
        >
          View Case Dossier
        </UX4GButton>
      ),
    },
  ];

  return (
    <DashboardShell
      title="District Operational Oversight"
      subtitle={`${districtName} District Magistrate & Atrocity Relief Administration • ${currentUser?.name}`}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: DISTRICT OPERATIONS (OVERVIEW & VISUALISATIONS)
          ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
          {/* 6 High-Level KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            {districtKPIs.map((kpi, idx) => (
              <UX4GCard key={idx} elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
                  {kpi.title}
                </span>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: kpi.color, margin: '4px 0' }}>
                  {kpi.value}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                  {kpi.sub}
                </div>
              </UX4GCard>
            ))}
          </div>

          {/* Analytics Visualisations Grid: Risk Donut + Trend Line */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <RiskDistributionChart
              data={analytics?.riskDistribution}
              title={`Algorithmic Risk Distribution (${districtName})`}
              subtitle="Real-time multi-modal triage classification across monitored cohort"
            />

            <LongitudinalTrendChart
              points={analytics?.trendHistory}
              title="District Aggregate Distress Trajectory"
              subtitle="30-day cohort average vs calibrated statutory tolerance baseline"
            />
          </div>

          {/* Analytics Visualisations Grid: Response SLA + Intervention Lifecycle */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <ResponseTimeChart
              slaTiers={analytics?.slaDistribution}
              overallCompliance={analytics?.slaComplianceRate || '98.6%'}
              avgResponseHours={`${analytics?.avgResponseTimeHours || 1.4} hrs`}
              title="Statutory SLA Adherence & Time-to-Action"
              subtitle="Compliance across Emergency, Urgent, Standard, and Routine SLA tiers"
            />

            <InterventionMetricsChart
              title="District Intervention Lifecycle Pipeline"
              subtitle="Current progress of relief and protection interventions"
            />
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: DISTRICT CASELOAD (SEARCH, FILTER & DOSSIERS)
          ========================================================================= */}
      {activeTab === 'cases' && (
        <UX4GCard elevation={2} liftOnHover={false} padding="24px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                District Active Monitored Cases ({filteredCases.length})
              </h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                Jurisdiction: {districtName} • Select any case file to review predictions, acoustic timeline, and statutory relief.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', width: '220px' }}>
                <Search size={15} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--ux4g-text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search case ID, name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="ux4g-focus-glow"
                  style={{
                    width: '100%',
                    padding: '7px 10px 7px 32px',
                    borderRadius: 'var(--radius-md)',
                    border: '1.5px solid var(--ux4g-border)',
                    fontSize: '0.82rem',
                  }}
                />
              </div>

              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="ux4g-focus-glow"
                style={{
                  padding: '7px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1.5px solid var(--ux4g-border)',
                  fontSize: '0.82rem',
                }}
              >
                <option value="ALL">All Risk Priorities</option>
                <option value="CRITICAL">Critical Priority</option>
                <option value="HIGH">High Priority</option>
                <option value="MEDIUM">Medium Priority</option>
                <option value="LOW">Low Priority</option>
              </select>
            </div>
          </div>

          <UX4GTable
            columns={caseColumns}
            data={filteredCases}
            emptyMessage="No district cases match your current search or risk priority filter."
            caption={`${districtName} Monitored Cases Queue`}
          />
        </UX4GCard>
      )}

      {/* =========================================================================
          TAB 3: ESCALATIONS & ALERTS (STATUTORY ACTION CONSOLE)
          ========================================================================= */}
      {activeTab === 'escalations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {escalationActionAlert && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success)', fontWeight: 600 }}>
              <CheckCircle2 size={18} />
              <span>{escalationActionAlert}</span>
            </div>
          )}

          {/* High Priority Critical Case Card */}
          <div style={{ backgroundColor: 'var(--ux4g-danger-bg)', border: '1.5px solid var(--ux4g-danger)', borderRadius: 'var(--radius-md)', padding: '22px', boxShadow: 'var(--elevation-1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <ShieldAlert size={26} color="var(--ux4g-danger)" style={{ marginTop: '2px' }} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="ux4g-badge ux4g-badge-high" style={{ background: 'var(--ux4g-danger)', color: '#FFF' }}>
                      CRITICAL STATUTORY ESCALATION
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ux4g-danger)', fontWeight: 700 }}>
                      SLA Window: 2.5 Hours Remaining
                    </span>
                  </div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--ux4g-danger)', marginTop: '4px' }}>
                    Case #AAROH-DEL-2026-001 • Meera Sharma
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-danger)', marginTop: '2px' }}>
                    Distress score spiked to 82 (+24 deviation). Acoustic pitch variation indicates acute psychological trauma following trial hearing.
                  </p>
                </div>
              </div>
            </div>

            {/* Statutory Action Bar */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', paddingTop: '12px', borderTop: '1px solid var(--ux4g-danger)' }}>
              <UX4GButton
                variant="danger"
                size="sm"
                icon={Scale}
                onClick={() => handleTriggerEscalation("Sanctioned immediate ₹1,50,000 interim financial relief under SC/ST PoA Rule 12(4). Forwarded to District Treasury.")}
              >
                Sanction Emergency Relief (PoA Rule 12(4))
              </UX4GButton>

              <UX4GButton
                variant="primary"
                size="sm"
                icon={Send}
                onClick={() => handleTriggerEscalation("Dispatched District Mobile Mental Health Crisis Unit to Meera Sharma's safe address.")}
              >
                Dispatch Mobile Mental Health Unit
              </UX4GButton>

              <UX4GButton
                variant="outline"
                size="sm"
                icon={Eye}
                onClick={() => {
                  const c = districtCases.find(item => item.id === 'AAROH-DEL-2026-001') || districtCases[0];
                  openCaseDetails(c);
                }}
              >
                Inspect Clinical Dossier
              </UX4GButton>
            </div>
          </div>

          {/* Escalation Alerts Matrix */}
          <UX4GCard elevation={1} padding="24px">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '14px' }}>
              Active District Escalation Roster ({districtName})
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '16px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RiskBadge level="High" size="sm" />
                    <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)' }}>
                      Case #AAROH-DEL-2026-003 • Rajesh Kumar
                    </strong>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                    Sustained fear indicators flagged in text check-in. Assigned to Dr. Sunita Rao.
                  </p>
                </div>
                <UX4GButton variant="outline" size="sm" onClick={() => handleTriggerEscalation("Superintendent of Police notified for preventive patrolling.")}>
                  Notify Police Cell
                </UX4GButton>
              </div>

              <div style={{ padding: '16px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RiskBadge level="High" size="sm" />
                    <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)' }}>
                      Case #AAROH-DEL-2026-004 • Geeta Devi
                    </strong>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                    Overdue legal aid coordination. DLSA assigned counsel Adv. Priya Malhotra.
                  </p>
                </div>
                <UX4GButton variant="outline" size="sm" onClick={() => handleTriggerEscalation("Expedited DLSA retainer hearing schedule.")}>
                  Expedite Legal Aid
                </UX4GButton>
              </div>
            </div>
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 4: COUNSELLOR WORKLOAD (CAPACITY MANAGEMENT)
          ========================================================================= */}
      {activeTab === 'workload' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {rebalanceAlert && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success)', fontWeight: 600 }}>
              <CheckCircle2 size={18} />
              <span>Caseload successfully rebalanced! 2 cases transferred from Shri Vikram Malhotra (95% → 85%) to Dr. Priya Nambiar (60% → 70%).</span>
            </div>
          )}

          <UX4GCard elevation={2} liftOnHover={false} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '18px' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Counsellor Workload &amp; Capacity Allocation
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                  Jurisdiction: {districtName} Atrocity Monitoring Cell • Dynamic capacity threshold: 20 active cases per clinician.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <UX4GButton variant="primary" size="sm" icon={RefreshCw} onClick={handleRebalanceWorkload}>
                  Rebalance Caseload
                </UX4GButton>
              </div>
            </div>

            <UX4GTable columns={counsellorColumns} data={counsellors} />
          </UX4GCard>

          {/* Capacity Insights Box */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
            <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Average Response SLA</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>1.6 Hours</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--ux4g-success)', fontWeight: 600 }}>60% faster than 4.0 hr statutory limit</p>
            </div>

            <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Total District Clinicians</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-700)', margin: '4px 0' }}>4 Certified</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>Tele-MANAS &amp; Social Justice Retainers</p>
            </div>

            <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Overall District Saturation</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-success)', margin: '4px 0' }}>78.7%</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>Healthy operational reserve margin</p>
            </div>
          </div>
        </div>
      )}

      {/* Complete End-to-End Case Dossier Modal */}
      {selectedCase && (
        <CaseDetailModal
          isOpen={caseModalOpen}
          onClose={() => setCaseModalOpen(false)}
          caseData={selectedCase}
          onCaseUpdated={handleCaseUpdated}
        />
      )}
    </DashboardShell>
  );
};
