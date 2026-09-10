import React from 'react';
import { HelpCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import { UX4GCard } from '../common/UX4GCard';

export const ModelExplainabilityCard = ({ factors = [], confidence = '89%', predictionHorizon = '7 Days' }) => {
  return (
    <UX4GCard elevation={2} liftOnHover={false} style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'var(--ux4g-violet-50)', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <HelpCircle size={18} />
          </div>
          <div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              Model Explainability &amp; Risk Drivers
            </h4>
            <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
              Explainable AI factors contributing to this case triage priority
            </p>
          </div>
        </div>

        <span className="ux4g-badge ux4g-badge-primary">Transparent Factors</span>
      </div>

      <div style={{ padding: '10px 14px', backgroundColor: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px', fontSize: '0.825rem', color: '#92400E' }}>
        <AlertTriangle size={16} style={{ flexShrink: 0 }} />
        <span>
          <strong>Clinical Note:</strong> Algorithmic factors are non-binding. Final triage decisions must be validated by the certified human psychologist.
        </span>
      </div>

      <h5 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-900)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
        Identified Contributing Variables:
      </h5>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
        {factors.map((factor, idx) => (
          <div
            key={idx}
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--ux4g-bg)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-border)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              fontSize: '0.85rem',
              color: 'var(--ux4g-text-primary)',
              lineHeight: 1.5,
            }}
          >
            <span
              style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-100)',
                color: 'var(--ux4g-violet-800)',
                fontSize: '0.75rem',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: '1px',
              }}
            >
              {idx + 1}
            </span>
            <span>{factor}</span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--ux4g-border-subtle)', fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
        <span>Confidence: <strong>{confidence}</strong></span>
        <span>Prediction Horizon: <strong>{predictionHorizon}</strong></span>
      </div>
    </UX4GCard>
  );
};
