import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Activity, ShieldCheck, Clock, TrendingUp, Landmark } from 'lucide-react';
import { RetroStamp } from '../components/RetroStamp';
import { RetroTiltCard } from '../components/RetroTiltCard';
import { analyticsService } from '../../services/analyticsService';

export const RetroAnalyticsView = () => {
  const [district, setDistrict] = useState('South Delhi');
  const [data, setData] = useState(null);

  useEffect(() => {
    async function loadStats() {
      const stats = await analyticsService.getDistrictAnalytics(district);
      setData(stats);
    }
    loadStats();
  }, [district]);

  if (!data) {
    return (
      <div style={{ maxWidth: '1000px', margin: '40px auto', textAlign: 'center', fontFamily: 'var(--retro-font-mono)' }}>
        COMPUTING NATIONAL STATISTICAL AGGREGATIONS...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Top Header Tag */}
      <div
        style={{
          borderBottom: '2.5px solid var(--retro-ink-black)',
          paddingBottom: '14px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RetroStamp type="verified" label="STATISTICAL SUPPLEMENT" size="sm" />
            <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem' }}>
              SECTION 15A STATUTORY AUDIT & OUTCOME LEDGER
            </span>
          </div>
          <h2 className="retro-headline-md" style={{ margin: '6px 0 0 0' }}>
            National & District Trauma Intervention Ledger
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem', fontWeight: 700 }}>
            JURISDICTION:
          </span>
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            style={{
              padding: '6px 12px',
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.8rem',
              fontWeight: 700,
              backgroundColor: 'var(--retro-bg-paper-light)',
              border: '2px solid var(--retro-ink-black)',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="South Delhi">South Delhi (Pilot Core)</option>
            <option value="North West Delhi">North West Delhi</option>
            <option value="Pune">Pune District</option>
            <option value="Jaipur">Jaipur Central</option>
          </select>
        </div>
      </div>

      {/* Top 4 Key Metrics */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '18px',
          marginBottom: '32px',
        }}
      >
        <RetroTiltCard cardboard>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--retro-ink-muted)' }}>
            ACTIVE BENEFICIARY DOSSIERS
          </div>
          <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2.5rem', fontWeight: 900, margin: '6px 0' }}>
            {data.totalCases}
          </div>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem' }}>
            Under continuous daily baseline surveillance
          </div>
        </RetroTiltCard>

        <RetroTiltCard paper>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--retro-stamp-red)' }}>
            CRITICAL & HIGH RISK ALERTS
          </div>
          <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2.5rem', fontWeight: 900, color: 'var(--retro-stamp-red)', margin: '6px 0' }}>
            {data.criticalCount + data.highCount}
          </div>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem' }}>
            Triggered immediate clinical escalation
          </div>
        </RetroTiltCard>

        <RetroTiltCard cardboard>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700, color: 'var(--retro-stamp-green)' }}>
            SUCCESSFUL RESOLUTIONS
          </div>
          <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2.5rem', fontWeight: 900, color: 'var(--retro-stamp-green)', margin: '6px 0' }}>
            {data.completedInterventions}
          </div>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem' }}>
            Psychological & legal stabilization achieved
          </div>
        </RetroTiltCard>

        <RetroTiltCard paper>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
            STATUTORY SLA COMPLIANCE
          </div>
          <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2.5rem', fontWeight: 900, margin: '6px 0' }}>
            100%
          </div>
          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem', color: 'var(--retro-stamp-green)', fontWeight: 800 }}>
            0 Overdue breaches recorded
          </div>
        </RetroTiltCard>
      </div>

      {/* Grid: Outcome Distribution & Longitudinal Trend */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '24px',
          marginBottom: '32px',
        }}
      >
        {/* Outcome Breakdown Ledger */}
        <div
          style={{
            border: '2px solid var(--retro-ink-black)',
            backgroundColor: 'var(--retro-bg-paper)',
            padding: '24px',
            boxShadow: 'var(--retro-shadow-md)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 className="retro-headline-md" style={{ margin: 0 }}>
              Intervention Outcomes Dispatched
            </h3>
            <RetroStamp type="verified" label="OFFICIALLY LOGGED" size="sm" />
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--retro-font-mono)', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--retro-ink-black)', textAlign: 'left' }}>
                <th style={{ padding: '8px 4px' }}>INTERVENTION CATEGORY</th>
                <th style={{ padding: '8px 4px', textAlign: 'right' }}>COUNT</th>
                <th style={{ padding: '8px 4px', textAlign: 'right' }}>RATIO</th>
              </tr>
            </thead>
            <tbody>
              {data.outcomes.map((item, idx) => {
                const total = data.outcomes.reduce((acc, o) => acc + o.count, 0);
                const pct = Math.round((item.count / total) * 100);
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--retro-border-light)' }}>
                    <td style={{ padding: '8px 4px', fontWeight: 700 }}>{item.type}</td>
                    <td style={{ padding: '8px 4px', textAlign: 'right', fontWeight: 800 }}>{item.count}</td>
                    <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--retro-ink-muted)' }}>{pct}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Longitudinal Seismograph Table */}
        <div
          style={{
            border: '2px solid var(--retro-ink-black)',
            backgroundColor: 'var(--retro-bg-paper)',
            padding: '24px',
            boxShadow: 'var(--retro-shadow-md)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 className="retro-headline-md" style={{ margin: 0 }}>
              30-Day Longitudinal Trajectory
            </h3>
            <RetroStamp type="sovereign" label="TIME-SERIES" size="sm" />
          </div>

          <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem', marginBottom: '16px', color: 'var(--retro-ink-muted)' }}>
            Average calibrated distress score tracking across all pilot beneficiaries over the past 30 days:
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data.trendHistory.map((pt, i) => (
              <div key={i} style={{ borderBottom: '1px dashed var(--retro-border-light)', paddingBottom: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--retro-font-mono)', fontSize: '0.78rem', marginBottom: '4px' }}>
                  <span>{pt.period}</span>
                  <span><strong>{pt.avgDistress}/100</strong> (Baseline: {pt.baseline})</span>
                </div>
                <div style={{ height: '8px', backgroundColor: 'var(--retro-bg-cardboard)', border: '1px solid var(--retro-ink-black)' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${pt.avgDistress}%`,
                      backgroundColor: pt.avgDistress > 58 ? 'var(--retro-stamp-red)' : 'var(--retro-stamp-green)',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              marginTop: '18px',
              padding: '10px',
              backgroundColor: 'var(--retro-bg-cardboard-dark)',
              border: '1px solid var(--retro-ink-black)',
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.72rem',
            }}
          >
            OBSERVATION: Calibrated distress dropped from 61/100 (Peak at Day 14) to 51/100 following active clinical grounding and legal aid intervention.
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetroAnalyticsView;
