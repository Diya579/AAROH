import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { Shield, Sparkles, CheckCircle2, Clock, PhoneCall, AlertTriangle, HeartHandshake, Scale, Activity, Brain } from 'lucide-react';

const CARDS_DATA = [
  {
    stepNumber: 1,
    badge: 'Step 01 • Citizen Entry',
    badgeColor: '#5B21B6',
    badgeBg: '#DDD6FE',
    title: 'Multimodal Citizen Interaction',
    subtitle: 'Safe, consensual check-in via sovereign speech audio or text',
    description:
      'Victims and beneficiaries interact at their chosen safe hour and channel using conversational voice or text prompts, supported in 22 scheduled Indian languages with complete DPDP 2023 consent control.',
    tags: ['Bilingual ASR Pipeline', 'Explicit DPDP Consent', '22 Scheduled Languages', 'Zero Surveillance'],
    accentColor: '#6D28D9',
    gradientBg: 'linear-gradient(135deg, #F3E8FF 0%, #EDE9FE 50%, #DDD6FE 100%)',
    borderColor: '#C4B5FD',
    watermarkColor: '#6D28D9',
    previewType: 'voice_input',
  },
  {
    stepNumber: 2,
    badge: 'Step 02 • AI Inference',
    badgeColor: '#4F46E5',
    badgeBg: '#E0E7FF',
    title: 'Distress & Acoustic Assessment',
    subtitle: 'Dynamic baseline calibration and acoustic sentiment screening',
    description:
      'Backend models calculate linguistic, acoustic, and temporal distress deviations relative to the individual\'s own historical baseline, preventing generic statistical bias from population averages.',
    tags: ['Temporal Smoothing', 'Baseline Deviation Tracking', 'Acoustic Pitch Variance', 'AES-256 Encrypted'],
    accentColor: '#4F46E5',
    gradientBg: 'linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 45%, #FFF7ED 100%)',
    watermarkColor: '#4F46E5',
    previewType: 'acoustic_ai',
  },
  {
    stepNumber: 3,
    badge: 'Step 03 • Longitudinal Care',
    badgeColor: '#059669',
    badgeBg: '#DCFCE7',
    title: 'Longitudinal Monitoring (Trauma vs. Coping)',
    subtitle: 'Continuous tracking across 30-day and 90-day recovery horizons',
    description:
      'Rather than relying on single-point snapshot questionnaires, AAROH evaluates emotional trajectories over time to observe natural coping patterns versus compounding trauma deterioration.',
    tags: ['30/90-Day Trajectory', 'Zero Snapshot Bias', 'GIGW 3.0 Certified', 'WCAG 2.1 AA Audited'],
    accentColor: '#059669',
    gradientBg: 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 40%, #EFF6FF 100%)',
    watermarkColor: '#059669',
    previewType: 'compliance_chips',
  },
  {
    stepNumber: 4,
    badge: 'Step 04 • Predictive Flag',
    badgeColor: '#DC2626',
    badgeBg: '#FEE2E2',
    title: 'Early Risk & Escalation Detection',
    subtitle: 'Predictive flags triggered 48 hours prior to acute crises',
    description:
      'When escalation probability crosses verified thresholds, proactive flags alert authorized clinical counsellors and district nodal officers with explainable AI contributing factors.',
    tags: ['48-Hour Proactive Window', 'Explainable AI Decomposition', 'District SLA Audited', 'Human-in-the-Loop'],
    accentColor: '#DC2626',
    gradientBg: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 45%, #FEE2E2 100%)',
    watermarkColor: '#DC2626',
    previewType: 'early_alert',
  },
  {
    stepNumber: 5,
    badge: 'Step 05 • Clinical Triage',
    badgeColor: '#7C3AED',
    badgeBg: '#EDE9FE',
    title: 'Human-Centred Clinical Support',
    subtitle: 'Direct assignment to certified trauma psychologists and officers',
    description:
      'AI never takes automated unilateral decisions. Certified mental health specialists conduct compassionate outreach, structured psychological evaluations, and statutory welfare reviews within strict SLA windows.',
    tags: ['NIMHANS Certified Leads', '2-Hour Emergency SLA', 'Protected Outcall', 'Dual Sign-Off Mandate'],
    accentColor: '#7C3AED',
    gradientBg: 'linear-gradient(135deg, #FAF5FF 0%, #EDE9FE 45%, #DDD6FE 100%)',
    watermarkColor: '#7C3AED',
    previewType: 'counsellor_dispatch',
  },
  {
    stepNumber: 6,
    badge: 'Step 06 • Statutory Resolution',
    badgeColor: '#0D9488',
    badgeBg: '#CCFBF1',
    title: 'Outcome Tracking & Continuous Follow-up',
    subtitle: 'Closed-loop accountability through District & State SLAs',
    description:
      'Intervention results — counselling sessions, medical referral, legal assistance, rehabilitation — feed back into the monitoring system to guarantee long-term citizen rehabilitation and statutory accountability.',
    tags: ['8 Statutory Deliverables', '100% CPGRAMS Loop', 'District Magistrate Sign-off', 'Zero Lost Cases'],
    accentColor: '#0D9488',
    gradientBg: 'linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 45%, #E0F2FE 100%)',
    watermarkColor: '#0D9488',
    previewType: 'outcome_governance',
  },
];

