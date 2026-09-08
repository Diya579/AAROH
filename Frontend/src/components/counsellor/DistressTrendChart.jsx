import React from 'react';
import { TrendingUp, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';
import { RiskBadge } from '../common/UX4GBadge';

export const DistressTrendChart = ({ caseData }) => {
  if (!caseData) return null;

  const points = caseData.distressHistory || [
    { day: 'Day 1', score: 56, baseline: 56 },
    { day: 'Day 7', score: 58, baseline: 56 },
    { day: 'Day 14', score: 54, baseline: 56 },
    { day: 'Day 21', score: 62, baseline: 56 },
    { day: 'Day 25', score: 68, baseline: 56 },
    { day: 'Day 30', score: 74, baseline: 56 },
  ];

  // SVG dimensions
  const width = 500;
  const height = 180;
  const padding = 36;
  const graphWidth = width - padding * 2;
  const graphHeight = height - padding * 2;

  // Max distress is 100, min is 0
  const getX = (index) => padding + (index / (points.length - 1)) * graphWidth;
  const getY = (val) => padding + graphHeight - (val / 100) * graphHeight;

  // Generate SVG path line
  const linePath = points.reduce((acc, pt, idx) => {
    const x = getX(idx);
    const y = getY(pt.score);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  // Generate closed area path for gradient fill
  const areaPath = `${linePath} L ${getX(points.length - 1)} ${padding + graphHeight} L ${getX(0)} ${padding + graphHeight} Z`;

  // Baseline line
  const baselineY = getY(caseData.baselineScore || 56);

  return (
    <UX4GCard elevation={2} liftOnHover={false} style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Longitudinal Distress Trajectory (30-Day Horizon)
            </h4>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            Adaptive individual baseline deviation curve vs generic statistical population models
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--ux4g-text-muted)' }}>Trend:</span>
          <span className={`ux4g-badge ${caseData.trend.includes('Worsening') ? 'ux4g-badge-high' : 'ux4g-badge-low'}`}>
            {caseData.trend}
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '12px', marginBottom: '18px', padding: '12px 16px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Current Score</span>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>{caseData.distressScore} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--ux4g-text-muted)' }}>/ 100</span></div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Calibrated Baseline</span>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--ux4g-text-secondary)' }}>{caseData.baselineScore} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--ux4g-text-muted)' }}>/ 100</span></div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Baseline Shift</span>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: caseData.baselineDeviation?.startsWith('+') ? 'var(--ux4g-danger)' : 'var(--ux4g-success)' }}>
            {caseData.baselineDeviation}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Escalation Risk</span>
          <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--ux4g-danger-text)' }}>
            {caseData.escalationProbability}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Prediction Horizon</span>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-900)', paddingTop: '2px' }}>
            {caseData.predictionHorizon}
          </div>
        </div>
      </div>

      {/* Accessible Responsive SVG Chart */}
      <div style={{ width: '100%', overflowX: 'auto', backgroundColor: '#FFFFFF', borderRadius: 'var(--radius-md)', padding: '8px 0' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          <defs>
            <linearGradient id="distressGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6D34EC" stopOpacity="0.25" />
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
              stroke="var(--ux4g-border-subtle)"
              strokeDasharray="4 4"
              strokeWidth="1"
            />
          ))}

          {/* Baseline Reference Dashed Line */}
          <line
            x1={padding}
            y1={baselineY}
            x2={width - padding}
            y2={baselineY}
            stroke="#94A3B8"
            strokeDasharray="6 4"
            strokeWidth="1.5"
          />
          <text x={width - padding - 4} y={baselineY - 5} fill="#64748B" fontSize="10" textAnchor="end" fontWeight="600">
            Individual Baseline ({caseData.baselineScore})
          </text>

          {/* Area Fill */}
          <path d={areaPath} fill="url(#distressGradient)" />

          {/* Curve Line */}
          <path
            d={linePath}
            fill="none"
            stroke="var(--ux4g-violet-700)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data Points */}
          {points.map((pt, idx) => {
            const cx = getX(idx);
            const cy = getY(pt.score);
            const isLast = idx === points.length - 1;
            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isLast ? 6 : 4}
                  fill={isLast ? 'var(--ux4g-danger)' : 'var(--ux4g-violet-700)'}
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
                <text
                  x={cx}
                  y={cy - 10}
                  fill="var(--ux4g-violet-950)"
                  fontSize="11"
                  textAnchor="middle"
                  fontWeight="700"
                >
                  {pt.score}
                </text>
                <text
                  x={cx}
                  y={height - 12}
                  fill="var(--ux4g-text-muted)"
                  fontSize="10"
                  textAnchor="middle"
                  fontWeight="500"
                >
                  {pt.day}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
        <span>Confidence Level: <strong>{caseData.confidence}</strong></span>
        <span>Human Oversight Principle: AI provides advisory distress trajectory only.</span>
      </div>
    </UX4GCard>
  );
};
