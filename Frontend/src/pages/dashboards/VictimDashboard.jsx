import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Heart, 
  Mic, 
  MessageSquare, 
  Calendar, 
  ShieldCheck, 
  CheckCircle2, 
  PhoneCall, 
  UserCheck, 
  Lock,
  Clock,
  Sparkles,
  Sliders,
  Bell,
  User,
  Shield,
  FileCheck2,
  AlertCircle,
  X,
  Volume2,
  FileText,
  HelpCircle,
  Download,
  AlertTriangle,
  Scale
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { DashboardShell } from './DashboardShell';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GButton } from '../../components/common/UX4GButton';
import { UX4GTable } from '../../components/common/UX4GTable';
import { UX4GOffcanvas } from '../../components/common/UX4GOffcanvas';
import { VoiceCheckInModal } from '../../components/victim/VoiceCheckInModal';
import { TextCheckInModal } from '../../components/victim/TextCheckInModal';
import { ConsentPreferencesModal } from '../../components/victim/ConsentPreferencesModal';
import { UserProfilePreferencesModal } from '../../components/victim/UserProfilePreferencesModal';
import { PersonalTrendCard } from '../../components/victim/PersonalTrendCard';
import { consentService } from '../../services/consentService';

export const VictimDashboard = () => {
  const { currentUser } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const handleTabChange = (tabId) => {
    setSearchParams({ tab: tabId });
  };
  
  // Modals state
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [textModalOpen, setTextModalOpen] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  
  // Beneficiary preferences & history state
  const [preferences, setPreferences] = useState({
    monitoringConsent: true,
    textAnalysisConsent: true,
    voiceAnalysisConsent: true,
    caseLinkageConsent: true,
    safeChannel: 'voice_telemanas',
    safeTimeSlot: '17:00-19:00',
    allowEmergencyOutreach: true,
  });
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Notifications
  const [notifications, setNotifications] = useState([
    {
      id: 'notif-1',
      title: 'Safe Check-In Window Active',
      message: 'Your safe 2-hour check-in window (17:00 – 19:00 IST) is open. You may submit a 2-minute voice or text check-in.',
      time: '15 mins ago',
      category: 'WINDOW',
      read: false,
    },
    {
      id: 'notif-2',
      title: 'Counsellor Review Completed',
      message: 'Dr. Rajesh Verma (Tele-MANAS) reviewed your encrypted check-in #CHK-VOX-982103. Longitudinal stability confirmed.',
      time: '2 hours ago',
      category: 'CLINICAL',
      read: false,
    },
    {
      id: 'notif-3',
      title: 'Statutory Relief Progress',
      message: 'Phase-1 financial assistance verification under SC/ST PoA Rule 12(4) forwarded to South Delhi District Magistrate Cell.',
      time: 'Yesterday',
      category: 'STATUTORY',
      read: true,
    },
    {
      id: 'notif-4',
      title: 'DPDP 2023 Consent Audit',
      message: 'All biometric speech samples and psychological evaluations stored in encrypted cold storage with strict RBAC.',
      time: '3 days ago',
      category: 'SECURITY',
      read: true,
    },
  ]);

  const [recentCheckIns, setRecentCheckIns] = useState([
    { id: 'CHK-VOX-982103', date: 'Yesterday, 05:30 PM', channel: 'Spoken Audio (Voice)', language: 'Hindi', status: 'Logged & Encrypted', confirmed: true },
    { id: 'CHK-VOX-982098', date: '27 Aug 2026, 05:45 PM', channel: 'Spoken Audio (Voice)', language: 'Hindi', status: 'Logged & Encrypted', confirmed: true },
    { id: 'CHK-TXT-982042', date: '20 Aug 2026, 04:45 PM', channel: 'Written Form (Text)', language: 'Hindi / English', status: 'Logged & Encrypted', confirmed: true },
  ]);

  // Support request state
  const [supportMessage, setSupportMessage] = useState('');
  const [supportSent, setSupportSent] = useState(false);

  useEffect(() => {
    consentService.getPreferences().then(data => {
      if (data) setPreferences(data);
    });
  }, []);

  const handleVoiceSuccess = (res) => {
    const newEntry = {
      id: res.referenceId,
      date: 'Just Now',
      channel: `Spoken Audio (${res.languageDetected || 'Voice'})`,
      language: res.languageDetected || 'Hindi',
      status: 'Logged & Encrypted',
      confirmed: true,
    };
    setRecentCheckIns(prev => [newEntry, ...prev]);
  };

  const handleTextSuccess = (res) => {
    const newEntry = {
      id: res.referenceId,
      date: 'Just Now',
      channel: 'Written Form (Text)',
      language: 'English / Hindi',
      status: 'Logged & Encrypted',
      confirmed: true,
    };
    setRecentCheckIns(prev => [newEntry, ...prev]);
  };

  const handleSavePreferences = async (e) => {
    e?.preventDefault();
    try {
      const updated = await consentService.updatePreferences(preferences);
      setPreferences(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendSupportMessage = (e) => {
    e.preventDefault();
    if (!supportMessage.trim()) return;
    setSupportSent(true);
    setSupportMessage('');
    setTimeout(() => setSupportSent(false), 4000);
  };

  const historyColumns = [
    {
      header: 'Interaction ID',
      key: 'id',
      render: (_, row) => (
        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--ux4g-violet-950)', fontSize: '0.85rem' }}>
          {row.id}
        </span>
      ),
    },
    {
      header: 'Date & Time',
      key: 'date',
      render: (_, row) => (
        <span style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)' }}>
          {row.date}
        </span>
      ),
    },
    {
      header: 'Modality',
      key: 'channel',
      render: (_, row) => {
        const isVoice = row.channel.includes('Voice') || row.channel.includes('Audio');
        return (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem', color: 'var(--ux4g-text-primary)' }}>
            {isVoice ? (
              <Mic size={14} color="var(--ux4g-violet-700)" />
            ) : (
              <MessageSquare size={14} color="var(--ux4g-violet-700)" />
            )}
            <span>{isVoice ? 'Voice Audio' : 'Written Form'}</span>
          </div>
        );
      },
    },
    {
      header: 'Security Status',
      key: 'status',
      render: (_, row) => (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', color: 'var(--ux4g-success-text)', fontSize: '0.8rem', fontWeight: 600 }}>
          <CheckCircle2 size={13} />
          <span>Encrypted</span>
        </div>
      ),
    },
  ];

  return (
    <DashboardShell
      title={`Namaste, ${currentUser?.name}`}
      subtitle="Beneficiary Care & Mental Health Monitoring Portal • Department of Social Justice & Empowerment"
      activeTab={activeTab}
      onTabChange={handleTabChange}
    >
      {/* =========================================================================
          TAB 1: MY CARE SPACE (OVERVIEW)
          ========================================================================= */}
      {activeTab === 'overview' && (
        <>
          {/* 1. Formal Care & Daily Check-In Action Center */}
          <div
            style={{
              backgroundColor: 'var(--ux4g-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-border)',
              padding: '20px 24px',
              marginBottom: '20px',
              boxShadow: 'var(--elevation-1)',
            }}
          >
            {/* Top Operational Status Bar */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
                paddingBottom: '16px',
                borderBottom: '1px solid var(--ux4g-border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span className="ux4g-badge ux4g-badge-low">
                  <ShieldCheck size={13} />
                  DPDP Act 2023 Protected
                </span>
                <span style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <Clock size={13} color="var(--ux4g-text-muted)" />
                  Daily Safe Window: <strong style={{ color: 'var(--ux4g-violet-950)' }}>{preferences?.safeTimeSlot ? `${preferences.safeTimeSlot.replace('-', ' – ')} IST` : '17:00 – 19:00 IST'}</strong>
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                  • South Delhi Atrocity Monitoring Unit
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setNotificationsOpen(true)}
                  className="ux4g-focus-glow"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--ux4g-border)',
                    backgroundColor: 'var(--ux4g-surface)',
                    color: 'var(--ux4g-text-primary)',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                  aria-label="View notifications"
                >
                  <Bell size={14} color="var(--ux4g-violet-700)" />
                  <span>Notifications</span>
                  {notifications.filter(n => !n.read).length > 0 && (
                    <span
                      style={{
                        backgroundColor: 'var(--ux4g-danger)',
                        color: '#FFF',
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        borderRadius: '8px',
                        padding: '0 6px',
                        lineHeight: '1.3',
                      }}
                    >
                      {notifications.filter(n => !n.read).length}
                    </span>
                  )}
                </button>

                <UX4GButton
                  variant="outline"
                  size="sm"
                  icon={Sliders}
                  onClick={() => handleTabChange('consent')}
                >
                  Preferences &amp; Consents
                </UX4GButton>
              </div>
            </div>

            {/* Check-In Primary Action Area */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '16px',
                paddingTop: '16px',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.08rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Submit Daily Check-In
                </h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                  Select your preferred modality. Audio check-ins are processed securely in under 2 minutes.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <UX4GButton
                  variant="primary"
                  size="sm"
                  icon={Mic}
                  onClick={() => setVoiceModalOpen(true)}
                >
                  Voice Check-In
                </UX4GButton>

                <UX4GButton
                  variant="outline"
                  size="sm"
                  icon={MessageSquare}
                  onClick={() => setTextModalOpen(true)}
                >
                  Written Form
                </UX4GButton>
              </div>
            </div>
          </div>

          {/* 2. Statutory Multi-Agency Support Strip (Clean 4-Column Bar) */}
          <div
            style={{
              backgroundColor: 'var(--ux4g-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-border)',
              padding: '16px 20px',
              marginBottom: '22px',
              boxShadow: 'var(--elevation-1)',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              {/* Pillar 1: Clinical Support */}
              <div style={{ paddingRight: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Clinical Support</span>
                  <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Assigned</span>
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>Dr. Rajesh Verma</div>
                <div style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                  Clinical Lead • <a href="tel:14416" style={{ color: 'var(--ux4g-violet-700)', textDecoration: 'none', fontWeight: 600 }}>Tele-MANAS (14416)</a>
                </div>
              </div>

              {/* Pillar 2: Legal Aid */}
              <div style={{ paddingRight: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Legal Counsel</span>
                  <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Appointed</span>
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>Adv. Priya Malhotra</div>
                <div style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                  DLSA Retainer • FIR #312/2026
                </div>
              </div>

              {/* Pillar 3: Statutory Relief */}
              <div style={{ paddingRight: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Statutory Relief</span>
                  <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Phase 1 Done</span>
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>₹1,50,000 Interim Relief</div>
                <div style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                  SC/ST PoA Rule 12(4) Disbursed
                </div>
              </div>

              {/* Pillar 4: Safe Outreach Policy */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Privacy Protocol</span>
                  <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>Enforced</span>
                </div>
                <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>Zero-Outreach Rule</div>
                <div style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                  Strictly prohibited outside safe slot
                </div>
              </div>
            </div>
          </div>

          {/* 3. Primary Workspace: Check-In Records & Recovery Milestones */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '22px', marginBottom: '28px' }}>
            {/* Recent Check-In Records Table */}
            <UX4GCard elevation={1} liftOnHover={false} style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '14px', borderBottom: '1px solid var(--ux4g-border-subtle)' }}>
                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    Recent Check-In Records
                  </h4>
                  <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)' }}>
                    Immutable audit history protected under DPDP Act 2023
                  </p>
                </div>
                <span className="ux4g-badge ux4g-badge-primary">
                  <Lock size={12} />
                  256-Bit Encrypted
                </span>
              </div>

              <UX4GTable
                columns={historyColumns}
                data={recentCheckIns}
                caption="Recent check-in interactions log"
              />
            </UX4GCard>

            {/* Longitudinal Recovery Stepper */}
            <PersonalTrendCard />
          </div>
        </>
      )}

      {/* =========================================================================
          TAB 2: CHECK-IN & VOICE (MULTIMODAL WORKFLOW)
          ========================================================================= */}
      {activeTab === 'checkin' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Active Safe Window Header */}
          <div style={{ backgroundColor: 'var(--ux4g-violet-100)', border: '2px solid #3A2312', boxShadow: '3px 3px 0px #3A2312', borderRadius: 'var(--radius-md)', padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span className="ux4g-badge ux4g-badge-low">
                  <CheckCircle2 size={13} /> Safe Window Active Now
                </span>
                <span style={{ fontSize: '0.82rem', color: 'var(--ux4g-violet-800)', fontWeight: 700 }}>
                  17:00 – 19:00 IST • DPDP Consent Verified
                </span>
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                Multimodal Psychological Check-In Console
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                Submit your encrypted, self-paced check-in via spoken voice or confidential text form.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>Assigned Nodal Officer</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  South Delhi District Cell
                </div>
              </div>
            </div>
          </div>

          {/* Dual Check-in Modalities Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '22px' }}>
            {/* Spoken Voice Check-in Card */}
            <UX4GCard elevation={1} padding="24px">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ width: '44px', height: '44px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Mic size={24} />
                </div>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    Spoken Voice Check-In
                  </h4>
                  <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
                    Primary Modality • 22 Scheduled Indian Languages
                  </p>
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--ux4g-bg)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', marginBottom: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Audio Encryption:</span>
                  <span style={{ color: 'var(--ux4g-success-text)', fontWeight: 700 }}>AES-256 GCM (At Rest)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Acoustic Processing:</span>
                  <span style={{ color: 'var(--ux4g-violet-900)', fontWeight: 600 }}>Sovereign Indian Server</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Target Duration:</span>
                  <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600 }}>60 – 120 seconds</span>
                </div>
              </div>

              <UX4GButton variant="primary" size="md" icon={Mic} fullWidth onClick={() => setVoiceModalOpen(true)}>
                Launch Interactive Audio Recorder
              </UX4GButton>
            </UX4GCard>

            {/* Written Text Check-in Card */}
            <UX4GCard elevation={1} padding="24px">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ width: '44px', height: '44px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <MessageSquare size={24} />
                </div>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                    Written Psychological Form
                  </h4>
                  <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
                    Alternate Modality • Form-based linguistic check-in
                  </p>
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--ux4g-bg)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border-subtle)', marginBottom: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Linguistic Parser:</span>
                  <span style={{ color: 'var(--ux4g-success-text)', fontWeight: 700 }}>Ready (Hindi &amp; English)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Estimated Time:</span>
                  <span style={{ color: 'var(--ux4g-violet-900)', fontWeight: 600 }}>&lt; 2 minutes</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Counsellor Notification:</span>
                  <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600 }}>Instant Triage Forwarding</span>
                </div>
              </div>

              <UX4GButton variant="outline" size="md" icon={MessageSquare} fullWidth onClick={() => setTextModalOpen(true)}>
                Fill Written Check-In
              </UX4GButton>
            </UX4GCard>
          </div>

          {/* Full Audit History Table */}
          <UX4GCard elevation={1} padding="24px">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--ux4g-border-subtle)' }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                  Complete Interaction Audit Trail
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-muted)' }}>
                  All historical audio and written check-ins logged under DPDP Act 2023 with cryptographic verification.
                </p>
              </div>
              <span className="ux4g-badge ux4g-badge-low">
                <CheckCircle2 size={13} /> {recentCheckIns.length} Verified Records
              </span>
            </div>

            <UX4GTable columns={historyColumns} data={recentCheckIns} caption="Detailed interaction history log" />
          </UX4GCard>
        </div>
      )}

      {/* =========================================================================
          TAB 3: CONSENT & PRIVACY (DPDP ACT 2023 CITIZEN CONTROL)
          ========================================================================= */}
      {activeTab === 'consent' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {saveSuccess && (
            <div style={{ backgroundColor: 'var(--ux4g-success-bg)', border: '1.5px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-md)', padding: '14px 20px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--ux4g-success-text)', fontWeight: 700 }}>
              <CheckCircle2 size={18} />
              <span>Preferences and DPDP Act 2023 consents have been securely updated and cryptographically recorded.</span>
            </div>
          )}

          {/* DPDP Header Banner */}
          <div style={{ backgroundColor: 'var(--ux4g-surface)', border: '2px solid #3A2312', boxShadow: 'var(--elevation-2)', borderRadius: 'var(--radius-md)', padding: '22px 26px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <ShieldCheck size={20} color="var(--ux4g-violet-700)" />
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Statutory Data Governance
                  </span>
                </div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  Consent &amp; Privacy Preferences
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px', maxWidth: '680px' }}>
                  Under the <strong>Digital Personal Data Protection (DPDP) Act 2023</strong>, you hold unconditional rights over your psychological evaluations and personal data. You can independently toggle permissions or modify your safe communication slots at any time.
                </p>
              </div>

              <UX4GButton variant="primary" size="md" icon={CheckCircle2} onClick={handleSavePreferences}>
                Save Preferences
              </UX4GButton>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '22px' }}>
            {/* 1. Granular Consent Toggles */}
            <UX4GCard elevation={1} padding="24px">
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={18} color="var(--ux4g-violet-700)" />
                1. Granular Data Processing Consents
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <label style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', cursor: 'pointer' }}>
                  <div style={{ paddingRight: '12px' }}>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>Continuous Well-being Monitoring</strong>
                    <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Allows regular supportive check-ins and recovery tracking by assigned counsellor.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.monitoringConsent}
                    onChange={(e) => setPreferences({ ...preferences, monitoringConsent: e.target.checked })}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)', marginTop: '3px' }}
                  />
                </label>

                <label style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', cursor: 'pointer' }}>
                  <div style={{ paddingRight: '12px' }}>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>Speech Acoustic Analysis</strong>
                    <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Extracts vocal tone, pitch, and speech cadence to detect escalating distress.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.voiceAnalysisConsent}
                    onChange={(e) => setPreferences({ ...preferences, voiceAnalysisConsent: e.target.checked })}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)', marginTop: '3px' }}
                  />
                </label>

                <label style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', cursor: 'pointer' }}>
                  <div style={{ paddingRight: '12px' }}>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>Text &amp; Semantic Analysis</strong>
                    <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Analyzes linguistic cues and feelings from written entries for fear indicators.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.textAnalysisConsent}
                    onChange={(e) => setPreferences({ ...preferences, textAnalysisConsent: e.target.checked })}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)', marginTop: '3px' }}
                  />
                </label>

                <label style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '12px 14px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', cursor: 'pointer' }}>
                  <div style={{ paddingRight: '12px' }}>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>SC/ST PoA Case Linkage</strong>
                    <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>Links check-in history to legal aid and statutory relief file (FIR #312/2026).</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.caseLinkageConsent}
                    onChange={(e) => setPreferences({ ...preferences, caseLinkageConsent: e.target.checked })}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--ux4g-violet-700)', marginTop: '3px' }}
                  />
                </label>
              </div>
            </UX4GCard>

            {/* 2. Safe Channel & Safe Time Window */}
            <UX4GCard elevation={1} padding="24px">
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={18} color="var(--ux4g-violet-700)" />
                2. Safe Outreach &amp; Timing Rules
              </h4>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ux4g-text-primary)', marginBottom: '6px' }}>
                    Preferred Communication Channel:
                  </label>
                  <select
                    value={preferences.safeChannel}
                    onChange={(e) => setPreferences({ ...preferences, safeChannel: e.target.value })}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.88rem', backgroundColor: 'var(--ux4g-surface)' }}
                  >
                    <option value="voice_telemanas">In-App Web Portal Only (Most Confidential)</option>
                    <option value="sms_encrypted">Encrypted SMS (Pre-approved text alerts)</option>
                    <option value="whatsapp">Government WhatsApp Care Line</option>
                  </select>
                  <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)', marginTop: '4px' }}>
                    Counsellors will NEVER contact you through unapproved channels.
                  </p>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--ux4g-text-primary)', marginBottom: '6px' }}>
                    Daily Safe Contact Time Window:
                  </label>
                  <select
                    value={preferences.safeTimeSlot}
                    onChange={(e) => setPreferences({ ...preferences, safeTimeSlot: e.target.value })}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.88rem', backgroundColor: 'var(--ux4g-surface)' }}
                  >
                    <option value="17:00-19:00">17:00 – 19:00 IST (Evening Safe Window - Active)</option>
                    <option value="10:00-12:00">10:00 – 12:00 IST (Morning Safe Window)</option>
                    <option value="14:00-16:00">14:00 – 16:00 IST (Afternoon Safe Window)</option>
                  </select>
                  <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)', marginTop: '4px' }}>
                    The <strong>Zero-Outreach Rule</strong> strictly blocks all outbound communications outside this chosen slot.
                  </p>
                </div>

                {/* DPDP Statutory Rights Box */}
                <div style={{ backgroundColor: 'var(--ux4g-violet-100)', border: '1.5px solid #3A2312', borderRadius: 'var(--radius-sm)', padding: '12px 14px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '4px' }}>
                    Statutory Data Principal Rights:
                  </div>
                  <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.76rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.5 }}>
                    <li>Right to access personal summary records at any time</li>
                    <li>Right to immediate consent withdrawal without loss of benefits</li>
                    <li>Automated erasure of raw audio upon clinical review completion</li>
                  </ul>
                </div>
              </div>
            </UX4GCard>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 4: SUPPORT & COUNSELLOR (HUMAN-IN-THE-LOOP CLINICAL CARE)
          ========================================================================= */}
      {activeTab === 'support' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {/* Top Support Banner */}
          <div style={{ backgroundColor: 'var(--ux4g-surface)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-md)', padding: '22px 26px', boxShadow: 'var(--elevation-1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <span className="ux4g-badge ux4g-badge-low" style={{ marginBottom: '6px' }}>
                  <UserCheck size={13} /> Dedicated Clinical Triage Team
                </span>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}>
                  Assigned Care &amp; Rehabilitation Network
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginTop: '4px', maxWidth: '680px' }}>
                  Under AAROH's Human-Centered Care doctrine, AI models only provide risk indicators. All counseling, legal aid, and financial relief actions are taken directly by certified government officials.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <a href="tel:14416" style={{ textDecoration: 'none' }}>
                  <UX4GButton variant="primary" size="md" icon={PhoneCall}>
                    Call Tele-MANAS (14416)
                  </UX4GButton>
                </a>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '22px' }}>
            {/* Assigned Clinical Counsellor Dossier */}
            <UX4GCard elevation={1} padding="24px">
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '18px', paddingBottom: '14px', borderBottom: '1px solid var(--ux4g-border-subtle)' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--ux4g-violet-700)', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', fontWeight: 700 }}>
                  RV
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                      Dr. Rajesh Verma
                    </h4>
                    <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.7rem' }}>Lead Clinical Lead</span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>
                    Tele-MANAS Regional Centre • License #GOV-CNS-4402
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.84rem', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Assigned Jurisdiction:</span>
                  <strong style={{ color: 'var(--ux4g-violet-950)' }}>South Delhi Atrocity Unit</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Next Scheduled Consultation:</span>
                  <strong style={{ color: 'var(--ux4g-violet-700)' }}>Tomorrow at 17:30 IST</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--ux4g-text-secondary)' }}>Clinical Grounding Protocol:</span>
                  <strong style={{ color: 'var(--ux4g-success)' }}>Trauma &amp; Anxiety Relief</strong>
                </div>
              </div>

              {/* Message Counsellor Form */}
              <form onSubmit={handleSendSupportMessage}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--ux4g-text-primary)', marginBottom: '6px' }}>
                  Leave a Confidential Message for Dr. Rajesh:
                </label>
                <textarea
                  rows="3"
                  value={supportMessage}
                  onChange={(e) => setSupportMessage(e.target.value)}
                  placeholder="Describe your current concern or request an earlier consultation slot..."
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--ux4g-border)', fontSize: '0.85rem', marginBottom: '10px', resize: 'vertical' }}
                />
                {supportSent && (
                  <div style={{ color: 'var(--ux4g-success)', fontSize: '0.8rem', fontWeight: 600, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle2 size={14} /> Message encrypted and forwarded to Dr. Rajesh.
                  </div>
                )}
                <UX4GButton variant="primary" size="sm" icon={MessageSquare} fullWidth type="submit">
                  Send Secure Note
                </UX4GButton>
              </form>
            </UX4GCard>

            {/* Legal Counsel & Statutory Relief Details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Legal Aid Box */}
              <UX4GCard elevation={1} padding="22px">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <Scale size={20} color="var(--ux4g-violet-700)" />
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                      Adv. Priya Malhotra (DLSA Retainer)
                    </h4>
                    <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)' }}>
                      Delhi State Legal Services Authority • Free Legal Counsel
                    </p>
                  </div>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.5, backgroundColor: 'var(--ux4g-bg)', padding: '10px 12px', borderRadius: 'var(--radius-sm)' }}>
                  Attached to FIR #312/2026. Free legal representation and witness protection advocate provided under Section 15A of SC/ST (PoA) Act.
                </div>
              </UX4GCard>

              {/* Statutory Relief Stepper Box */}
              <UX4GCard elevation={1} padding="22px">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                  <FileCheck2 size={20} color="var(--ux4g-success)" />
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                      Statutory Compensation Entitlement
                    </h4>
                    <p style={{ fontSize: '0.76rem', color: 'var(--ux4g-text-muted)' }}>
                      SC/ST PoA Amendment Rules 2016 • Annexure I Relief
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: 'var(--ux4g-success-bg)', border: '1px solid var(--ux4g-success-border)', borderRadius: 'var(--radius-sm)' }}>
                    <div>
                      <strong style={{ fontSize: '0.82rem', color: 'var(--ux4g-success-text)' }}>Stage 1: ₹1,50,000 (Interim)</strong>
                      <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-secondary)' }}>Direct DBT Aadhaar transfer completed</div>
                    </div>
                    <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.68rem' }}>Disbursed</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-sm)' }}>
                    <div>
                      <strong style={{ fontSize: '0.82rem', color: 'var(--ux4g-violet-950)' }}>Stage 2: ₹3,50,000 (Chargesheet)</strong>
                      <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>Pending DM verification &amp; police filing</div>
                    </div>
                    <span className="ux4g-badge ux4g-badge-medium" style={{ fontSize: '0.68rem' }}>In Verification</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: 'var(--ux4g-bg)', border: '1px solid var(--ux4g-border)', borderRadius: 'var(--radius-sm)' }}>
                    <div>
                      <strong style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)' }}>Stage 3: ₹3,25,000 (Trial Conclusion)</strong>
                      <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>Final statutory rehabilitation release</div>
                    </div>
                    <span className="ux4g-badge" style={{ fontSize: '0.68rem' }}>Scheduled</span>
                  </div>
                </div>
              </UX4GCard>

              {/* 24x7 Helplines Box */}
              <div style={{ backgroundColor: '#FFFBEB', border: '1px solid #FCD34D', borderRadius: 'var(--radius-md)', padding: '14px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <PhoneCall size={18} color="#D97706" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#92400E' }}>24x7 National Emergency Hotlines</div>
                    <div style={{ fontSize: '0.76rem', color: '#B45309' }}>Tele-MANAS: 14416 • Atrocity Helpline: 14566 • Women Helpline: 1091</div>
                  </div>
                </div>
                <a href="tel:14416" style={{ textDecoration: 'none' }}>
                  <UX4GButton variant="outline" size="sm">Call 14416</UX4GButton>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODALS & NOTIFICATIONS DRAWER */}
      <VoiceCheckInModal
        isOpen={voiceModalOpen}
        onClose={() => setVoiceModalOpen(false)}
        onSwitchToText={() => {
          setVoiceModalOpen(false);
          setTextModalOpen(true);
        }}
        onSuccess={handleVoiceSuccess}
      />

      <TextCheckInModal
        isOpen={textModalOpen}
        onClose={() => setTextModalOpen(false)}
        onSuccess={handleTextSuccess}
      />

      <UserProfilePreferencesModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        onUpdated={(updated) => setPreferences(updated)}
      />

      {/* Notifications Slide Drawer */}
      <UX4GOffcanvas
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        title="Beneficiary Notifications & Updates"
        subtitle="Confidential notices, review alerts & statutory milestones"
        position="right"
        width="460px"
      >
        <div style={{ padding: '4px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
              {notifications.filter(n => !n.read).length} unread notices
            </span>
            {notifications.some(n => !n.read) && (
              <button
                type="button"
                onClick={() => setNotifications(prev => prev.map(n => ({ ...n, read: true })))}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--ux4g-violet-700)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Mark all as read
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: n.read ? 'var(--ux4g-surface)' : 'var(--ux4g-violet-100)',
                  border: n.read ? '1.5px solid #3A2312' : '2px solid #3A2312',
                  boxShadow: n.read ? '2px 2px 0px #3A2312' : '3px 3px 0px #3A2312',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {!n.read && (
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--ux4g-violet-700)', display: 'inline-block' }} />
                    )}
                    <strong style={{ fontSize: '0.9rem', color: 'var(--ux4g-violet-950)' }}>
                      {n.title}
                    </strong>
                  </div>
                  <button
                    type="button"
                    onClick={() => setNotifications(prev => prev.filter(item => item.id !== n.id))}
                    style={{ background: 'none', border: 'none', color: 'var(--ux4g-text-muted)', cursor: 'pointer', padding: '2px' }}
                    title="Dismiss notification"
                  >
                    <X size={14} />
                  </button>
                </div>

                <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.45, marginBottom: '8px' }}>
                  {n.message}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>
                  <span>{n.time}</span>
                  <span className="ux4g-badge ux4g-badge-primary" style={{ fontSize: '0.7rem' }}>
                    {n.category}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </UX4GOffcanvas>
    </DashboardShell>
  );
};
