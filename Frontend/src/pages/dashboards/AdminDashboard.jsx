import React from 'react';
import { ShieldCheck, Server, Lock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';

export const AdminDashboard = () => {
  const { currentUser } = useAuth();

  const auditEvents = [
    { timestamp: '2026-09-05 13:42:10', event: 'Role Session Initialized', actor: 'Meera Sharma (VICTIM)', ip: '10.24.11.8', status: 'Success' },
    { timestamp: '2026-09-05 13:15:00', event: 'Caseload Triage Escalated', actor: 'Dr. Rajesh Varma (COUNSELLOR)', ip: '10.42.0.12', status: 'Logged' },
    { timestamp: '2026-09-05 12:48:32', event: 'Intervention SLA Acknowledged', actor: 'Ananya Sen, IAS (DISTRICT)', ip: '10.88.4.19', status: 'Logged' },
    { timestamp: '2026-09-05 11:20:04', event: 'Audit Log Integrity Check', actor: 'SYS-ADM-0001 (ADMIN)', ip: '127.0.0.1', status: 'Verified' },
  ];

  const columns = [
    { header: 'Timestamp (IST)', key: 'timestamp', render: (v) => <span style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{v}</span> },
    { header: 'Audit Event', key: 'event', render: (v) => <strong style={{ color: 'var(--ux4g-violet-950)' }}>{v}</strong> },
    { header: 'Authorized Actor', key: 'actor', render: (v) => <span style={{ fontSize: '0.85rem' }}>{v}</span> },
    { header: 'Internal IP', key: 'ip', render: (v) => <span style={{ color: 'var(--ux4g-text-muted)', fontSize: '0.8rem' }}>{v}</span> },
    {
      header: 'Integrity Status',
      key: 'status',
      render: (v) => <span className="ux4g-badge ux4g-badge-low">{v}</span>,
    },
  ];

  return (
    <DashboardShell
      title="System Authority & Security Governance"
      subtitle={`${currentUser?.name} • Central Infrastructure & RBAC Audit Console`}
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', marginBottom: '28px' }}>
        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
              Core Voice/ASR Pipeline
            </span>
            <Server size={18} color="var(--ux4g-success)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--ux4g-success)' }}>
            Operational (Healthy)
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            Latency: 142ms • End-to-end Encrypted
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
              DPDP 2023 Consent Audit
            </span>
            <Lock size={18} color="var(--ux4g-violet-700)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
            100% Verified
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            Immutable audit record retention
          </div>
        </UX4GCard>

        <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2} padding="20px">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ux4g-text-muted)', textTransform: 'uppercase' }}>
              RBAC Boundaries
            </span>
            <ShieldCheck size={18} color="var(--ux4g-violet-700)" />
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
            Strictly Enforced
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
            Zero elevated role self-assignments
          </div>
        </UX4GCard>
      </div>

      <UX4GCard elevation={2} liftOnHover={false} padding="24px">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Tamper-Evident System Audit Trail
            </h3>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
              In compliance with Section 28 (Audit & Activity Visibility)
            </p>
          </div>
          <span className="ux4g-badge ux4g-badge-low">Append-Only</span>
        </div>

        <UX4GTable columns={columns} data={auditEvents} />
      </UX4GCard>
    </DashboardShell>
  );
};