// Sub-Component: Rich, High-Fidelity UI Previews Matching Reference
const CardUIPreview = ({ type, accentColor }) => {
  switch (type) {
    case 'voice_input':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: 'var(--ux4g-surface)',
          borderRadius: '24px',
          padding: '24px',
          boxShadow: '0 16px 36px -8px rgba(109, 40, 217, 0.12), 0 0 0 1px rgba(221, 214, 254, 0.8)',
          position: 'relative',
        }}>
          {/* Top Phone / App Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid #F3F4F6' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '8px', backgroundColor: '#EDE9FE', color: '#6D28D9', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '12px' }}>
                आ
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1E1B4B' }}>AAROH Citizen Portal</div>
                <div style={{ fontSize: '0.7rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#059669', display: 'inline-block' }}></span>
                  Safe Window Active (17:00–19:00 IST)
                </div>
              </div>
            </div>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#FAF5FF', color: '#6D28D9', border: '1px solid #DDD6FE', padding: '3px 8px', borderRadius: '6px', fontWeight: 600 }}>
              Hindi (हिन्दी)
            </span>
          </div>

          {/* Voice Waveform Live Card */}
          <div style={{ backgroundColor: '#FAF5FF', borderRadius: '16px', padding: '16px', border: '1px solid #DDD6FE', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#6D28D9', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Activity size={14} /> Spoken Voice Input
              </span>
              <span style={{ fontSize: '0.72rem', color: '#6B7280', fontWeight: 600 }}>00:42 / 02:00</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', height: '48px' }}>
              {[8, 14, 26, 18, 38, 22, 44, 30, 16, 36, 42, 28, 14, 32, 40, 24, 12, 28, 18, 10].map((h, i) => (
                <div
                  key={i}
                  style={{
                    width: '5px',
                    height: `${h}px`,
                    borderRadius: '4px',
                    backgroundColor: i % 2 === 0 ? '#7C3AED' : '#A78BFA',
                    opacity: 0.85,
                  }}
                />
              ))}
            </div>
          </div>

          {/* DPDP Consent Pill & Tele-MANAS */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#F0FDF4', padding: '8px 12px', borderRadius: '10px', border: '1px solid #BBF7D0' }}>
              <span style={{ fontSize: '0.75rem', color: '#166534', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={13} color="#059669" /> DPDP 2023 Explicit Consent
              </span>
              <span style={{ fontSize: '0.7rem', color: '#059669', fontWeight: 700 }}>Granted</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#EFF6FF', padding: '8px 12px', borderRadius: '10px', border: '1px solid #BFDBFE' }}>
              <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <PhoneCall size={13} color="#2563EB" /> 24x7 Tele-MANAS Crisis Helpline
              </span>
              <span style={{ fontSize: '0.72rem', color: '#1D4ED8', fontWeight: 800 }}>14416</span>
            </div>
          </div>
        </div>
      );

    case 'acoustic_ai':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: 'var(--ux4g-surface)',
          borderRadius: '24px',
          padding: '24px',
          boxShadow: '0 16px 36px -8px rgba(79, 70, 229, 0.12), 0 0 0 1px rgba(199, 210, 254, 0.8)',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#312E81', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Brain size={15} color="#4F46E5" /> AI Engine Sovereign v2.4
            </span>
            <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '999px', backgroundColor: '#EEF2FF', color: '#4338CA', fontWeight: 700 }}>
              BERT + Wav2Vec
            </span>
          </div>

          {/* Baseline vs Current Score Gauge */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
            <div style={{ backgroundColor: '#F8FAFC', padding: '12px', borderRadius: '12px', border: '1px solid #E2E8F0', textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: '#64748B', fontWeight: 600 }}>Personal Baseline</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#334155' }}>54%</div>
              <div style={{ fontSize: '0.65rem', color: '#059669', fontWeight: 700 }}>30-Day Mean</div>
            </div>
            <div style={{ backgroundColor: '#FEF2F2', padding: '12px', borderRadius: '12px', border: '1px solid #FECACA', textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: '#991B1B', fontWeight: 600 }}>Current Distress</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#DC2626' }}>72%</div>
              <div style={{ fontSize: '0.65rem', color: '#DC2626', fontWeight: 800 }}>+18% Deviation</div>
            </div>
          </div>

          {/* Explainability Breakdown */}
          <div style={{ backgroundColor: '#FAF5FF', padding: '12px 14px', borderRadius: '14px', border: '1px solid #E9D5FF' }}>
            <div style={{ fontSize: '0.74rem', fontWeight: 700, color: '#581C87', marginBottom: '8px' }}>
              Contributing Explainability Factors:
            </div>
            {[
              { name: 'Vocal Tremor & Acoustic Pitch', pct: 42, color: '#4F46E5' },
              { name: 'Semantic Hopelessness Markers', pct: 30, color: '#7C3AED' },
              { name: 'Circadian Check-In Anomaly', pct: 28, color: '#059669' },
            ].map((f, i) => (
              <div key={i} style={{ marginBottom: i < 2 ? '6px' : '0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#475569', fontWeight: 600, marginBottom: '2px' }}>
                  <span>{f.name}</span>
                  <span style={{ fontWeight: 800, color: f.color }}>{f.pct}%</span>
                </div>
                <div style={{ height: '5px', backgroundColor: '#E2E8F0', borderRadius: '999px', overflow: 'hidden' }}>
                  <div style={{ width: `${f.pct}%`, height: '100%', backgroundColor: f.color, borderRadius: '999px' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      );

    case 'compliance_chips':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          position: 'relative',
          padding: '10px',
        }}>
          {/* Floating Pill Badges Directly Like UX4G Reference */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center', marginBottom: '18px' }}>
            {[
              { label: 'WCAG 2.1 AA', desc: 'Accessibility' },
              { label: 'DPDP 2023', desc: 'Privacy Shield' },
              { label: 'GIGW 3.0', desc: 'Govt Standard' },
              { label: 'Right to SLA', desc: 'Guaranteed' },
              { label: 'Zero Surveillance', desc: 'No Wiretapping' },
            ].map((b, i) => (
              <div
                key={i}
                style={{
                  backgroundColor: 'var(--ux4g-surface)',
                  borderRadius: '999px',
                  padding: '10px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  boxShadow: '0 8px 20px -4px rgba(5, 150, 105, 0.15), 0 2px 6px rgba(0, 0, 0, 0.04)',
                  border: '1.5px solid #A7F3D0',
                }}
              >
                <span style={{ fontSize: '0.95rem', fontWeight: 800, color: '#065F46', letterSpacing: '-0.01em' }}>
                  {b.label}
                </span>
                <span style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#059669', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 900 }}>
                  ✓
                </span>
              </div>
            ))}
          </div>

          {/* Longitudinal Recovery Trajectory Card */}
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '18px',
            padding: '14px 18px',
            boxShadow: '0 10px 24px -6px rgba(16, 185, 129, 0.12), 0 0 0 1px #D1FAE5',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#065F46' }}>Longitudinal Trajectory (90-Day Coping Horizon)</span>
              <span style={{ fontSize: '0.7rem', color: '#059669', fontWeight: 700 }}>87% Recovery</span>
            </div>
            <svg viewBox="0 0 340 60" style={{ width: '100%', height: '54px' }}>
              <path d="M 10 50 Q 80 45, 140 32 T 260 20 T 330 12" fill="none" stroke="#059669" strokeWidth="3.5" strokeLinecap="round" />
              <path d="M 10 50 Q 80 45, 140 32 T 260 20 T 330 12 L 330 60 L 10 60 Z" fill="url(#emeraldGrad)" opacity="0.12" />
              <circle cx="10" cy="50" r="4" fill="#059669" />
              <circle cx="140" cy="32" r="4" fill="#059669" />
              <circle cx="260" cy="20" r="4" fill="#059669" />
              <circle cx="330" cy="12" r="5" fill="#059669" stroke="#FFFFFF" strokeWidth="2" />
              <defs>
                <linearGradient id="emeraldGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#059669" />
                  <stop offset="100%" stopColor="#FFFFFF" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
      );

    case 'early_alert':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FFFFFF',
          borderRadius: '24px',
          padding: '24px',
          boxShadow: '0 16px 36px -8px rgba(220, 38, 38, 0.15), 0 0 0 1px rgba(254, 202, 202, 0.8)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#FEE2E2', color: '#DC2626', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle size={18} />
              </span>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#991B1B' }}>Predictive Crisis Alert</div>
                <div style={{ fontSize: '0.7rem', color: '#DC2626', fontWeight: 600 }}>48h Prior to Acute Event</div>
              </div>
            </div>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#DC2626', color: '#FFFFFF', padding: '4px 10px', borderRadius: '999px', fontWeight: 800 }}>
              CRITICAL
            </span>
          </div>

          {/* Probability Dial / Bar */}
          <div style={{ backgroundColor: '#FFF5F5', padding: '14px', borderRadius: '14px', border: '1px solid #FECACA', marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7F1D1D' }}>Crisis Probability Escalation:</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 900, color: '#DC2626' }}>78%</span>
            </div>
            <div style={{ height: '8px', backgroundColor: '#FEE2E2', borderRadius: '999px', overflow: 'hidden' }}>
              <div style={{ width: '78%', height: '100%', backgroundColor: '#DC2626', borderRadius: '999px' }} />
            </div>
          </div>

          {/* Action Routing List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: '#F8FAFC', borderRadius: '8px', fontSize: '0.75rem' }}>
              <span style={{ color: '#334155', fontWeight: 600 }}>District Magistrate Nodal SLA</span>
              <span style={{ color: '#DC2626', fontWeight: 700 }}>2-Hour SLA Timer</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: '#F8FAFC', borderRadius: '8px', fontSize: '0.75rem' }}>
              <span style={{ color: '#334155', fontWeight: 600 }}>Counsellor Notification</span>
              <span style={{ color: '#059669', fontWeight: 700 }}>Dispatched</span>
            </div>
          </div>
        </div>
      );

    case 'counsellor_dispatch':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FFFFFF',
          borderRadius: '24px',
          padding: '24px',
          boxShadow: '0 16px 36px -8px rgba(124, 58, 237, 0.15), 0 0 0 1px rgba(221, 214, 254, 0.8)',
        }}>
          {/* Counsellor Profile Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px', paddingBottom: '12px', borderBottom: '1px solid #F3F4F6' }}>
            <div style={{ width: '46px', height: '46px', borderRadius: '50%', backgroundColor: '#EDE9FE', border: '2px solid #7C3AED', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
              👩‍⚕️
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#1E1B4B' }}>Dr. Priya Sharma, Ph.D.</div>
              <div style={{ fontSize: '0.72rem', color: '#7C3AED', fontWeight: 600 }}>Lead Clinical Psychologist • NIMHANS Reg #8821</div>
            </div>
            <span style={{ fontSize: '0.7rem', backgroundColor: '#F0FDF4', color: '#166534', border: '1px solid #BBF7D0', padding: '3px 8px', borderRadius: '6px', fontWeight: 700 }}>
              Assigned
            </span>
          </div>

          {/* Statutory Countdown Clock */}
          <div style={{ backgroundColor: '#FAF5FF', padding: '12px', borderRadius: '12px', border: '1px solid #DDD6FE', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#581C87', fontWeight: 700 }}>
              <Clock size={16} color="#7C3AED" /> Statutory SLA Window:
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 900, color: '#7C3AED', letterSpacing: '0.04em' }}>
              01:48:12
            </div>
          </div>

          {/* Outreach Channels */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div style={{ backgroundColor: '#F8FAFC', padding: '8px 10px', borderRadius: '8px', border: '1px solid #E2E8F0', textAlign: 'center', fontSize: '0.72rem', color: '#334155', fontWeight: 600 }}>
              📞 Encrypted Voice Call
            </div>
            <div style={{ backgroundColor: '#F8FAFC', padding: '8px 10px', borderRadius: '8px', border: '1px solid #E2E8F0', textAlign: 'center', fontSize: '0.72rem', color: '#334155', fontWeight: 600 }}>
              🏥 PHC Medical Outreach
            </div>
          </div>
        </div>
      );

    case 'outcome_governance':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FFFFFF',
          borderRadius: '24px',
          padding: '24px',
          boxShadow: '0 16px 36px -8px rgba(13, 148, 136, 0.15), 0 0 0 1px rgba(153, 246, 228, 0.8)',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#134E4A', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Scale size={16} color="#0D9488" /> 8 Statutory Deliverables
            </span>
            <span style={{ fontSize: '0.7rem', backgroundColor: '#CCFBF1', color: '#0F766E', fontWeight: 800, padding: '3px 8px', borderRadius: '6px' }}>
              100% SLA Audited
            </span>
          </div>

          {/* Checklist of Outcomes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
            {[
              { label: 'Section 15A Protective Relocation', status: 'Delivered' },
              { label: 'Interim Compensation Disbursed (₹1,00,000)', status: 'Credited' },
              { label: '6/6 Clinical Counselling Cycles', status: 'Completed' },
              { label: 'Free Legal Defense Advocate', status: 'Assigned' },
            ].map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#F0FDFA', padding: '6px 10px', borderRadius: '8px', border: '1px solid #99F6E4', fontSize: '0.72rem' }}>
                <span style={{ color: '#115E59', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <CheckCircle2 size={13} color="#0D9488" /> {item.label}
                </span>
                <span style={{ color: '#0D9488', fontWeight: 800, fontSize: '0.68rem' }}>{item.status}</span>
              </div>
            ))}
          </div>

          {/* Recovery Stats */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#F8FAFC', padding: '10px 14px', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
            <span style={{ fontSize: '0.74rem', color: '#64748B', fontWeight: 600 }}>Total All-India Resolved:</span>
            <span style={{ fontSize: '1rem', fontWeight: 900, color: '#0D9488' }}>87.4% Success</span>
          </div>
        </div>
      );

    default:
      return null;
  }
};

// Single Stack Card with Scroll Transform
const StackCard = ({ card, index, totalCards, progress, reducedMotion }) => {
  const targetScale = 1 - (totalCards - index) * 0.035;
  const range = [index * (1 / totalCards), 1];
  const scale = useTransform(progress, range, [1, targetScale]);

  return (
    <div
      style={{
        minHeight: '78vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'sticky',
        top: `calc(90px + ${index * 26}px)`,
        zIndex: index + 1,
        padding: '16px 0',
      }}
    >
      <motion.div
        style={{
          scale: reducedMotion ? 1 : scale,
          width: '100%',
          maxWidth: '1180px',
          borderRadius: '36px',
          background: card.gradientBg,
          border: card.borderColor ? `1.5px solid ${card.borderColor}` : '1.5px solid rgba(255, 255, 255, 0.95)',
          boxShadow: `0 ${18 + index * 6}px ${45 + index * 10}px -12px rgba(30, 41, 59, ${0.08 + index * 0.02}), 0 0 0 1px rgba(226, 232, 240, 0.75)`,
          position: 'relative',
          overflow: 'hidden',
          backdropFilter: 'blur(12px)',
        }}
      >
        {/* Giant Watermark Step Number in Background */}
        <div
          style={{
            position: 'absolute',
            top: '-25px',
            left: '20px',
            fontSize: '13rem',
            fontWeight: 900,
            lineHeight: 1,
            color: card.watermarkColor,
            opacity: 0.085,
            pointerEvents: 'none',
            userSelect: 'none',
            zIndex: 0,
            letterSpacing: '-0.06em',
          }}
        >
          {card.stepNumber}
        </div>

        {/* Card Content Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '46% 54%',
            position: 'relative',
            zIndex: 1,
            minHeight: '440px',
          }}
        >
          {/* LEFT: Text Content */}
          <div
            style={{
              padding: '48px 44px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: '16px',
            }}
          >
            {/* Step badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  padding: '5px 14px',
                  borderRadius: '999px',
                  backgroundColor: card.badgeBg,
                  color: card.badgeColor,
                  border: `1px solid ${card.accentColor}30`,
                }}
              >
                {card.badge}
              </span>
            </div>

            {/* Title & Subtitle */}
            <div>
              <h3
                style={{
                  fontSize: '1.85rem',
                  fontWeight: 800,
                  color: '#1E1B4B',
                  lineHeight: '1.25',
                  marginBottom: '8px',
                  letterSpacing: '-0.02em',
                }}
              >
                {card.title}
              </h3>
              <p
                style={{
                  fontSize: '0.96rem',
                  fontWeight: 600,
                  color: card.accentColor,
                  lineHeight: '1.4',
                }}
              >
                {card.subtitle}
              </p>
            </div>

            {/* Description */}
            <p
              style={{
                fontSize: '0.92rem',
                color: '#475569',
                lineHeight: '1.65',
              }}
            >
              {card.description}
            </p>

            {/* Feature Tag Chips */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
              {card.tags.map((tag, idx) => (
                <span
                  key={idx}
                  style={{
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    padding: '4px 12px',
                    borderRadius: '999px',
                    backgroundColor: '#FFFFFF',
                    color: '#334155',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* RIGHT: High-Fidelity UI Component Preview */}
          <div
            style={{
              padding: '36px 40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
            }}
          >
            <CardUIPreview type={card.previewType} accentColor={card.accentColor} />
          </div>
        </div>
      </motion.div>
    </div>
  );
};

// Main Stacked Card Section
export const StackedCardSection = () => {
  const containerRef = useRef(null);
  const { reducedMotion } = useThemeAccessibility();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  return (
    <section
      id="workflow"
      ref={containerRef}
      style={{
        padding: '80px 0 120px',
        backgroundColor: '#F8FAFC',
        borderTop: '1px solid #E2E8F0',
        position: 'relative',
      }}
    >
      <div className="container">
        {/* Section Header */}
        <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 40px' }}>
          <span
            style={{
              color: 'var(--ux4g-violet-700)',
              fontWeight: 800,
              fontSize: '0.85rem',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              display: 'inline-block',
              marginBottom: '10px',
            }}
          >
            Process Architecture
          </span>
          <h2
            style={{
              fontSize: '2.5rem',
              fontWeight: 900,
              color: 'var(--ux4g-violet-950)',
              letterSpacing: '-0.025em',
              lineHeight: '1.2',
              marginBottom: '14px',
            }}
          >
            How AAROH Operates (The 6-Step Care Cycle)
          </h2>
          <p
            style={{
              color: 'var(--ux4g-text-secondary)',
              fontSize: '1.05rem',
              lineHeight: '1.6',
            }}
          >
            Explore the end-to-end workflow from citizen check-in to clinical resolution.
          </p>
        </div>

        {/* Stacked Cards Stream */}
        <div style={{ position: 'relative' }}>
          {CARDS_DATA.map((card, index) => (
            <StackCard
              key={card.stepNumber}
              card={card}
              index={index}
              totalCards={CARDS_DATA.length}
              progress={scrollYProgress}
              reducedMotion={reducedMotion}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default StackedCardSection;
