import React, { useState, useEffect } from 'react';
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
  X
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
  
  // Modals state
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [textModalOpen, setTextModalOpen] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  
  // Beneficiary preferences & history state
  const [preferences, setPreferences] = useState(null);
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

  useEffect(() => {
    consentService.getPreferences().then(data => setPreferences(data));
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
              <MessageSquare size={14} color="#0284C7" />
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
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', color: '#15803D', fontSize: '0.8rem', fontWeight: 500 }}>
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
    >
      {/* 1. Formal Care & Daily Check-In Action Center */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
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
                backgroundColor: '#FFFFFF',
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
              onClick={() => setProfileModalOpen(true)}
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
          backgroundColor: '#FFFFFF',
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

      {/* Full Beneficiary Profile, Safe Communication Preferences & DPDP 2023 Consents Modal */}
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
                  backgroundColor: n.read ? '#FAFAFA' : '#F5F3FF',
                  border: n.read ? '1px solid var(--ux4g-border)' : '1.5px solid var(--ux4g-violet-300)',
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
