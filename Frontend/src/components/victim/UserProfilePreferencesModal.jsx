import React, { useState, useEffect } from 'react';
import { 
  User, 
  ShieldCheck, 
  Clock, 
  Phone, 
  CheckCircle2, 
  Lock, 
  Globe, 
  Bell 
} from 'lucide-react';
import { UX4GModal } from '../common/UX4GModal';
import { UX4GButton } from '../common/UX4GButton';
import { consentService } from '../../services/consentService';
import { useAuth } from '../../context/AuthContext';

export const UserProfilePreferencesModal = ({ isOpen, onClose, onUpdated }) => {
  const { currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'preferences' | 'consent'
  const [prefs, setPrefs] = useState({
    monitoringConsent: true,
    textAnalysisConsent: true,
    voiceAnalysisConsent: true,
    caseLinkageConsent: true,
    safeChannel: 'voice_telemanas',
    safeTimeSlot: '17:00-19:00',
    preferredLanguage: 'Hindi',
    emergencyContact: '+91 98765 43210 (Sister)',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      consentService.getPreferences().then(data => {
        setPrefs(prev => ({ ...prev, ...data }));
        setSavedSuccess(false);
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
      setSavedSuccess(true);
      if (onUpdated) onUpdated(updated);
      setTimeout(() => {
        onClose();
      }, 800);
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
      title="Beneficiary Profile & Preferences"
      subtitle="Confidential settings & DPDP Act 2023 governance panel"
      maxWidth="640px"
    >
      {savedSuccess && (
        <div style={{ backgroundColor: '#DCFCE7', border: '1px solid #86EFAC', borderRadius: 'var(--radius-md)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', color: '#166534', fontSize: '0.85rem', fontWeight: 600 }}>
          <CheckCircle2 size={18} />
          <span>Profile &amp; Preferences successfully updated and securely recorded.</span>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '6px', borderBottom: '1px solid var(--ux4g-border)', marginBottom: '20px' }}>
        {[
          { id: 'profile', label: 'Beneficiary Profile' },
          { id: 'preferences', label: 'Safe Communication' },
          { id: 'consent', label: 'DPDP 2023 Consents' },
        ].map(tab => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 16px',
              border: 'none',
              background: 'transparent',
              fontSize: '0.88rem',
              fontWeight: activeTab === tab.id ? 700 : 500,
              color: activeTab === tab.id ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-secondary)',
              borderBottom: activeTab === tab.id ? '2.5px solid var(--ux4g-violet-700)' : '2.5px solid transparent',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSave}>
        {/* ================= TAB 1: PROFILE ================= */}
        {activeTab === 'profile' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ padding: '14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '1.2rem' }}>
                {currentUser?.name?.charAt(0) || 'M'}
              </div>
              <div>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  {currentUser?.name}
                </h4>
                <div style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                  De-Identified System ID: <strong>BEN-9821-DEL</strong>
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  District Jurisdiction
                </label>
                <input
                  type="text"
                  disabled
                  value="South Delhi, Delhi NCT"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', backgroundColor: 'var(--ux4g-bg)', fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                  Preferred Language
                </label>
                <select
                  value={prefs.preferredLanguage}
                  onChange={(e) => setPrefs(prev => ({ ...prev, preferredLanguage: e.target.value }))}
                  className="ux4g-focus-glow"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.85rem' }}
                >
                  <option value="Hindi">Hindi (हिंदी)</option>
                  <option value="English">English</option>
                  <option value="Punjabi">Punjabi (ਪੰਜਾਬੀ)</option>
                  <option value="Bengali">Bengali (বাংলা)</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.825rem', fontWeight: 600, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                Trusted Emergency SOS Contact
              </label>
              <input
                type="text"
                value={prefs.emergencyContact}
                onChange={(e) => setPrefs(prev => ({ ...prev, emergencyContact: e.target.value }))}
                className="ux4g-focus-glow"
                style={{ width: '100%', padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-border)', fontSize: '0.85rem' }}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>Notified solely if a severe physical safety crisis is reported.</span>
            </div>
          </div>
        )}

        {/* ================= TAB 2: PREFERENCES ================= */}
        {activeTab === 'preferences' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ padding: '12px 14px', backgroundColor: 'var(--ux4g-saffron-50)', border: '1px solid #FDE68A', borderRadius: 'var(--radius-md)', fontSize: '0.825rem', color: '#92400E' }}>
              🛡️ <strong>Safe Hours Guarantee:</strong> Outreach is strictly prohibited outside your designated hours to prevent harassment or unwanted social exposure.
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                Preferred Interaction Modality
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
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
                Daily Safe Hour Window (IST)
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
        )}

        {/* ================= TAB 3: CONSENTS ================= */}
        {activeTab === 'consent' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '8px' }}>
              Under DPDP Act 2023, you retain sovereign ownership over your personal data. Consents can be toggled at any time.
            </p>

            {[
              { key: 'monitoringConsent', label: 'Continuous Well-being Monitoring', desc: 'Allows regular supportive check-ins and longitudinal care by your assigned counsellor.' },
              { key: 'voiceAnalysisConsent', label: 'Speech & Acoustic Analysis', desc: 'Authorizes speech audio processing through sovereign Indian ASR pipelines without external sharing.' },
              { key: 'textAnalysisConsent', label: 'Text & Sentiment Analysis', desc: 'Enables distress trend screening on written check-in responses.' },
              { key: 'caseLinkageConsent', label: 'Statutory Case Linkage', desc: 'Enables updating District Magistrate welfare officers for expedited compensation disbursements.' },
            ].map(item => (
              <div key={item.key} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
                <div>
                  <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>{item.label}</strong>
                  <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>{item.desc}</p>
                </div>
                <input
                  type="checkbox"
                  checked={prefs[item.key]}
                  onChange={() => handleToggle(item.key)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)' }}
                />
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '18px', marginTop: '16px', borderTop: '1px solid var(--ux4g-border)' }}>
          <UX4GButton variant="outline" size="md" onClick={onClose} type="button">
            Cancel
          </UX4GButton>
          <UX4GButton variant="primary" size="md" type="submit" loading={isSaving}>
            Save Changes
          </UX4GButton>
        </div>
      </form>
    </UX4GModal>
  );
};
