import React from 'react';
import { Award, CheckCircle2 } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const OutcomeDistributionChart = ({
  outcomes = [
    { type: 'Counselling provided', count: 42, color: 'var(--ux4g-violet-700)' },
    { type: 'Safety confirmed', count: 35, color: '#8C6240' },
    { type: 'Medical referral', count: 18, color: '#AB8867' },
    { type: 'Financial assistance', count: 14, color: '#443F24' },
    { type: 'Legal aid (NALSA)', count: 11, color: '#9C631B' },
    { type: 'Witness protection', count: 9, color: '#822710' },
    { type: 'Relocation / shelter', count: 6, color: '#B8860B' },
    { type: 'Resolved / stabilized', count: 28, color: '#3A2312' },
  ],
  title = 'Categorical Outcome Distribution',
  subtitle = 'Breakdown of recorded relief outcomes across statutory categories',
}) => {
  const maxCount = Math.max(...outcomes.map(o => o.count), 1);
  const totalOutcomes = outcomes.reduce((acc, o) => acc + o.count, 0);

  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.75rem' }}>
          Recorded: {totalOutcomes}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {outcomes.map((item, idx) => {
          const barWidthPercent = Math.round((item.count / maxCount) * 100);
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '160px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                {item.type}
              </div>
              <div style={{ flex: 1, backgroundColor: 'var(--ux4g-border)', height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${barWidthPercent}%`,
                    height: '100%',
                    backgroundColor: item.color,
                    borderRadius: '5px',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
              <div style={{ width: '40px', textAlign: 'right', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                {item.count}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--ux4g-border)', fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>
        8 Statutory Outcome Categories under SC/ST Protection of Atrocities Rehabilitation Guidelines
      </div>
    </UX4GCard>
  );
};
