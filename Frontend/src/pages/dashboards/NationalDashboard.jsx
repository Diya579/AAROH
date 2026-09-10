import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Globe, 
  MapPin, 
  ChevronRight, 
  ArrowLeft, 
  Eye, 
  ShieldCheck, 
  Award,
  TrendingUp,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  BarChart3
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';
import { UX4GButton } from '../../components/common/UX4GButton';
import { RiskBadge, StatusBadge } from '../../components/common/UX4GBadge';
import { 
  RiskDistributionChart, 
  DistrictComparisonChart, 
  OutcomeDistributionChart,
  LongitudinalTrendChart,
  ResponseTimeChart
} from '../../components/analytics';
import { CaseDetailModal } from '../../components/counsellor/CaseDetailModal';
import { caseService } from '../../services/caseService';
import { analyticsService } from '../../services/analyticsService';

export const NationalDashboard = () => {
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };

  const [nationalAnalytics, setNationalAnalytics] = useState(null);
  const [selectedState, setSelectedState] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [stateData, setStateData] = useState(null);
  const [activeCases, setActiveCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseModalOpen, setCaseModalOpen] = useState(false);

  useEffect(() => {
    loadNationalData();
  }, []);

  const loadNationalData = async () => {
    const data = await analyticsService.getNationalAnalytics();
    setNationalAnalytics(data);
  };

  const handleSelectState = async (stateName) => {
    setSelectedState(stateName);
    setSelectedDistrict(null);
    const sData = await analyticsService.getStateAnalytics(stateName);
    setStateData(sData);
    const cases = await caseService.getCasesByState(stateName);
    setActiveCases(cases);
  };

  const handleSelectDistrict = async (districtName) => {
    setSelectedDistrict(districtName);
    const cases = await caseService.getCasesByDistrict(districtName);
    setActiveCases(cases);
  };

  const handleReset = () => {
    setSelectedState(null);
    setSelectedDistrict(null);
    setStateData(null);
    setActiveCases([]);
  };

  const handleCaseUpdated = (updatedCase) => {
    setActiveCases(prev => prev.map(c => c.id === updatedCase.id ? updatedCase : c));
    setSelectedCase(updatedCase);
  };

  const openCaseDetails = (c) => {
    setSelectedCase(c);
    setCaseModalOpen(true);
  };

  const stateColumns = [
    {
      header: 'State / Union Territory',
      key: 'state',
      render: (val) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
          <Globe size={15} color="var(--ux4g-violet-700)" />
          <span>{val}</span>
        </div>
      ),
    },
    {
      header: 'Active Caseload',
      key: 'monitored',
      render: (val) => <span style={{ fontWeight: 600 }}>{val.toLocaleString()}</span>,
    },
    {
      header: 'High Risk Proportion',
      key: 'highRiskRate',
      render: (val) => <span style={{ fontWeight: 600, color: '#DC2626' }}>{val}</span>,
    },
    {
      header: 'National Response SLA',
      key: 'avgResponse',
      render: (val) => <span>{val}</span>,
    },
    {
      header: 'Overall Adherence',
      key: 'compliance',
      render: (val) => <span className="ux4g-badge ux4g-badge-low">{val}</span>,
    },
    {
      header: 'District Coverage',
      key: 'coverage',
      render: (val) => <span style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)' }}>{val}</span>,
    },
    {
      header: 'Action',
      key: 'actions',
      render: (_, row) => (
        <UX4GButton
          variant={selectedState === row.state ? 'primary' : 'outline'}
          size="sm"
          icon={ChevronRight}
          onClick={() => handleSelectState(row.state)}
        >
          {selectedState === row.state ? 'Selected' : 'Drill Down'}
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
      header: 'District',
      key: 'district',
      render: (val) => <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{val}</span>,
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
      header: 'SLA Window',
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

  const coverageZones = [
    { zone: 'Northern Zone', states: 'Delhi, Punjab, Haryana, Rajasthan, HP', districtsOnboarded: '86 / 94', coveragePct: '91.5%', status: 'Phase 1 Complete' },
    { zone: 'Western Zone', states: 'Maharashtra, Gujarat, Goa', districtsOnboarded: '62 / 68', coveragePct: '91.2%', status: 'Phase 1 Complete' },
    { zone: 'Southern Zone', states: 'Tamil Nadu, Karnataka, Telangana, AP, Kerala', districtsOnboarded: '118 / 132', coveragePct: '89.4%', status: 'Phase 2 Active' },
    { zone: 'Central Zone', states: 'Uttar Pradesh, Madhya Pradesh, Chhattisgarh', districtsOnboarded: '142 / 164', coveragePct: '86.5%', status: 'Phase 2 Active' },
    { zone: 'Eastern Zone', states: 'Bihar, West Bengal, Odisha, Jharkhand', districtsOnboarded: '94 / 118', coveragePct: '79.6%', status: 'Phase 2 Active' },
    { zone: 'North-Eastern Zone', states: 'Assam, Meghalaya, Tripura, Manipur, etc.', districtsOnboarded: '48 / 64', coveragePct: '75.0%', status: 'Phase 3 Expanding' },
  ];

  return (
    <DashboardShell
      title="National Directorate Overview"
      subtitle={`${currentUser?.ministry || 'Ministry of Social Justice & Empowerment'} • ${currentUser?.name} • All-India Coverage`}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: NATIONAL DIRECTORATE (OVERVIEW & HIGH-LEVEL KPIS)
          ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
          {/* 4 National KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
                All-India Monitored Beneficiaries
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>
                {nationalAnalytics?.totalMonitored.toLocaleString() || '7,656'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                Across 28 States &amp; 8 UTs
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase' }}>
                Certified Care Providers
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-700)', margin: '4px 0' }}>
                {nationalAnalytics?.certifiedProviders || 842}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                Clinical psychologists &amp; counsellors
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-danger)', textTransform: 'uppercase' }}>
                High-Risk Cases (National)
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-danger)', margin: '4px 0' }}>
                {nationalAnalytics?.totalHighRisk || 476}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-danger-text)' }}>
                Statutory escalated priority
              </div>
            </UX4GCard>

            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="18px">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ux4g-success)', textTransform: 'uppercase' }}>
                National SLA Compliance
              </span>
              <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-success)', margin: '4px 0' }}>
                {nationalAnalytics?.nationalCompliance || '97.5%'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)' }}>
                Within designated statutory windows
              </div>
            </UX4GCard>
          </div>

          {/* Visualisations Grid: National Risk Donut + State Comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <RiskDistributionChart
              data={nationalAnalytics?.nationalRiskDistribution}
              title="National Risk Distribution"
              subtitle="All-India aggregate triage stratification across state jurisdictions"
            />

            <DistrictComparisonChart
              data={nationalAnalytics?.stateComparison}
              title="State-Level Caseload & SLA Compliance"
              subtitle="Comparative distribution across reporting States & UTs"
              onSelectDistrict={(s) => {
                handleSelectState(s);
                handleTabChange('states');
              }}
              activeDistrict={selectedState}
            />
          </div>

          {/* Quick States Overview Table */}
          <UX4GCard elevation={2} liftOnHover={false} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  State Performance &amp; Jurisdiction Adherence Summary
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                  Aggregated compliance scores and active caseload numbers across high-volume states.
                </p>
              </div>
              <UX4GButton variant="outline" size="sm" onClick={() => handleTabChange('states')}>
                Inspect Drill-Down
              </UX4GButton>
            </div>

            <UX4GTable columns={stateColumns} data={nationalAnalytics?.stateComparison || []} />
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 2: STATE COMPARISON (3-TIER DRILL-DOWN: NATIONAL -> STATE -> DISTRICT -> CASE)
          ========================================================================= */}
      {activeTab === 'states' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* 3-Tier Breadcrumb Navigation */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 18px', backgroundColor: 'var(--ux4g-violet-100)', borderRadius: 'var(--radius-md)', border: '1.5px solid #3A2312', boxShadow: '2px 2px 0px #3A2312' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
              <span style={{ fontWeight: selectedState ? 500 : 700, color: 'var(--ux4g-violet-950)', cursor: selectedState ? 'pointer' : 'default' }} onClick={handleReset}>
                🇮🇳 All-India Directorate
              </span>
              {selectedState && (
                <>
                  <ChevronRight size={14} color="var(--ux4g-text-muted)" />
                  <span
                    style={{ fontWeight: selectedDistrict ? 500 : 700, color: 'var(--ux4g-violet-700)', cursor: selectedDistrict ? 'pointer' : 'default' }}
                    onClick={() => setSelectedDistrict(null)}
                  >
                    {selectedState}
                  </span>
                </>
              )}
              {selectedDistrict && (
                <>
                  <ChevronRight size={14} color="var(--ux4g-text-muted)" />
                  <span style={{ fontWeight: 700, color: 'var(--ux4g-violet-900)' }}>
                    {selectedDistrict} District
                  </span>
                </>
              )}
            </div>
            {selectedState && (
              <UX4GButton
                variant="outline"
                size="sm"
                icon={ArrowLeft}
                onClick={handleReset}
              >
                Reset to All-India View
              </UX4GButton>
            )}
          </div>

          {/* Drill-down Table View */}
          {selectedState ? (
            <UX4GCard elevation={2} liftOnHover={false} padding="24px">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Globe size={20} color="var(--ux4g-violet-700)" />
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                      {selectedState} State Caseload Queue {selectedDistrict ? `• ${selectedDistrict} District` : ''}
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                    National-to-State-to-District Drill Down: Select any case dossier to review predictions and assign relief.
                  </p>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">
                  {activeCases.length} Monitored Cases
                </span>
              </div>

              <UX4GTable
                columns={caseColumns}
                data={activeCases}
                emptyMessage="No monitored cases recorded for this State/UT."
                caption={`Active monitored cases for ${selectedState}`}
              />
            </UX4GCard>
          ) : (
            <UX4GCard elevation={2} liftOnHover={false} padding="24px">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    All-India State Performance &amp; Jurisdiction Adherence Matrix
                  </h3>
                  <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                    Select "Drill Down" on any State to inspect districts, active cases, and intervention statuses.
                  </p>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">5 High-Volume Reporting States</span>
              </div>

              <UX4GTable columns={stateColumns} data={nationalAnalytics?.stateComparison || []} />
            </UX4GCard>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 3: AGGREGATED TRENDS (LONGITUDINAL DISTRESS & OUTCOMES)
          ========================================================================= */}
      {activeTab === 'trends' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ backgroundColor: '#FFFFFF', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              All-India Aggregated Distress Trajectory &amp; Outcome Statistics
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
              Longitudinal analysis of multimodal predictions, statutory escalation early-warning lead times, and post-intervention recovery rates.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            <LongitudinalTrendChart
              points={[
                { date: 'Jan 2026', avgDistress: 68, highRiskCount: 520, baseline: 50 },
                { date: 'Mar 2026', avgDistress: 64, highRiskCount: 495, baseline: 50 },
                { date: 'May 2026', avgDistress: 59, highRiskCount: 480, baseline: 50 },
                { date: 'Jul 2026', avgDistress: 56, highRiskCount: 482, baseline: 50 },
                { date: 'Sep 2026', avgDistress: 53, highRiskCount: 476, baseline: 50 },
              ]}
              title="National 9-Month Average Distress De-escalation"
              subtitle="Downward trajectory indicates efficacy of multimodal early-intervention"
            />

            <OutcomeDistributionChart
              data={{
                counsellingCount: 4746,
                legalAidCount: 1378,
                financialReliefCount: 918,
                protectionCount: 614,
              }}
              title="National Statutory Intervention Modality Breakdown"
              subtitle="7,656 total interventions categorized by multi-agency action"
            />
          </div>

          <ResponseTimeChart
            slaTiers={[
              { tier: 'Emergency Tier (<2 hrs)', total: 476, compliant: 468, pct: '98.3%' },
              { tier: 'Urgent Tier (<4 hrs)', total: 1240, compliant: 1215, pct: '97.9%' },
              { tier: 'Standard Tier (<24 hrs)', total: 3820, compliant: 3740, pct: '97.9%' },
              { tier: 'Routine Review (<48 hrs)', total: 2120, compliant: 2045, pct: '96.5%' },
            ]}
            overallCompliance="97.5%"
            avgResponseHours="1.9 hrs"
            title="All-India Response SLA Adherence Matrix"
            subtitle="Real-time statutory time-to-action tracking across 28 States & 8 UTs"
          />
        </div>
      )}

      {/* =========================================================================
          TAB 4: MONITORING COVERAGE (GEOGRAPHIC EXPANSION & CLINICIAN CAPACITY)
          ========================================================================= */}
      {activeTab === 'coverage' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          <div style={{ backgroundColor: '#FFFFFF', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Geographic Expansion &amp; Tele-MANAS Regional Coverage
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
              Phase-wise deployment of AAROH AI-powered psychological monitoring system across Indian districts and specialized SC/ST special courts.
            </p>
          </div>

          {/* 3 Rollout Milestone Boxes */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1.5px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '18px', boxShadow: '2px 2px 0px #3A2312' }}>
              <span className="ux4g-badge ux4g-badge-low" style={{ marginBottom: '8px' }}>Phase 1 Complete</span>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-success-text)' }}>142 Districts</div>
              <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>100% active monitoring • Delhi, Maharashtra, Karnataka</p>
            </div>

            <div style={{ backgroundColor: 'var(--ux4g-violet-100)', border: '1.5px solid var(--ux4g-violet-300)', borderRadius: 'var(--radius-md)', padding: '18px', boxShadow: '2px 2px 0px #3A2312' }}>
              <span className="ux4g-badge ux4g-badge-primary" style={{ marginBottom: '8px' }}>Phase 2 (Active)</span>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>210 Districts</div>
              <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>84% clinical onboarding • UP, Tamil Nadu, MP, Gujarat</p>
            </div>

            <div style={{ backgroundColor: 'var(--ux4g-saffron-50)', border: '1.5px solid var(--ux4g-saffron-400)', borderRadius: 'var(--radius-md)', padding: '18px', boxShadow: '2px 2px 0px #3A2312' }}>
              <span className="ux4g-badge ux4g-badge-medium" style={{ marginBottom: '8px' }}>Phase 3 (Expanding)</span>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>360 Districts</div>
              <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-violet-700)', marginTop: '4px' }}>Target: Complete Pan-India saturation by 2027</p>
            </div>
          </div>

          {/* Regional Zonal Matrix */}
          <UX4GCard elevation={1} padding="24px">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '16px' }}>
              Regional Zonal Saturation &amp; Clinician Capacity Status
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {coverageZones.map((z) => (
                <div key={z.zone} style={{ padding: '14px 18px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <MapPin size={16} color="var(--ux4g-violet-700)" />
                      <strong style={{ fontSize: '0.95rem', color: 'var(--ux4g-violet-950)' }}>{z.zone}</strong>
                      <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.72rem' }}>{z.status}</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', marginTop: '3px' }}>
                      {z.states}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{z.districtsOnboarded} Districts</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>Coverage: {z.coveragePct}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </UX4GCard>
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
