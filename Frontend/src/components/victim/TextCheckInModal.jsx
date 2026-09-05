import React, { useState } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Send, 
  ShieldCheck,
  Smile,
  Meh,
  Frown,
  AlertCircle
} from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { interactionService } from '../../services/interactionService';

export const TextCheckInModal = ({ isOpen, onClose, onSuccess }) => {
  const [mood, setMood] = useState('steady');
  const [sleepQuality, setSleepQuality] = useState('fair');
  const [safetyFeeling, setSafetyFeeling] = useState('safe');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await interactionService.submitTextCheckIn({
        mood,
        sleepQuality,
        safetyFeeling,
        notes,
      });
      setConfirmation(res);
      if (onSuccess) onSuccess(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetAndClose = () => {
    setConfirmation(null);
    setNotes('');
    onClose();
  };

  return (
    <UX4GModal
      isOpen={isOpen}
      onClose={handleResetAndClose}
      title="Written Text Check-In"
      subtitle="Confidential emotional check-in form for your care team"
      maxWidth="540px"
    >
      {confirmation ? (
        <div style={{ textAlign: 'center', padding: '24px 16px' }}>
          <div style={{ width: '60px', height: '60px', borderRadius: '50%', backgroundColor: '#DCFCE7', color: '#15803D', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <CheckCircle2 size={32} />
          </div>

          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#14532D', marginBottom: '8px' }}>
            Check-In Received Safely
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-secondary)', marginBottom: '20px', lineHeight: 1.6 }}>
            {confirmation.message}
          </p>

          <div style={{ backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-md)', padding: '12px 16px', maxWidth: '360px', margin: '0 auto 24px', textAlign: 'left', fontSize: '0.825rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ color: 'var(--ux4g-text-muted)' }}>Reference:</span>
              <strong>{confirmation.referenceId}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--ux4g-text-muted)' }}>Status:</span>
              <span className="ux4g-badge ux4g-badge-low">Confidential & Stored</span>
            </div>
          </div>

          <UX4GButton variant="primary" size="md" onClick={handleResetAndClose}>
            Back to My Care Space
          </UX4GButton>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ padding: '4px 0' }}>
          {/* Mood Selection */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
              1. How are you feeling today overall?
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {[
                { id: 'calm', label: 'Calm & Steady', icon: Smile, color: '#10B981' },
                { id: 'anxious', label: 'Anxious / Uneasy', icon: Meh, color: '#F59E0B' },
                { id: 'heavy', label: 'Heavy / Overwhelmed', icon: Frown, color: '#EF4444' },
              ].map(item => {
                const IconComponent = item.icon;
                const isSelected = mood === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setMood(item.id)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '12px 8px',
                      borderRadius: 'var(--radius-md)',
                      border: isSelected ? '2px solid var(--ux4g-violet-700)' : '1px solid var(--ux4g-border)',
                      backgroundColor: isSelected ? 'var(--ux4g-violet-50)' : '#FFF',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <IconComponent size={22} color={item.color} />
                    <span style={{ fontSize: '0.78rem', fontWeight: isSelected ? 700 : 500, color: 'var(--ux4g-text-primary)' }}>
                      {item.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sleep Quality */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
              2. How was your sleep last night?
            </label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {['Rested (6+ hrs)', 'Disturbed / Broken', 'Hardly slept'].map(option => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setSleepQuality(option)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-full)',
                    border: sleepQuality === option ? '1.5px solid var(--ux4g-violet-700)' : '1px solid var(--ux4g-border)',
                    backgroundColor: sleepQuality === option ? 'var(--ux4g-violet-50)' : '#FFF',
                    fontSize: '0.825rem',
                    fontWeight: sleepQuality === option ? 700 : 500,
                    color: sleepQuality === option ? 'var(--ux4g-violet-900)' : 'var(--ux4g-text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Thoughts / Notes */}
          <div style={{ marginBottom: '22px' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
              3. Anything you would like your counsellor to know? (Optional)
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Write your thoughts here in confidence..."
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

          {/* Privacy footnote */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
            <ShieldCheck size={16} color="var(--ux4g-violet-700)" />
            <span>Encrypted under DPDP Act 2023. Seen solely by your assigned counsellor.</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
              Cancel
            </UX4GButton>
            <UX4GButton variant="primary" size="md" icon={Send} type="submit" loading={isSubmitting}>
              Submit Check-In
            </UX4GButton>
          </div>
        </form>
      )}
    </UX4GModal>
  );
};
