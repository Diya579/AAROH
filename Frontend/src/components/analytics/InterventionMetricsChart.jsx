import React from 'react';
import { ShieldCheck, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const InterventionMetricsChart = ({
  stages = [
    { label: 'Pending Review', status: 'PENDING', count: 5, color: '#9C631B', description: 'Within triage queue' },
    { label: 'Assigned to Official', status: 'ASSIGNED', count: 8, color: '#8C6240', description: 'SLA countdown active' },
    { label: 'In Progress / Active', status: 'IN_PROGRESS', count: 14, color: '#543118', description: 'Clinical / legal ongoing' },
    { label: 'Completed / Stabilized', status: 'COMPLETED', count: 126, color: '#443F24', description: 'Outcome verified' },
    { label: 'Escalated to DM / Nodal', status: 'ESCALATED', count: 2, color: '#822710', description: 'Statutory escalation' },
  ],
  title = 'Intervention Lifecycle Pipeline',
  subtitle = 'Progress of statutory relief across administrative stages',
}) => {
  const total = stages.reduce((acc, s) => acc + s.count, 0);

  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.75rem' }}>
          Total Actions: {total}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {stages.map((stage, idx) => {
          const percent = total > 0 ? Math.round((stage.count / total) * 100) : 0;
          return (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.825rem' }}>
                <span style={{ fontWeight: 600, color: 'var(--ux4g-violet-950)' }}>
                  {stage.label}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 700, color: 'var(--ux4g-text-primary)' }}>{stage.count}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>({percent}%)</span>
                </div>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '8px',
                  backgroundColor: 'var(--ux4g-border)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${percent}%`,
                    minWidth: stage.count > 0 ? '6px' : '0px',
                    height: '100%',
                    backgroundColor: stage.color,
                    borderRadius: '4px',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>
                {stage.description}
              </div>
            </div>
          );
        })}
      </div>
    </UX4GCard>
  );
};
