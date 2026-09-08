import React from 'react';
import { Clock, CheckCircle2 } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const ResponseTimeChart = ({
  slaTiers = [
    { label: '≤ 2 Hours (Emergency SLA)', count: 3, compliance: '100%', color: '#B91C1C', maxTime: '2h' },
    { label: '2–4 Hours (Urgent SLA)', count: 8, compliance: '98.5%', color: '#DC2626', maxTime: '4h' },
    { label: '4–24 Hours (Standard SLA)', count: 38, compliance: '99.2%', color: '#6D34EC', maxTime: '24h' },
    { label: '> 24 Hours (Routine Maintenance)', count: 96, compliance: '100%', color: '#059669', maxTime: '72h' },
  ],
  overallCompliance = '98.6%',
  avgResponseHours = '1.4 hrs',
  title = 'Response-Time & SLA Adherence',
  subtitle = 'Statutory time-to-first-action metrics against district benchmarks',
}) => {
  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={18} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '14px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Avg Response</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>{avgResponseHours}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Compliance</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--ux4g-success)' }}>{overallCompliance}</div>
          </div>
        </div>
      </div>

      {/* Grid of SLA Tiers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {slaTiers.map((tier, idx) => (
          <div
            key={idx}
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--ux4g-bg)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-border)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: tier.color }} />
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  {tier.label}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
                <span style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  {tier.count}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>actions taken</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--ux4g-border)' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>Adherence:</span>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--ux4g-success)' }}>
                {tier.compliance}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '14px', fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', display: 'flex', justifyContent: 'space-between' }}>
        <span>Statutory Mandate: Section 15B SC/ST Prevention of Atrocities Rules</span>
        <span>Escalation Rule: &gt;24h breach triggers DM notification</span>
      </div>
    </UX4GCard>
  );
};
