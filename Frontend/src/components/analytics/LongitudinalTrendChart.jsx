import React from 'react';
import { Activity, TrendingUp } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const LongitudinalTrendChart = ({
  points = [
    { period: 'Day 1', avgDistress: 58, baseline: 55, highRiskProportion: 12 },
    { period: 'Day 7', avgDistress: 59, baseline: 55, highRiskProportion: 14 },
    { period: 'Day 14', avgDistress: 61, baseline: 55, highRiskProportion: 15 },
    { period: 'Day 21', avgDistress: 57, baseline: 55, highRiskProportion: 11 },
    { period: 'Day 25', avgDistress: 54, baseline: 55, highRiskProportion: 9 },
    { period: 'Day 30', avgDistress: 51, baseline: 55, highRiskProportion: 8 },
  ],
  title = 'Longitudinal Distress Trajectory (Cohort Average)',
  subtitle = '30-Day aggregate distress index vs calibrated baseline stability',
  baselineValue = 55,
}) => {
  const width = 520;
  const height = 180;
  const padding = 36;
  const graphWidth = width - padding * 2;
  const graphHeight = height - padding * 2;

  const getX = (index) => padding + (index / (points.length - 1)) * graphWidth;
  const getY = (val) => padding + graphHeight - (val / 100) * graphHeight;

  const linePath = points.reduce((acc, pt, idx) => {
    const x = getX(idx);
    const y = getY(pt.avgDistress);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaPath = `${linePath} L ${getX(points.length - 1)} ${padding + graphHeight} L ${getX(0)} ${padding + graphHeight} Z`;
  const baselineY = getY(baselineValue);

  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={17} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
          <span style={{ color: 'var(--ux4g-violet-700)' }}>● Cohort Mean</span>
          <span style={{ color: '#64748B' }}>--- Calibrated Baseline ({baselineValue})</span>
        </div>
      </div>

      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <defs>
            <linearGradient id="longitudinalGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6D34EC" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#6D34EC" stopOpacity="0.01" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[20, 40, 60, 80, 100].map((level) => (
            <line
              key={level}
              x1={padding}
              y1={getY(level)}
              x2={width - padding}
              y2={getY(level)}
              stroke="var(--ux4g-border)"
              strokeDasharray="4 4"
              strokeWidth="1"
            />
          ))}

          {/* Baseline reference */}
          <line
            x1={padding}
            y1={baselineY}
            x2={width - padding}
            y2={baselineY}
            stroke="#64748B"
            strokeDasharray="6 4"
            strokeWidth="1.5"
          />

          {/* Area fill */}
          <path d={areaPath} fill="url(#longitudinalGrad)" />

          {/* Line curve */}
          <path
            d={linePath}
            fill="none"
            stroke="var(--ux4g-violet-700)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points */}
          {points.map((pt, idx) => {
            const cx = getX(idx);
            const cy = getY(pt.avgDistress);
            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r="4.5"
                  fill="var(--ux4g-violet-700)"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
                <text
                  x={cx}
                  y={cy - 9}
                  fill="var(--ux4g-violet-950)"
                  fontSize="11"
                  textAnchor="middle"
                  fontWeight="700"
                >
                  {pt.avgDistress}
                </text>
                <text
                  x={cx}
                  y={height - 12}
                  fill="var(--ux4g-text-muted)"
                  fontSize="10"
                  textAnchor="middle"
                  fontWeight="500"
                >
                  {pt.period}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>
        <span>Statutory Trend: <strong>Stabilizing (-12% relative to Day 14 peak)</strong></span>
        <span>High-Risk Cohort Proportion: <strong>8% (Active monitoring)</strong></span>
      </div>
    </UX4GCard>
  );
};
