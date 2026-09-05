import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Clock, 
  Phone, 
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { consentService } from '../../services/consentService';

export const ConsentPreferencesModal = ({ isOpen, onClose, onPreferencesUpdated }) => {
  const [prefs, setPrefs] = useState({
    monitoringConsent: true,
    textAnalysisConsent: true,
    voiceAnalysisConsent: true,
    caseLinkageConsent: true,
    safeChannel: 'voice_telemanas',
    safeTimeSlot: '17:00-19:00',
    allowEmergencyOutreach: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [showSavedAlert, setShowSavedAlert] = useState(false);

  useEffect(() => {
    if (isOpen) {
      consentService.getPreferences().then(data => {
        setPrefs(data);
        setShowSavedAlert(false);
      });
    }
  }, [isOpen]);

  const handleToggle = (key) => {
    setPrefs(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updated = await consentService.updatePreferences(prefs);
      setShowSavedAlert(true);
      if (onPreferencesUpdated) onPreferencesUpdated(updated);
      setTimeout(() => {
        onClose();
      }, 900);
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
      title="Consent & Communication Preferences"
      subtitle="Digital Personal Data Protection (DPDP Act 2023) Citizen Control Panel"
      maxWidth="620px"
    >
      <form onSubmit={handleSave} style={{ padding: '4px 0' }}>
        {showSavedAlert && (
          <div style={{ backgroundColor: '#DCFCE7', border: '1px solid #86EFAC', borderRadius: 'var(--radius-md)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', color: '#166534', fontSize: '0.85rem', fontWeight: 600 }}>
            <CheckCircle2 size={18} />
            <span>Preferences successfully updated and cryptographically recorded.</span>
          </div>
        )}

        {/* Section 1: Granular Consents */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={18} color="var(--ux4g-violet-700)" />
            <span>1. Granular Data Processing Consents</span>
          </h4>
          <p style="font-size: 0.8rem; color: var(--ux4g-text-secondary); margin-bottom: 14px;">
            You may independently grant or revoke consent for each type of processing without affecting your statutory entitlements.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Monitoring Consent */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div>
                <strong style={{ fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>Continuous Well-being Monitoring</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Allows regular supportive check-ins and recovery tracking by your counsellor.</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.monitoringConsent}
                onChange={() => handleToggle('monitoringConsent')}
                style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)' }}
              />
            </div>

            {/* Voice Analysis Consent */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div>
                <strong style={{ fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>Speech & Acoustic Analysis Consent</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Authorizes speech audio processing through sovereign Indian ASR pipelines.</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.voiceAnalysisConsent}
                onChange={() => handleToggle('voiceAnalysisConsent')}
                style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)' }}
              />
            </div>

            {/* Case Linkage Consent */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
              <div>
                <strong style={{ fontSize: '0.85rem', color: 'var(--ux4g-violet-950)' }}>Statutory Case Linkage Consent</strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Enables linking clinical updates to the District Magistrate welfare officer for relief disbursal.</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.caseLinkageConsent}
                onChange={() => handleToggle('caseLinkageConsent')}
                style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)' }}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Safe Channel & Time Preferences */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={18} color="var(--ux4g-violet-700)" />
            <span>2. Safe Communication Windows & Channels</span>
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)', marginBottom: '14px' }}>
            To protect your privacy and peace of mind, outreach is strictly restricted to your designated time windows.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, marginBottom: '6px' }}>
                Preferred Channel
              </label>
              <select
                value={prefs.safeChannel}
                onChange={(e) => setPrefs(prev => ({ ...prev, safeChannel: e.target.value }))}
                className="ux4g-focus-glow"
                style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.88rem' }}
              >
                <option value="voice_telemanas">Voice Call via Tele-MANAS (14416)</option>
                <option value="in_app_text">In-App Confidential Text Form</option>
                <option value="whatsapp_secure">Secure WhatsApp Outreach</option>
                <option value="sms_only">Simple SMS Reminder</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, marginBottom: '6px' }}>
                Safe Time Window (IST)
              </label>
              <select
                value={prefs.safeTimeSlot}
                onChange={(e) => setPrefs(prev => ({ ...prev, safeTimeSlot: e.target.value }))}
                className="ux4g-focus-glow"
                style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.88rem' }}
              >
                <option value="10:00-12:00">Morning (10:00 AM – 12:00 PM)</option>
                <option value="14:00-16:00">Afternoon (02:00 PM – 04:00 PM)</option>
                <option value="17:00-19:00">Early Evening (05:00 PM – 07:00 PM)</option>
                <option value="19:00-21:00">Late Evening (07:00 PM – 09:00 PM)</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '12px', borderTop: '1px solid var(--ux4g-border)' }}>
          <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
            Cancel
          </UX4GButton>
          <UX4GButton variant="primary" size="md" type="submit" loading={isSaving}>
            Save Preferences
          </UX4GButton>
        </div>
      </form>
    </UX4GModal>
  );
};
