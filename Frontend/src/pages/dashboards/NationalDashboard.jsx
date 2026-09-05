import React from 'react';
import { Globe } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';

export const NationalDashboard = () => {
  const { currentUser } = useAuth();

  const stateComparison = [
    { state: 'Delhi NCT', monitored: 506, highRiskRate: '6.5%', avgResponse: '1.6 hrs', compliance: '98.4%', coverage: '100% (11/11 Districts)' },
    { state: 'Maharashtra', monitored: 1840, highRiskRate: '5.8%', avgResponse: '2.1 hrs', compliance: '97.2%', coverage: '94% (34/36 Districts)' },
    { state: 'Uttar Pradesh', monitored: 3210, highRiskRate: '7.2%', avgResponse: '2.4 hrs', compliance: '95.1%', coverage: '89% (67/75 Districts)' },
    { state: 'Tamil Nadu', monitored: 1120, highRiskRate: '4.9%', avgResponse: '1.5 hrs', compliance: '99.0%', coverage: '97% (37/38 Districts)' },
    { state: 'Karnataka', monitored: 980, highRiskRate: '5.2%', avgResponse: '1.8 hrs', compliance: '97.8%', coverage: '93% (29/31 Districts)' },
  ];

  const columns = [
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
      render: (val) => <span>{val}</span>,
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
  ];

  return (
    <DashboardShell
      title="National Directorate Overview"
      subtitle={`${currentUser?.ministry} • ${currentUser?.name} • All-India Coverage`}
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '28px' }}>
        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
            All-India Monitored Beneficiaries
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>
            7,656
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)' }}>
            Covering 28 States & 8 UTs
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase' }}>
            Certified Care Providers
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-violet-700)', margin: '4px 0' }}>
            842
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)' }}>
            Clinical psychologists & counsellors
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-success-text)', textTransform: 'uppercase' }}>
            National SLA Compliance
          </span>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--ux4g-success-text)', margin: '4px 0' }}>
            97.8%
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)' }}>
            Within designated statutory windows
          </div>
        </UX4GCard>
      </div>

      <UX4GCard elevation={2} liftOnHover={false} padding="24px">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              State & Union Territory Aggregated Comparison
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
              Hierarchy: National → State → District → Case
            </p>
          </div>
          <span className="ux4g-badge ux4g-badge-primary">National Directive</span>
        </div>

        <UX4GTable columns={columns} data={stateComparison} />
      </UX4GCard>
    </DashboardShell>
  );
};
