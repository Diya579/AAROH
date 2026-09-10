import React from 'react';
import { ShieldAlert, AlertTriangle, ShieldCheck, Info } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const RiskDistributionChart = ({
  data = [
    { label: 'Critical', count: 3, percentage: '2.1%', color: '#B91C1C' },
    { label: 'High', count: 8, percentage: '5.6%', color: '#DC2626' },
    { label: 'Medium', count: 54, percentage: '38.0%', color: '#D97706' },
    { label: 'Low', count: 77, percentage: '54.2%', color: '#059669' },
  ],
  title = 'Algorithmic Risk Distribution',
  subtitle = 'De-identified active cohort triage distribution',
}) => {
  const total = data.reduce((acc, item) => acc + item.count, 0);

  // SVG Donut dimensions
  const size = 180;
  const strokeWidth = 26;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Calculate cumulative stroke offsets
  let cumulativePercent = 0;

  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
            {title}
          </h4>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.75rem' }}>
          Total: {total}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px' }}>
        {/* SVG Donut */}
        <div style={{ position: 'relative', width: size, height: size }}>
          <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
            {/* Background track */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="transparent"
              stroke="var(--ux4g-border)"
              strokeWidth={strokeWidth}
            />
            {data.map((slice, i) => {
              const slicePercent = total > 0 ? slice.count / total : 0;
              const strokeDasharray = `${slicePercent * circumference} ${circumference}`;
              const strokeDashoffset = -cumulativePercent * circumference;
              cumulativePercent += slicePercent;

              return (
                <circle
                  key={i}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="transparent"
                  stroke={slice.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  style={{ transition: 'stroke-dasharray 0.4s ease' }}
                />
              );
            })}
          </svg>
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
              {total}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Cases
            </div>
          </div>
        </div>

        {/* Legend List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '180px' }}>
          {data.map((item, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: item.color,
                    display: 'inline-block',
                  }}
                />
                <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--ux4g-violet-950)' }}>
                  {item.label}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-text-primary)' }}>
                  {item.count}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', marginLeft: '6px' }}>
                  ({item.percentage || `${Math.round((item.count / (total || 1)) * 100)}%`})
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--ux4g-border)', fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', display: 'flex', justifyContent: 'space-between' }}>
        <span>Triage Protocol: Predictive Multi-Modal NLP &amp; Acoustics</span>
        <span>Statutory Escalation: Critical &gt;85</span>
      </div>
    </UX4GCard>
  );
};
