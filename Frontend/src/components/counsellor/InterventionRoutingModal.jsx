import React, { useState } from 'react';
import { Shield, Sparkles, Clock, AlertTriangle, UserCheck, PhoneCall, CheckCircle2 } from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { caseService } from '../../services/caseService';

export const InterventionRoutingModal = ({
  isOpen,
  onClose,
  caseData,
  onInterventionUpdated,
}) => {
  const counsellorsList = [
    { name: 'Dr. Rajesh Verma', role: 'Senior Clinical Psychologist', capacity: 90, caseload: 18, status: 'Near Limit' },
    { name: 'Dr. Sunita Rao', role: 'Adolescent & Child Atrocity Relief', capacity: 70, caseload: 14, status: 'Optimal' },
    { name: 'Shri Vikram Malhotra', role: 'Rehabilitation & Legal Aid Liaison', capacity: 95, caseload: 19, status: 'Near Limit' },
    { name: 'Dr. Priya Nambiar', role: 'Crisis De-escalation Specialist', capacity: 60, caseload: 12, status: 'Optimal' },
    { name: 'Dr. Meenakshi Sundaram', role: 'State Psychiatric Nodal Officer', capacity: 68, caseload: 13, status: 'Optimal' },
  ];

  const [category, setCategory] = useState(
    caseData?.recommendedIntervention || 'Counselling / psychological support'
  );
  const [primaryAssignee, setPrimaryAssignee] = useState(
    caseData?.primaryAssignee || counsellorsList[0].name
  );
  const [backupAssignee, setBackupAssignee] = useState(
    caseData?.backupAssignee || counsellorsList[1].name
  );
  const [slaHours, setSlaHours] = useState(caseData?.slaHoursRemaining || 4);
  const [status, setStatus] = useState(caseData?.status || 'ASSIGNED');
  const [instructions, setInstructions] = useState('');
  const [escalationContact, setEscalationContact] = useState('South Delhi DM Nodal Cell (+91-11-2953-XXXX)');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!caseData) return null;

  const getCapacityColor = (cap) => {
    if (cap >= 90) return 'var(--ux4g-danger)';
    if (cap >= 75) return 'var(--ux4g-warning)';
    return 'var(--ux4g-success)';
  };

  const selectedPrimary = counsellorsList.find(c => c.name === primaryAssignee) || counsellorsList[0];
  const selectedBackup = counsellorsList.find(c => c.name === backupAssignee) || counsellorsList[1];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const updated = await caseService.assignOfficial(caseData.id, {
        category,
        primaryAssignee,
        backupAssignee,
        slaHours,
        status,
        instructions,
        escalationContact,
      });
      if (onInterventionUpdated) onInterventionUpdated(updated);
      onClose();
    } catch (err) {
      console.error('Assignment error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <UX4GModal
      isOpen={isOpen}
      onClose={onClose}
      title="Intervention Assignment &amp; Routing Suite"
      subtitle={`Case #${caseData.id} • ${caseData.beneficiaryName} • District: ${caseData.district}`}
      maxWidth="680px"
    >
      <form onSubmit={handleSubmit} style={{ padding: '4px 0' }}>
        {/* Section 5 & Rule 5: Human Decision Authority vs AI Recommendation */}
        <div
          style={{
            backgroundColor: 'var(--ux4g-violet-50)',
            border: '1px solid var(--ux4g-violet-200)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 16px',
            marginBottom: '18px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Sparkles size={16} color="var(--ux4g-violet-700)" />
            <strong style={{ fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>
              Algorithmic Advisory Recommendation:
            </strong>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-violet-800)', lineHeight: 1.4, margin: '2px 0 6px 0' }}>
            "{caseData.recommendedIntervention}" (Escalation Probability: {caseData.escalationProbability || '82%'}, Risk: {caseData.riskLevel})
          </p>
          <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', borderTop: '1px dashed var(--ux4g-violet-200)', paddingTop: '6px', marginTop: '6px' }}>
            ⚖️ <strong>Human Decision Authority (Rule 5):</strong> The authorized official possesses exclusive statutory decision authority to assign, re-route, or escalate this intervention.
          </div>
        </div>

        {/* 2-Col Assignee Grid with Live Capacity Indicators */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
          {/* Primary Assignee */}
          <div style={{ padding: '12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
              Primary Assignee *
            </label>
            <select
              value={primaryAssignee}
              onChange={(e) => setPrimaryAssignee(e.target.value)}
              className="ux4g-focus-glow"
              style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.82rem' }}
            >
              {counsellorsList.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.capacity}% - {c.status})
                </option>
              ))}
            </select>
            {/* Live Capacity Meter */}
            <div style={{ marginTop: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '2px' }}>
                <span style={{ color: 'var(--ux4g-text-muted)' }}>Caseload: {selectedPrimary.caseload} active</span>
                <span style={{ fontWeight: 700, color: getCapacityColor(selectedPrimary.capacity) }}>{selectedPrimary.capacity}% capacity</span>
              </div>
              <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--ux4g-border)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${selectedPrimary.capacity}%`, height: '100%', backgroundColor: getCapacityColor(selectedPrimary.capacity) }} />
              </div>
            </div>
          </div>

          {/* Backup Assignee */}
          <div style={{ padding: '12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
              Backup Assignee (Failover SLA) *
            </label>
            <select
              value={backupAssignee}
              onChange={(e) => setBackupAssignee(e.target.value)}
              className="ux4g-focus-glow"
              style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.82rem' }}
            >
              {counsellorsList.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.capacity}% - {c.status})
                </option>
              ))}
            </select>
            {/* Live Capacity Meter */}
            <div style={{ marginTop: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '2px' }}>
                <span style={{ color: 'var(--ux4g-text-muted)' }}>Caseload: {selectedBackup.caseload} active</span>
                <span style={{ fontWeight: 700, color: getCapacityColor(selectedBackup.capacity) }}>{selectedBackup.capacity}% capacity</span>
              </div>
              <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--ux4g-border)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${selectedBackup.capacity}%`, height: '100%', backgroundColor: getCapacityColor(selectedBackup.capacity) }} />
              </div>
            </div>
          </div>
        </div>

        {/* Statutory Category */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
            Statutory Intervention Category (8 Mandated Types)
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="ux4g-focus-glow"
            style={{ width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.85rem' }}
          >
            <option value="Counselling / psychological support">1. Counselling / Psychological Support (Tele-MANAS linkage)</option>
            <option value="Medical treatment / referral">2. Medical Treatment / Psychiatric In-Patient Referral</option>
            <option value="Witness protection">3. Witness &amp; Physical Protection Protocol</option>
            <option value="Relocation / safety support">4. Relocation &amp; Safe Housing Routing</option>
            <option value="Financial / compensation assistance">5. Financial &amp; Statutory Compensation Disbursement</option>
            <option value="Legal aid (NALSA)">6. Judicial Legal Aid (NALSA State Authority Representation)</option>
            <option value="Rehabilitation">7. Comprehensive Socio-Economic Rehabilitation</option>
            <option value="Continued monitoring">8. Continued Longitudinal Baseline Monitoring</option>
          </select>
        </div>

        {/* Statutory SLA Countdown Allocation & Lifecycle Status */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
              Statutory SLA Response Window
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
              {[
                { hours: 2, label: '2h (Emerg.)' },
                { hours: 4, label: '4h (Urgent)' },
                { hours: 24, label: '24h (Std.)' },
                { hours: 48, label: '48h (Rout.)' },
              ].map(item => (
                <button
                  key={item.hours}
                  type="button"
                  onClick={() => setSlaHours(item.hours)}
                  style={{
                    padding: '8px 4px',
                    borderRadius: 'var(--radius-sm)',
                    border: slaHours === item.hours ? '2px solid var(--ux4g-violet-700)' : '1px solid var(--ux4g-border)',
                    backgroundColor: slaHours === item.hours ? 'var(--ux4g-violet-50)' : '#FFF',
                    color: slaHours === item.hours ? 'var(--ux4g-violet-950)' : 'var(--ux4g-text-secondary)',
                    fontWeight: slaHours === item.hours ? 700 : 500,
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    textAlign: 'center',
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
              Intervention Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="ux4g-focus-glow"
              style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.82rem' }}
            >
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="IN_PROGRESS">IN PROGRESS</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="ESCALATED">ESCALATED</option>
            </select>
          </div>
        </div>

        {/* Clinical Action Directives */}
        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
            Clinical Action Directives &amp; Field Instructions
          </label>
          <textarea
            rows={2}
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Specify intervention directives, safe contact parameters, or designated liaison officer instructions..."
            className="ux4g-focus-glow"
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1.5px solid var(--ux4g-border)',
              fontSize: '0.825rem',
              fontFamily: 'inherit',
              resize: 'vertical',
            }}
          />
        </div>

        {/* Escalation Contact */}
        <div style={{ marginBottom: '18px', padding: '8px 12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem' }}>
          <PhoneCall size={14} color="var(--ux4g-danger)" />
          <span style={{ color: 'var(--ux4g-text-secondary)' }}>Escalation Hotline:</span>
          <strong style={{ color: 'var(--ux4g-violet-950)' }}>{escalationContact}</strong>
        </div>

        {/* Modal Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '10px', borderTop: '1px solid var(--ux4g-border)' }}>
          <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
            Cancel
          </UX4GButton>
          <UX4GButton variant="primary" size="md" type="submit" loading={isSubmitting} icon={Shield}>
            Authorize &amp; Dispatch Assignment
          </UX4GButton>
        </div>
      </form>
    </UX4GModal>
  );
};
