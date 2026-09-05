import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';

export const DistrictDashboard = () => {
  const { currentUser } = useAuth();

  const districtKPIs = [
    { title: 'Total Monitored Cases', value: '142', sub: 'South Delhi Jurisdiction', color: 'var(--ux4g-violet-700)' },
    { title: 'High & Critical Risk', value: '11', sub: 'Immediate clinical review', color: 'var(--ux4g-danger)' },
    { title: 'Worsening Trends', value: '7', sub: 'Algorithmic escalation alerts', color: 'var(--ux4g-warning)' },
    { title: 'Pending Interventions', value: '5', sub: 'Within 24-hr SLA window', color: 'var(--ux4g-info)' },
    { title: 'Overdue Interventions', value: '0', sub: '100% SLA compliance', color: 'var(--ux4g-success)' },
    { title: 'Completed Interventions', value: '126', sub: 'Successfully closed/stabilized', color: 'var(--ux4g-violet-950)' },
  ];

  const counsellors = [
    { name: 'Dr. Rajesh Varma', specialization: 'Trauma & PTSD', activeCaseload: 18, capacity: '90%', avgResponse: '1.4 hrs', status: 'Optimal' },
    { name: 'Dr. Sunita Rao', specialization: 'Adolescent & Child Atrocity Relief', activeCaseload: 14, capacity: '70%', avgResponse: '1.8 hrs', status: 'Optimal' },
    { name: 'Shri Vikram Malhotra', specialization: 'Rehabilitation & Legal Aid Liaison', activeCaseload: 19, capacity: '95%', avgResponse: '2.1 hrs', status: 'Near Limit' },
    { name: 'Dr. Priya Nambiar', specialization: 'Crisis De-escalation', activeCaseload: 12, capacity: '60%', avgResponse: '1.1 hrs', status: 'Optimal' },
  ];

  const columns = [
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

  return (
    <DashboardShell
      title="District Operational Oversight"
      subtitle={`South Delhi District Magistrate & Atrocity Relief Administration • ${currentUser?.name}`}
    >
      {/* 6 High-Level KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '28px' }}>
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

      {/* District Counsellor Workload Allocation */}
      <UX4GCard elevation={2} liftOnHover={false} padding="24px">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Counsellor Workload & Capacity Allocation
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
              Jurisdiction: South Delhi District Atrocity Monitoring Cell
            </p>
          </div>
          <span className="ux4g-badge ux4g-badge-primary">4 Active Officials</span>
        </div>

        <UX4GTable columns={columns} data={counsellors} />
      </UX4GCard>
    </DashboardShell>
  );
};
