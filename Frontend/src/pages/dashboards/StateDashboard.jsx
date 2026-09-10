import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  MapPin, 
  ChevronRight, 
  ArrowLeft, 
  Eye, 
  ShieldAlert, 
  BarChart2, 
  Clock, 
  CheckCircle2, 
  FileText, 
  Download, 
  Share2,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';
import { UX4GButton } from '../../components/common/UX4GButton';
import { RiskBadge, StatusBadge } from '../../components/common/UX4GBadge';
import { 
  DistrictComparisonChart, 
  LongitudinalTrendChart, 
  OutcomeDistributionChart,
  ResponseTimeChart
} from '../../components/analytics';
import { CaseDetailModal } from '../../components/counsellor/CaseDetailModal';
import { caseService } from '../../services/caseService';
import { analyticsService } from '../../services/analyticsService';

export const StateDashboard = () => {
  const { currentUser } = useAuth();
  const stateName = currentUser?.state || 'Delhi NCT';

  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };

  const [stateAnalytics, setStateAnalytics] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [districtCases, setDistrictCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseModalOpen, setCaseModalOpen] = useState(false);
  const [reportDownloadAlert, setReportDownloadAlert] = useState('');

  useEffect(() => {
    loadStateData();
  }, [stateName]);

  const loadStateData = async () => {
    const data = await analyticsService.getStateAnalytics(stateName);
    setStateAnalytics(data);
  };

  const handleSelectDistrict = async (district) => {
    setSelectedDistrict(district);
    const cases = await caseService.getCasesByDistrict(district);
    setDistrictCases(cases);
  };

  const handleResetDistrict = () => {
    setSelectedDistrict(null);
    setDistrictCases([]);
  };

  const handleCaseUpdated = (updatedCase) => {
    setDistrictCases(prev => prev.map(c => c.id === updatedCase.id ? updatedCase : c));
    setSelectedCase(updatedCase);
  };

  const openCaseDetails = (c) => {
    setSelectedCase(c);
    setCaseModalOpen(true);
  };

  const handleDownloadReport = (reportName) => {
    setReportDownloadAlert(`Generated and downloaded "${reportName}" for ${stateName}.`);
    setTimeout(() => setReportDownloadAlert(''), 4000);
  };

  const districtComparisonColumns = [
    {
      header: 'District Name',
      key: 'district',
      render: (val) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
          <MapPin size={15} color="var(--ux4g-violet-700)" />
          <span>{val}</span>
        </div>
      ),
    },
    {
      header: 'Total Monitored',
      key: 'totalCases',
      render: (val) => <span style={{ fontWeight: 600 }}>{val} cases</span>,
    },
    {
      header: 'High / Critical Risk',
      key: 'highRisk',
      render: (val) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, color: 'var(--ux4g-danger)' }}>{val}</span>
          <RiskBadge level={val > 8 ? 'High' : 'Medium'} size="sm" />
        </div>
      ),
    },
    {
      header: 'Pending Interventions',
      key: 'pendingInterventions',
      render: (val) => <span style={{ fontWeight: 500 }}>{val}</span>,
    },
    {
      header: 'Avg Response Time',
      key: 'avgResponse',
      render: (val) => <span>{val}</span>,
    },
    {
      header: 'SLA Adherence',
      key: 'compliance',
      render: (val) => (
        <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.75rem' }}>
          {val}
        </span>
      ),
    },
    {
      header: 'Action',
      key: 'actions',
      render: (_, row) => (
        <UX4GButton
          variant={selectedDistrict === row.district ? 'primary' : 'outline'}
          size="sm"
          icon={ChevronRight}
          onClick={() => handleSelectDistrict(row.district)}
        >
          {selectedDistrict === row.district ? 'Selected' : 'Drill Down'}
        </UX4GButton>
      ),
    },
  ];

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
      header: 'Risk Priority',
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
      header: 'Primary Counsellor',
      key: 'primaryAssignee',
      render: (val) => <span style={{ fontSize: '0.85rem' }}>{val || 'Dr. Rajesh Verma'}</span>,
    },
    {
      header: 'SLA Remaining',
      key: 'slaHoursRemaining',
      render: (val, row) => (
        <div>
          <span style={{ fontWeight: 700, color: val <= 2 ? 'var(--ux4g-danger)' : 'var(--ux4g-text-primary)' }}>
            {val}h
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
          View Dossier
        </UX4GButton>
      ),
    },
  ];

  const stateReports = [
    {
      id: 'REP-DL-001',
      title: 'Monthly Atrocity Distress & Intervention Summary',
      period: 'August 2026',
      size: '2.4 MB PDF',
      desc: 'Complete cross-district analysis of distress trajectories, clinical counselor engagements, and SLA adherence across 11 districts.'
    },
    {
      id: 'REP-DL-002',
      title: 'SC/ST (PoA) Statutory Compensation Disbursement Audit',
      period: 'Q2 2026',
      size: '1.8 MB PDF',
      desc: 'Audit trail of Annexure-I interim relief disbursements under Rule 12(4) with DBT Aadhaar verification.'
    },
    {
      id: 'REP-DL-003',
      title: 'District Capacity & Counsellor Workload Distribution',
      period: 'Current Cycle',
      size: '1.1 MB CSV',
      desc: 'Granular clinician-to-beneficiary ratios, workload saturation meters, and rebalancing logs.'
    },
    {
      id: 'REP-DL-004',
      title: 'Algorithmic Escalation Validation & False Positive Review',
      period: 'Last 90 Days',
      size: '3.2 MB PDF',
      desc: 'Independent evaluation of multimodal acoustic/NLP distress predictions verified against human clinician judgments.'
    },
  ];

  return (
    <DashboardShell
      title="State-Wide Atrocity Monitoring Oversight"
      subtitle={`${stateName} Directorate of Social Justice & Empowerment • ${currentUser?.name}`}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: STATE-WIDE DASHBOARD (OVERVIEW)
          ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
          {/* 4 State KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
                Total State Monitored
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>
                {stateAnalytics?.totalMonitored || '506'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                Across {stateAnalytics?.districtCount || 11} State Districts
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-danger)', textTransform: 'uppercase' }}>
                High-Risk Cohort (State)
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-danger)', margin: '4px 0' }}>
                {stateAnalytics?.highRiskCount || '33'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-danger-text)' }}>
                Mandatory DM intervention window
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-success)', textTransform: 'uppercase' }}>
                Overall State Compliance
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-success)', margin: '4px 0' }}>
                {stateAnalytics?.slaCompliance || '98.4%'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                All 11 districts within SLA target
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase' }}>
                Active Certified Counsellors
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-700)', margin: '4px 0' }}>
                48 Clinicians
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                Tele-MANAS &amp; Social Welfare Retainers
              </div>
            </UX4GCard>
          </div>

          {/* Visualisations Grid: District Comparison + Trend Line */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <DistrictComparisonChart
              data={stateAnalytics?.districtComparison}
              title={`District-Level Caseload & SLA Compliance (${stateName})`}
              subtitle="Comparison across all reporting districts"
              onSelectDistrict={handleSelectDistrict}
              activeDistrict={selectedDistrict}
            />

            <LongitudinalTrendChart
              points={stateAnalytics?.stateTrend}
              title="State Longitudinal Distress Average"
              subtitle="60-day historical cohort distress trend vs tolerance baseline"
            />
          </div>

          {/* Outcome Distribution Across State */}
          <OutcomeDistributionChart
            data={stateAnalytics?.outcomes}
            title="State Statutory Intervention Outcomes"
            subtitle="Distribution of resolved, counselled, and referred atrocity interventions"
          />
        </div>
      )}

      {/* =========================================================================
          TAB 2: DISTRICT COMPARISON (STATE -> DISTRICT -> CASE DRILL-DOWN)
          ========================================================================= */}
      {activeTab === 'districts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Breadcrumb drill down header */}
          {selectedDistrict && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 18px', backgroundColor: 'var(--ux4g-violet-50)', border: '1px solid var(--ux4g-violet-300)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
                <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600, cursor: 'pointer' }} onClick={handleResetDistrict}>
                  {stateName}
                </span>
                <ChevronRight size={15} color="var(--ux4g-text-muted)" />
                <span style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700 }}>
                  {selectedDistrict} District Caseload
                </span>
              </div>
              <UX4GButton variant="outline" size="sm" icon={ArrowLeft} onClick={handleResetDistrict}>
                Back to All Districts
              </UX4GButton>
            </div>
          )}

          {selectedDistrict ? (
            <UX4GCard elevation={2} liftOnHover={false} padding="24px">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    {selectedDistrict} District Case Roster
                  </h3>
                  <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-muted)' }}>
                    Drill-down view: Select any case dossier to inspect distress predictions and clinical intervention logs.
                  </p>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">
                  {districtCases.length} Active Cases
                </span>
              </div>

              <UX4GTable
                columns={caseColumns}
                data={districtCases}
                emptyMessage={`No active cases found for ${selectedDistrict}.`}
                caption={`${selectedDistrict} Active Caseload`}
              />
            </UX4GCard>
          ) : (
            <UX4GCard elevation={2} liftOnHover={false} padding="24px">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    {stateName} District Comparative Matrix
                  </h3>
                  <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                    Select "Drill Down" on any district to inspect active cases and assigned clinical counsellors.
                  </p>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">11 Reporting Districts</span>
              </div>

              <UX4GTable
                columns={districtComparisonColumns}
                data={stateAnalytics?.districtComparison || []}
              />
            </UX4GCard>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: SLA PERFORMANCE (RESPONSE TIMES & AUDIT)
          ========================================================================= */}
      {activeTab === 'performance' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              State SLA Compliance &amp; Time-to-Intervention Audit
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
              Statutory mandate under SC/ST PoA guidelines: Emergency distress spikes must receive certified human clinician intervention in &lt; 4 hours.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <ResponseTimeChart
              slaTiers={stateAnalytics?.slaDistribution}
              overallCompliance={stateAnalytics?.slaCompliance || '98.4%'}
              avgResponseHours="1.8 hrs"
              title="State Response SLA Distribution"
              subtitle="Breakdown across Emergency, Urgent, Standard, and Routine SLA tiers"
            />

            <UX4GCard elevation={1} padding="24px">
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '14px' }}>
                District SLA Compliance Rankings
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {(stateAnalytics?.districtComparison || []).map((d) => (
                  <div key={d.district} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <MapPin size={14} color="var(--ux4g-violet-700)" />
                      <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>{d.district}</strong>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>Avg: {d.avgResponse}</span>
                      <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.75rem' }}>{d.compliance}</span>
                    </div>
                  </div>
                ))}
              </div>
            </UX4GCard>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: STATE REPORTS (PDF/CSV COMPILATION & AUDIT EXPORTS)
          ========================================================================= */}
      {activeTab === 'reports' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {reportDownloadAlert && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success)', fontWeight: 600 }}>
              <CheckCircle2 size={18} />
              <span>{reportDownloadAlert}</span>
            </div>
          )}

          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Official State Statutory Reports Repository
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
              As specified in Section 29 of AAROH Plan: Access authorized case summaries, district performance digests, and algorithmic validation reports.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            {stateReports.map((rep) => (
              <UX4GCard key={rep.id} elevation={1} padding="22px">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--ux4g-violet-700)', fontWeight: 700 }}>
                    {rep.id}
                  </span>
                  <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.7rem' }}>
                    {rep.period}
                  </span>
                </div>

                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  {rep.title}
                </h4>

                <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
                  {rep.desc}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--ux4g-border-subtle)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>{rep.size}</span>
                  <UX4GButton
                    variant="outline"
                    size="sm"
                    icon={Download}
                    onClick={() => handleDownloadReport(rep.title)}
                  >
                    Download Official Report
                  </UX4GButton>
                </div>
              </UX4GCard>
            ))}
          </div>
        </div>
      )}

      {/* Case Detail Modal for Drill Down */}
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
