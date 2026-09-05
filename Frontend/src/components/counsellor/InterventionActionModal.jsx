import React, { useState } from 'react';
import { Shield, Sparkles, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { caseService } from '../../services/caseService';

export const InterventionActionModal = ({ isOpen, onClose, caseData, onInterventionUpdated }) => {
  const [category, setCategory] = useState(caseData?.recommendedIntervention || 'Counselling / psychological support');
  const [slaHours, setSlaHours] = useState(4);
  const [instructions, setInstructions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!caseData) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const updated = await caseService.updateIntervention(caseData.id, {
        category,
        slaHours,
        instructions,
      });
      if (onInterventionUpdated) onInterventionUpdated(updated);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <UX4GModal
      isOpen={isOpen}
      onClose={onClose}
      title="Human Decision: Assign Statutory Intervention"
      subtitle={`Case #${caseData.id} • ${caseData.beneficiaryName}`}
      maxWidth="600px"
    >
      <form onSubmit={handleSubmit} style={{ padding: '4px 0' }}>
        {/* Human vs AI Distinction Banner */}
        <div style={{ backgroundColor: 'var(--ux4g-violet-50)', border: '1px solid var(--ux4g-violet-200)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Sparkles size={16} color="var(--ux4g-violet-700)" />
            <strong style={{ fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>
              AI Advisory Recommendation:
            </strong>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-violet-800)', lineHeight: 1.4 }}>
            "{caseData.recommendedIntervention}" (Escalation probability: {caseData.escalationProbability})
          </p>
          <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', marginTop: '6px' }}>
            ⚖️ <strong>Rule 5:</strong> The human clinician possesses statutory authority to validate, modify, or escalate this pathway.
          </div>
        </div>

        {/* Category Selection */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Statutory Intervention Category
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="ux4g-focus-glow"
            style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.88rem' }}
          >
            <option value="Counselling / psychological support">Counselling / Psychological Support (Tele-MANAS linkage)</option>
            <option value="Medical treatment / referral">Medical Treatment / Clinical Psychiatric Referral</option>
            <option value="Witness protection">Witness &amp; Physical Protection Protocol</option>
            <option value="Relocation / safety support">Relocation &amp; Safe Housing Routing</option>
            <option value="Financial / compensation assistance">Financial &amp; Statutory Compensation Disbursement</option>
            <option value="Legal aid (NALSA)">Judicial Legal Aid (NALSA Representation)</option>
            <option value="Rehabilitation">Comprehensive Multi-Agency Rehabilitation</option>
            <option value="Continued monitoring">Continued Baseline Longitudinal Monitoring</option>
          </select>
        </div>

        {/* Statutory SLA Countdown Allocation */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Statutory SLA Window for Action
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            {[
              { hours: 2, label: '2 Hours (Emergency)' },
              { hours: 4, label: '4 Hours (Urgent)' },
              { hours: 24, label: '24 Hours (Standard)' },
              { hours: 48, label: '48 Hours (Routine)' },
            ].map(item => (
              <button
                key={item.hours}
                type="button"
                onClick={() => setSlaHours(item.hours)}
                style={{
                  padding: '10px 8px',
                  borderRadius: 'var(--radius-md)',
                  border: slaHours === item.hours ? '2px solid var(--ux4g-violet-700)' : '1px solid var(--ux4g-border)',
                  backgroundColor: slaHours === item.hours ? 'var(--ux4g-violet-50)' : '#FFF',
                  color: slaHours === item.hours ? 'var(--ux4g-violet-950)' : 'var(--ux4g-text-secondary)',
                  fontWeight: slaHours === item.hours ? 700 : 500,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Action Directives / Instructions */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Clinical Action Directives &amp; Protocol Instructions
          </label>
          <textarea
            rows={3}
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Enter clinical instructions for local field officer / support unit..."
            className="ux4g-focus-glow"
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              border: '1.5px solid var(--ux4g-border)',
              fontSize: '0.88rem',
              fontFamily: 'inherit',
              resize: 'vertical',
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--ux4g-border)' }}>
          <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
            Cancel
          </UX4GButton>
          <UX4GButton variant="primary" size="md" type="submit" loading={isSubmitting} icon={Shield}>
            Authorize &amp; Dispatch Intervention
          </UX4GButton>
        </div>
      </form>
    </UX4GModal>
  );
};
