import React, { useState } from 'react';
import { CheckCircle2, Calendar, FileText, UserCheck, AlertCircle } from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { caseService } from '../../services/caseService';

export const OutcomeRecordModal = ({ isOpen, onClose, caseData, onOutcomeSaved }) => {
  const [outcomeType, setOutcomeType] = useState('Counselling provided');
  const [status, setStatus] = useState('COMPLETED');
  const [notes, setNotes] = useState('');
  const [followUpRequired, setFollowUpRequired] = useState(true);
  const [followUpDate, setFollowUpDate] = useState('2026-09-10');
  const [isSaving, setIsSaving] = useState(false);

  if (!caseData) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updated = await caseService.recordOutcome(caseData.id, {
        outcomeType,
        status,
        notes,
        followUpRequired,
        followUpDate: followUpRequired ? followUpDate : null,
        officerName: 'Dr. Rajesh Verma (Senior Clinical Psychologist)',
      });
      if (onOutcomeSaved) onOutcomeSaved(updated);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <UX4GModal
      isOpen={isOpen}
      onClose={onClose}
      title="Record Clinical Intervention Outcome"
      subtitle={`Case #${caseData.id} • ${caseData.beneficiaryName}`}
      maxWidth="580px"
    >
      <form onSubmit={handleSubmit} style={{ padding: '4px 0' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Outcome Type
          </label>
          <select
            value={outcomeType}
            onChange={(e) => setOutcomeType(e.target.value)}
            className="ux4g-focus-glow"
            style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.88rem' }}
          >
            <option value="Counselling provided">Counselling Provided (Session Completed)</option>
            <option value="Contacted & Safety Confirmed">Contacted &amp; Safety Confirmed</option>
            <option value="Follow-up required">Follow-up Required (Needs Escalation Support)</option>
            <option value="Referred to Specialized Care">Referred to Specialized Psychiatric Care</option>
            <option value="Referred to DM Legal Aid / Shelter">Referred to DM Legal Aid / Shelter</option>
            <option value="Unable to contact">Unable to Contact (Outside Safe Hours)</option>
            <option value="Declined">Beneficiary Declined Current Session</option>
            <option value="Resolved">Resolved / Stabilized</option>
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Case Progression Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="ux4g-focus-glow"
            style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.88rem' }}
          >
            <option value="IN_PROGRESS">IN PROGRESS (Under Active Follow-up)</option>
            <option value="COMPLETED">COMPLETED (Milestone Attained)</option>
            <option value="ESCALATED">ESCALATED (Forward to District Magistrate Cell)</option>
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
            Clinical Session Notes
          </label>
          <textarea
            rows={4}
            required
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Record summary of assessment, coping techniques reinforced, beneficiary affect, and safety measures..."
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

        {/* Follow-up Scheduling */}
        <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: followUpRequired ? '12px' : '0' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                checked={followUpRequired}
                onChange={(e) => setFollowUpRequired(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--ux4g-violet-700)' }}
              />
              <span>Schedule Structured Follow-Up Session</span>
            </label>
          </div>

          {followUpRequired && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Calendar size={18} color="var(--ux4g-violet-700)" />
              <input
                type="date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                className="ux4g-focus-glow"
                style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', fontSize: '0.85rem' }}
              />
              <span style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>Respecting beneficiary safe hours (17:00 – 19:00 IST)</span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--ux4g-border)' }}>
          <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
            Cancel
          </UX4GButton>
          <UX4GButton variant="primary" size="md" type="submit" loading={isSaving} icon={CheckCircle2}>
            Confirm &amp; Log Outcome
          </UX4GButton>
        </div>
      </form>
    </UX4GModal>
  );
};
