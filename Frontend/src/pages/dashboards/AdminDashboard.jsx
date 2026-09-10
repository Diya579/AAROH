import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  ShieldCheck, 
  Server, 
  Lock, 
  Users, 
  Cpu, 
  Activity, 
  CheckCircle2,
  AlertTriangle,
  Play,
  Download,
  Terminal,
  Database,
  RefreshCw,
  Shield
} from 'lucide-react';
import { useAuth, DEMO_USERS } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GTable } from '../../components/common/UX4GTable';
import { UX4GButton } from '../../components/common/UX4GButton';

export const AdminDashboard = () => {
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };

  const [diagnosticRunning, setDiagnosticRunning] = useState(false);
  const [diagnosticDone, setDiagnosticDone] = useState(false);
  const [exportAlert, setExportAlert] = useState('');

  const auditEvents = [
    { timestamp: '2026-09-08 08:14:10', event: 'Role Session Initialized', actor: 'Meera Sharma (VICTIM)', ip: '10.24.11.8', status: 'Success' },
    { timestamp: '2026-09-08 07:55:00', event: 'Caseload Triage Escalated', actor: 'Dr. Rajesh Varma (COUNSELLOR)', ip: '10.42.0.12', status: 'Logged' },
    { timestamp: '2026-09-08 07:30:32', event: 'Intervention SLA Acknowledged', actor: 'Ananya Sen, IAS (DISTRICT)', ip: '10.88.4.19', status: 'Logged' },
    { timestamp: '2026-09-08 06:12:04', event: 'Audit Log Integrity Check', actor: 'SYS-ADM-0001 (ADMIN)', ip: '127.0.0.1', status: 'Verified' },
    { timestamp: '2026-09-07 22:40:19', event: 'DPDP Consent Preferences Updated', actor: 'Meera Sharma (VICTIM)', ip: '10.24.11.8', status: 'Encrypted' },
    { timestamp: '2026-09-07 20:15:44', event: 'State Performance Report Exported', actor: 'Dr. Kavita Rao (STATE)', ip: '10.12.9.4', status: 'Success' },
  ];

  const auditColumns = [
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

  const userRoleList = Object.keys(DEMO_USERS).map(key => {
    const u = DEMO_USERS[key];
    return {
      name: u.name,
      userId: u.userId,
      role: u.role,
      roleTitle: u.roleTitle,
      idBadge: u.idBadge,
      status: 'Active Provisioned',
    };
  });

  const userColumns = [
    {
      header: 'Authorized User',
      key: 'name',
      render: (v, row) => (
        <div>
          <div style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>{v}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>{row.userId}</div>
        </div>
      ),
    },
    {
      header: 'Assigned Role',
      key: 'role',
      render: (v, row) => (
        <div>
          <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.75rem' }}>{v}</span>
          <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>{row.roleTitle}</div>
        </div>
      ),
    },
    {
      header: 'Statutory Credential ID',
      key: 'idBadge',
      render: (v) => <span style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{v}</span>,
    },
    {
      header: 'RBAC Status',
      key: 'status',
      render: (v) => <span className="ux4g-badge ux4g-badge-low">{v}</span>,
    },
  ];

  const apiEndpoints = [
    { service: 'Voice/ASR Pipeline (Diya)', route: '/api/v1/voice/asr', latency: '142ms', uptime: '99.99%', status: 'Operational' },
    { service: 'AI Distress Modeling (Adwait)', route: '/api/v1/inference/distress', latency: '210ms', uptime: '99.95%', status: 'Operational' },
    { service: 'FastAPI Application Layer (Mahendra)', route: '/api/v1/cases/query', latency: '65ms', uptime: '100%', status: 'Operational' },
    { service: 'Intervention & Routing Engine (Preet)', route: '/api/v1/interventions/route', latency: '85ms', uptime: '99.98%', status: 'Operational' },
    { service: 'DPDP 2023 Consent Vault', route: '/api/v1/dpdp/consent-vault', latency: '48ms', uptime: '100%', status: 'Operational' },
  ];

  const handleRunDiagnostic = () => {
    setDiagnosticRunning(true);
    setDiagnosticDone(false);
    setTimeout(() => {
      setDiagnosticRunning(false);
      setDiagnosticDone(true);
    }, 1200);
  };

  const handleExportAudit = () => {
    setExportAlert('Cryptographic audit trail exported to SEC-AUDIT-20260908.json.');
    setTimeout(() => setExportAlert(''), 4000);
  };

  return (
    <DashboardShell
      title="System Authority &amp; Security Governance"
      subtitle={`${currentUser?.name} • Central Infrastructure, RBAC Audit &amp; AI Model Governance`}
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: SYSTEM OVERVIEW
          ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
          {/* 3 Core System Health Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
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

          {/* Model Governance Banner */}
          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
              <div>
                <span className="ux4g-badge ux4g-badge-primary" style={{ marginBottom: '6px' }}>
                  Production Model Governance
                </span>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Acoustic &amp; Linguistic Distress Model: Version 2.4-Production
                </h3>
                <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                  Audited under AI Safety Guidelines for Sensitive Welfare Interventions. No automated penalties. Human review required for all high-risk flags.
                </p>
              </div>
              <UX4GButton variant="outline" size="sm" icon={Activity} onClick={() => handleTabChange('health')}>
                System Health Details
              </UX4GButton>
            </div>
          </div>

          {/* Recent Audit Events Snippet */}
          <UX4GCard elevation={2} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Recent System Audit Events
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                  Real-time cryptographic access and role change logging
                </p>
              </div>
              <UX4GButton variant="outline" size="sm" onClick={() => handleTabChange('audit')}>
                Full Audit Log
              </UX4GButton>
            </div>

            <UX4GTable columns={auditColumns} data={auditEvents.slice(0, 4)} />
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 2: ROLE MANAGEMENT (RBAC)
          ========================================================================= */}
      {activeTab === 'rbac' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Authorized Role-Based Access Control (RBAC) Architecture
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
              As defined in Section 4 of AAROH Plan: Every authorized stakeholder accesses only features appropriate to their role. Strictly NO public registration.
            </p>
          </div>

          {/* Provisioned Personas Table */}
          <UX4GCard elevation={2} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Provisioned Government &amp; Citizen Personas ({userRoleList.length})
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                  Assigned through authorized administrative workflow with statutory verification badges.
                </p>
              </div>
              <span className="ux4g-badge ux4g-badge-low">All Verified</span>
            </div>

            <UX4GTable columns={userColumns} data={userRoleList} />
          </UX4GCard>

          {/* Permissions Matrix */}
          <UX4GCard elevation={1} padding="24px">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '14px' }}>
              Statutory Permissions Matrix
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
              <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)' }}>
                <strong style={{ color: 'var(--ux4g-violet-950)' }}>VICTIM / CITIZEN</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                  Personal check-ins, consent preferences, distress trend, recovery milestones. Zero internal notes or other victims' data.
                </p>
              </div>
              <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)' }}>
                <strong style={{ color: 'var(--ux4g-violet-950)' }}>COUNSELLOR</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                  Assigned cases, acoustic distress trends, intervention execution, outcome recording, SLA tracking.
                </p>
              </div>
              <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)' }}>
                <strong style={{ color: 'var(--ux4g-violet-950)' }}>DISTRICT OFFICIAL</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                  District caseload oversight, escalations, counselor capacity allocation, statutory compensation sanction under PoA Rule 12(4).
                </p>
              </div>
              <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border-subtle)' }}>
                <strong style={{ color: 'var(--ux4g-violet-950)' }}>STATE &amp; NATIONAL</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                  Comparative jurisdiction matrices, longitudinal trends, policy reporting, 3-tier drill-down to cases.
                </p>
              </div>
            </div>
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 3: SECURITY & AUDIT LOG
          ========================================================================= */}
      {activeTab === 'audit' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {exportAlert && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success)', fontWeight: 600 }}>
              <CheckCircle2 size={18} />
              <span>{exportAlert}</span>
            </div>
          )}

          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                Immutable DPDP Act 2023 Security &amp; Audit Trail
              </h3>
              <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                All authorization attempts, case file accesses, intervention triggers, and consent modifications are recorded chronologically.
              </p>
            </div>
            <UX4GButton variant="outline" size="sm" icon={Download} onClick={handleExportAudit}>
              Export Cryptographic Trail (JSON)
            </UX4GButton>
          </div>

          <UX4GCard elevation={2} padding="24px">
            <UX4GTable columns={auditColumns} data={auditEvents} caption="System-wide security and audit events" />
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 4: SYSTEM HEALTH & APIS
          ========================================================================= */}
      {activeTab === 'health' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '22px 26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', boxShadow: 'var(--elevation-1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                Backend Integration Health &amp; Microservices API Status
              </h3>
              <p style={{ fontSize: '0.84rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px' }}>
                Real-time latency metrics for backend services (Diya, Adwait, Mahendra, Preet) consuming statutory contracts.
              </p>
            </div>

            <UX4GButton
              variant="primary"
              size="sm"
              icon={RefreshCw}
              onClick={handleRunDiagnostic}
              disabled={diagnosticRunning}
            >
              {diagnosticRunning ? 'Running Ping Diagnostic...' : 'Run Live Diagnostic Ping'}
            </UX4GButton>
          </div>

          {diagnosticDone && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success)', fontWeight: 600 }}>
              <CheckCircle2 size={18} />
              <span>Live Diagnostic Complete: All 5 core services responding with 0 errors. Average latency: 108ms.</span>
            </div>
          )}

          {/* Endpoints Table */}
          <UX4GCard elevation={1} padding="24px">
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '16px' }}>
              Microservices Latency &amp; Uptime Table
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {apiEndpoints.map((ep) => (
                <div key={ep.route} style={{ padding: '14px 18px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <strong style={{ fontSize: '0.92rem', color: 'var(--ux4g-violet-950)' }}>{ep.service}</strong>
                    <div style={{ fontSize: '0.78rem', fontFamily: 'monospace', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>{ep.route}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Latency: <strong>{ep.latency}</strong></span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Uptime: <strong>{ep.uptime}</strong></span>
                    <span className="ux4g-badge ux4g-badge-low">{ep.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </UX4GCard>

          {/* Active Model Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
            <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase' }}>Speech Acoustic Model</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>Distress-Acoustic-v2.4</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Feature extractor: F0 pitch variance, jitter, shimmer, speaking rate deviations.</p>
              <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--ux4g-success)', fontWeight: 600 }}>Validation Accuracy: 94.2% • DPDP Compliant</div>
            </div>

            <div style={{ backgroundColor: 'var(--ux4g-surface)', padding: '20px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase' }}>NLP Semantic Model</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', margin: '4px 0' }}>NLP-Sentiment-PoA-v3.1</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>Linguistic parser: Fear, helplessness, sleep disruption, trauma indicators.</p>
              <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--ux4g-success)', fontWeight: 600 }}>Validation Accuracy: 96.8% • DPDP Compliant</div>
            </div>
          </div>
        </div>
      )}
    </DashboardShell>
  );
};
