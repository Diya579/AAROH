import React from 'react';
import { BarChart3, ChevronRight } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const DistrictComparisonChart = ({
  data = [
    { district: 'South Delhi', totalCases: 142, highRisk: 11, pendingInterventions: 5, avgResponse: '1.4 hrs', compliance: '98.6%' },
    { district: 'North Delhi', totalCases: 98, highRisk: 6, pendingInterventions: 2, avgResponse: '1.8 hrs', compliance: '96.8%' },
    { district: 'West Delhi', totalCases: 115, highRisk: 8, pendingInterventions: 3, avgResponse: '1.5 hrs', compliance: '99.1%' },
    { district: 'East Delhi', totalCases: 87, highRisk: 5, pendingInterventions: 1, avgResponse: '2.0 hrs', compliance: '95.4%' },
    { district: 'Central Delhi', totalCases: 64, highRisk: 3, pendingInterventions: 0, avgResponse: '1.2 hrs', compliance: '100%' },
  ],
  title = 'Inter-District Caseload & Compliance Comparison',
  subtitle = 'Comparative metrics across administrative districts under State Directorate',
  onSelectDistrict = null,
  activeDistrict = null,
}) => {
  const maxTotal = Math.max(...data.map(d => d.totalCases || d.monitored || 100));

  return (
    <UX4GCard elevation={1} liftOnHover={false} padding="22px">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={18} color="var(--ux4g-violet-700)" />
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h4>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
            {subtitle}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', fontSize: '0.75rem', fontWeight: 600 }}>
          <span style={{ color: 'var(--ux4g-violet-700)' }}>■ Total Caseload</span>
          <span style={{ color: 'var(--ux4g-danger)' }}>■ High Risk</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {data.map((item, idx) => {
          const totalVal = item.totalCases || item.monitored || 0;
          const highRiskVal = item.highRisk || (item.highRiskRate ? parseInt(item.highRiskRate) : 0);
          const name = item.district || item.state;
          const isSelected = activeDistrict && activeDistrict.toLowerCase() === name.toLowerCase();

          const totalWidth = Math.round((totalVal / maxTotal) * 100);
          const highRiskWidth = totalVal > 0 ? Math.round((highRiskVal / totalVal) * totalWidth) : 0;

          return (
            <div
              key={idx}
              onClick={() => onSelectDistrict && onSelectDistrict(name)}
              style={{
                padding: '8px 10px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isSelected ? 'var(--ux4g-violet-50)' : 'transparent',
                border: isSelected ? '1.5px solid var(--ux4g-violet-500)' : '1px solid transparent',
                cursor: onSelectDistrict ? 'pointer' : 'default',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>
                    {name}
                  </span>
                  {onSelectDistrict && <ChevronRight size={14} color="var(--ux4g-violet-700)" />}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem' }}>
                  <span><strong>{totalVal}</strong> cases</span>
                  <span style={{ color: 'var(--ux4g-danger)', fontWeight: 600 }}>{highRiskVal} high risk</span>
                  <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.72rem' }}>
                    {item.compliance} SLA
                  </span>
                </div>
              </div>

              {/* Stacked Bar */}
              <div style={{ width: '100%', height: '10px', backgroundColor: 'var(--ux4g-border)', borderRadius: '5px', overflow: 'hidden', position: 'relative' }}>
                <div
                  style={{
                    width: `${totalWidth}%`,
                    height: '100%',
                    backgroundColor: 'var(--ux4g-violet-700)',
                    borderRadius: '5px',
                    position: 'absolute',
                    left: 0,
                    top: 0,
                  }}
                />
                <div
                  style={{
                    width: `${Math.max(highRiskWidth, 4)}%`,
                    height: '100%',
                    backgroundColor: 'var(--ux4g-danger)',
                    borderRadius: '5px 0 0 5px',
                    position: 'absolute',
                    left: 0,
                    top: 0,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {onSelectDistrict && (
        <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--ux4g-violet-700)', textAlign: 'right', fontWeight: 600 }}>
          💡 Click any row to drill down into district caseload
        </div>
      )}
    </UX4GCard>
  );
};
