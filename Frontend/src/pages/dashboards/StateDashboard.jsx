import React from 'react';
import { MapPin } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';
import { RiskBadge } from '../../components/common/UX4GBadge';

export const StateDashboard = () => {
  const { currentUser } = useAuth();

  const districtComparison = [
    { district: 'South Delhi', totalCases: 142, highRisk: 11, pendingInterventions: 5, avgResponse: '1.6 hrs', compliance: '98.4%' },
    { district: 'North Delhi', totalCases: 98, highRisk: 6, pendingInterventions: 2, avgResponse: '1.9 hrs', compliance: '96.8%' },
    { district: 'West Delhi', totalCases: 115, highRisk: 8, pendingInterventions: 3, avgResponse: '1.4 hrs', compliance: '99.1%' },
    { district: 'East Delhi', totalCases: 87, highRisk: 5, pendingInterventions: 1, avgResponse: '2.0 hrs', compliance: '95.2%' },
    { district: 'Central Delhi', totalCases: 64, highRisk: 3, pendingInterventions: 0, avgResponse: '1.2 hrs', compliance: '100%' },
  ];

  const columns = [
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
  ];

  return (
    <DashboardShell
      title="State Directorate Overview"
      subtitle={`State Welfare Department • ${currentUser?.state} • ${currentUser?.name}`}
    >
      {/* State-Level Aggregated KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '28px' }}>
        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
            State-Wide Active Beneficiaries
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>
            506
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)' }}>
            Across 11 administrative districts
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-danger)', textTransform: 'uppercase' }}>
            High-Risk Cases (State Total)
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-danger)', margin: '4px 0' }}>
            33
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-danger-text)' }}>
            6.5% of total caseload
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-success-text)', textTransform: 'uppercase' }}>
            Average State Triage SLA
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-success-text)', margin: '4px 0' }}>
            1.6 hrs
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)' }}>
            Target threshold: &lt; 4.0 hrs
          </div>
        </UX4GCard>
      </div>

      {/* District Comparison Table */}
      <UX4GCard elevation={2} liftOnHover={false} padding="24px">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Inter-District Comparison & SLA Performance
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
              Drill down from State → District → Case under authorized supervision
            </p>
          </div>
          <span className="ux4g-badge ux4g-badge-primary">State View</span>
        </div>

        <UX4GTable columns={columns} data={districtComparison} />
      </UX4GCard>
    </DashboardShell>
  );
};
