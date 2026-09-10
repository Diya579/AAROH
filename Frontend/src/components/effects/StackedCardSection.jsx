import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { Shield, Sparkles, CheckCircle2, Clock, PhoneCall, AlertTriangle, HeartHandshake, Scale, Activity, Brain } from 'lucide-react';

const CARDS_DATA = [
  {
    stepNumber: 1,
    badge: 'Step 01 • Citizen Entry',
    badgeColor: '#3E210E',
    badgeBg: '#E4CFB8',
    title: 'Multimodal Citizen Interaction',
    subtitle: 'Safe, consensual check-in via sovereign speech audio or text',
    description:
      'Victims and beneficiaries interact at their chosen safe hour and channel using conversational voice or text prompts, supported in 22 scheduled Indian languages with complete DPDP 2023 consent control.',
    tags: ['Bilingual ASR Pipeline', 'Explicit DPDP Consent', '22 Scheduled Languages', 'Zero Surveillance'],
    accentColor: '#543118',
    gradientBg: 'linear-gradient(135deg, #F7F1E6 0%, #EFE8DB 50%, #E4CFB8 100%)',
    borderColor: '#3A2312',
    watermarkColor: '#3A2312',
    previewType: 'voice_input',
  },
  {
    stepNumber: 2,
    badge: 'Step 02 • AI Inference',
    badgeColor: '#543118',
    badgeBg: '#F3E7D7',
    title: 'Distress & Acoustic Assessment',
    subtitle: 'Dynamic baseline calibration and acoustic sentiment screening',
    description:
      'Backend models calculate linguistic, acoustic, and temporal distress deviations relative to the individual\'s own historical baseline, preventing generic statistical bias from population averages.',
    tags: ['Temporal Smoothing', 'Baseline Deviation Tracking', 'Acoustic Pitch Variance', 'AES-256 Encrypted'],
    accentColor: '#734828',
    gradientBg: 'linear-gradient(135deg, #FAF4EB 0%, #F4ECE0 45%, #E6DAC9 100%)',
    borderColor: '#3A2312',
    watermarkColor: '#3A2312',
    previewType: 'acoustic_ai',
  },
  {
    stepNumber: 3,
    badge: 'Step 03 • Longitudinal Care',
    badgeColor: '#2D2913',
    badgeBg: '#F3F1E7',
    title: 'Longitudinal Monitoring (Trauma vs. Coping)',
    subtitle: 'Continuous tracking across 30-day and 90-day recovery horizons',
    description:
      'Rather than relying on single-point snapshot questionnaires, AAROH evaluates emotional trajectories over time to observe natural coping patterns versus compounding trauma deterioration.',
    tags: ['30/90-Day Trajectory', 'Zero Snapshot Bias', 'GIGW 3.0 Certified', 'WCAG 2.1 AA Audited'],
    accentColor: '#443F24',
    gradientBg: 'linear-gradient(135deg, #F3F1E7 0%, #EAE5D4 40%, #E6DAC9 100%)',
    borderColor: '#3A2312',
    watermarkColor: '#3A2312',
    previewType: 'compliance_chips',
  },
  {
    stepNumber: 4,
    badge: 'Step 04 • Predictive Flag',
    badgeColor: '#591605',
    badgeBg: '#F8ECE7',
    title: 'Early Risk & Escalation Detection',
    subtitle: 'Predictive flags triggered 48 hours prior to acute crises',
    description:
      'When escalation probability crosses verified thresholds, proactive flags alert authorized clinical counsellors and district nodal officers with explainable AI contributing factors.',
    tags: ['48-Hour Proactive Window', 'Explainable AI Decomposition', 'District SLA Audited', 'Human-in-the-Loop'],
    accentColor: '#822710',
    gradientBg: 'linear-gradient(135deg, #FBF6EE 0%, #F4E8D1 45%, #F8ECE7 100%)',
    borderColor: '#822710',
    watermarkColor: '#822710',
    previewType: 'early_alert',
  },
  {
    stepNumber: 5,
    badge: 'Step 05 • Clinical Triage',
    badgeColor: '#3E210E',
    badgeBg: '#E4CFB8',
    title: 'Human-Centred Clinical Support',
    subtitle: 'Direct assignment to certified trauma psychologists and officers',
    description:
      'AI never takes automated unilateral decisions. Certified mental health specialists conduct compassionate outreach, structured psychological evaluations, and statutory welfare reviews within strict SLA windows.',
    tags: ['NIMHANS Certified Leads', '2-Hour Emergency SLA', 'Protected Outcall', 'Dual Sign-Off Mandate'],
    accentColor: '#543118',
    gradientBg: 'linear-gradient(135deg, #FAF4EB 0%, #F4ECE0 45%, #E4CFB8 100%)',
    borderColor: '#3A2312',
    watermarkColor: '#3A2312',
    previewType: 'counsellor_dispatch',
  },
  {
    stepNumber: 6,
    badge: 'Step 06 • Statutory Resolution',
    badgeColor: '#2C1508',
    badgeBg: '#DCCEB9',
    title: 'Outcome Tracking & Continuous Follow-up',
    subtitle: 'Closed-loop accountability through District & State SLAs',
    description:
      'Intervention results — counselling sessions, medical referral, legal assistance, rehabilitation — feed back into the monitoring system to guarantee long-term citizen rehabilitation and statutory accountability.',
    tags: ['8 Statutory Deliverables', '100% CPGRAMS Loop', 'District Magistrate Sign-off', 'Zero Lost Cases'],
    accentColor: '#543118',
    gradientBg: 'linear-gradient(135deg, #F4ECE0 0%, #E6DAC9 45%, #DCCEB9 100%)',
    borderColor: '#3A2312',
    watermarkColor: '#3A2312',
    previewType: 'outcome_governance',
  },
];

// Sub-Component: Rich, High-Fidelity UI Previews Matching Retro Paper Reference
const CardUIPreview = ({ type, accentColor }) => {
  switch (type) {
    case 'voice_input':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FAF4EB',
          borderRadius: '8px',
          padding: '24px',
          border: '2px solid #3A2312',
          boxShadow: '4px 4px 0px #3A2312',
          position: 'relative',
        }}>
          {/* Top Phone / App Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1.5px solid #3A2312' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '4px', backgroundColor: '#E4CFB8', color: '#3E210E', border: '1px solid #3A2312', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '12px', fontFamily: '"Space Mono", monospace' }}>
                आ
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1C120C', fontFamily: '"Fraunces", serif' }}>AAROH Citizen Portal</div>
                <div style={{ fontSize: '0.7rem', color: '#443F24', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#443F24', display: 'inline-block' }}></span>
                  Safe Window Active (17:00–19:00 IST)
                </div>
              </div>
            </div>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#E4CFB8', color: '#3E210E', border: '1.5px solid #3A2312', padding: '3px 8px', borderRadius: '3px', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              Hindi (हिन्दी)
            </span>
          </div>

          {/* Voice Waveform Live Card */}
          <div style={{ backgroundColor: '#F4ECE0', borderRadius: '6px', padding: '16px', border: '1.5px solid #3A2312', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#543118', display: 'flex', alignItems: 'center', gap: '6px', fontFamily: '"Space Mono", monospace' }}>
                <Activity size={14} /> Spoken Voice Input
              </span>
              <span style={{ fontSize: '0.72rem', color: '#785F49', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>00:42 / 02:00</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', height: '48px' }}>
              {[8, 14, 26, 18, 38, 22, 44, 30, 16, 36, 42, 28, 14, 32, 40, 24, 12, 28, 18, 10].map((h, i) => (
                <div
                  key={i}
                  style={{
                    width: '5px',
                    height: `${h}px`,
                    borderRadius: '2px',
                    backgroundColor: i % 2 === 0 ? '#543118' : '#AB8867',
                  }}
                />
              ))}
            </div>
          </div>

          {/* DPDP Consent Pill & Tele-MANAS */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#F3F1E7', padding: '8px 12px', borderRadius: '4px', border: '1.5px solid #443F24' }}>
              <span style={{ fontSize: '0.75rem', color: '#2D2913', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', fontFamily: '"Space Mono", monospace' }}>
                <CheckCircle2 size={13} color="#443F24" /> DPDP 2023 Explicit Consent
              </span>
              <span style={{ fontSize: '0.7rem', color: '#443F24', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>Granted</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#F8ECE7', padding: '8px 12px', borderRadius: '4px', border: '1.5px solid #822710' }}>
              <span style={{ fontSize: '0.75rem', color: '#591605', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px', fontFamily: '"Space Mono", monospace' }}>
                <PhoneCall size={13} color="#822710" /> 24x7 Tele-MANAS Crisis Helpline
              </span>
              <span style={{ fontSize: '0.75rem', color: '#822710', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>14416</span>
            </div>
          </div>
        </div>
      );

    case 'acoustic_ai':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FAF4EB',
          borderRadius: '8px',
          padding: '24px',
          border: '2px solid #3A2312',
          boxShadow: '4px 4px 0px #3A2312',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1.5px solid #3A2312' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#1C120C', display: 'flex', alignItems: 'center', gap: '6px', fontFamily: '"Space Mono", monospace' }}>
              <Brain size={15} color="#543118" /> AI Engine Sovereign v2.4
            </span>
            <span style={{ fontSize: '0.68rem', padding: '3px 8px', borderRadius: '3px', backgroundColor: '#E4CFB8', color: '#3E210E', border: '1px solid #3A2312', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              BERT + Wav2Vec
            </span>
          </div>

          {/* Baseline vs Current Score Gauge */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
            <div style={{ backgroundColor: '#F4ECE0', padding: '12px', borderRadius: '6px', border: '1.5px solid #3A2312', textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: '#785F49', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>Personal Baseline</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#1C120C', fontFamily: '"Fraunces", serif' }}>54%</div>
              <div style={{ fontSize: '0.65rem', color: '#443F24', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>30-Day Mean</div>
            </div>
            <div style={{ backgroundColor: '#F8ECE7', padding: '12px', borderRadius: '6px', border: '1.5px solid #822710', textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: '#822710', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>Current Distress</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#822710', fontFamily: '"Fraunces", serif' }}>72%</div>
              <div style={{ fontSize: '0.65rem', color: '#822710', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>+18% Deviation</div>
            </div>
          </div>

          {/* Explainability Breakdown */}
          <div style={{ backgroundColor: '#F4ECE0', padding: '12px 14px', borderRadius: '6px', border: '1.5px solid #3A2312' }}>
            <div style={{ fontSize: '0.74rem', fontWeight: 800, color: '#1C120C', marginBottom: '8px', fontFamily: '"Space Mono", monospace' }}>
              Contributing Explainability Factors:
            </div>
            {[
              { name: 'Vocal Tremor & Acoustic Pitch', pct: 42, color: '#543118' },
              { name: 'Semantic Hopelessness Markers', pct: 30, color: '#8C6240' },
              { name: 'Circadian Check-In Anomaly', pct: 28, color: '#945B1C' },
            ].map((f, i) => (
              <div key={i} style={{ marginBottom: i < 2 ? '6px' : '0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#4A3423', fontWeight: 700, marginBottom: '2px', fontFamily: '"Space Mono", monospace' }}>
                  <span>{f.name}</span>
                  <span style={{ fontWeight: 800, color: f.color }}>{f.pct}%</span>
                </div>
                <div style={{ height: '6px', backgroundColor: '#E4CFB8', borderRadius: '2px', overflow: 'hidden', border: '1px solid #3A2312' }}>
                  <div style={{ width: `${f.pct}%`, height: '100%', backgroundColor: f.color }} />
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
          {/* Floating Pill Badges Directly in Retro Tactile Style */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', justifyContent: 'center', marginBottom: '18px' }}>
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
                  backgroundColor: '#FAF4EB',
                  borderRadius: '4px',
                  padding: '8px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '3px 3px 0px #3A2312',
                  border: '2px solid #3A2312',
                  fontFamily: '"Space Mono", monospace',
                }}
              >
                <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#1C120C' }}>
                  {b.label}
                </span>
                <span style={{ width: '18px', height: '18px', borderRadius: '3px', backgroundColor: '#3A2312', color: '#FAF4EB', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 900 }}>
                  ✓
                </span>
              </div>
            ))}
          </div>

          {/* Longitudinal Recovery Trajectory Card */}
          <div style={{
            backgroundColor: '#FAF4EB',
            borderRadius: '6px',
            padding: '16px 18px',
            border: '2px solid #3A2312',
            boxShadow: '4px 4px 0px #3A2312',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#1C120C', fontFamily: '"Space Mono", monospace' }}>Longitudinal Trajectory (90-Day Coping Horizon)</span>
              <span style={{ fontSize: '0.72rem', color: '#443F24', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>87% Recovery</span>
            </div>
            <svg viewBox="0 0 340 60" style={{ width: '100%', height: '54px' }}>
              <path d="M 10 50 Q 80 45, 140 32 T 260 20 T 330 12" fill="none" stroke="#543118" strokeWidth="3" strokeLinecap="round" />
              <path d="M 10 50 Q 80 45, 140 32 T 260 20 T 330 12 L 330 60 L 10 60 Z" fill="url(#brownGrad)" opacity="0.2" />
              <circle cx="10" cy="50" r="4" fill="#543118" />
              <circle cx="140" cy="32" r="4" fill="#543118" />
              <circle cx="260" cy="20" r="4" fill="#543118" />
              <circle cx="330" cy="12" r="5" fill="#543118" stroke="#FAF4EB" strokeWidth="2" />
              <defs>
                <linearGradient id="brownGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8C6240" />
                  <stop offset="100%" stopColor="#FAF4EB" />
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
          backgroundColor: '#FAF4EB',
          borderRadius: '8px',
          padding: '24px',
          border: '2px solid #822710',
          boxShadow: '4px 4px 0px #822710',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1.5px solid #822710' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '32px', height: '32px', borderRadius: '4px', backgroundColor: '#F8ECE7', border: '1.5px solid #822710', color: '#822710', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <AlertTriangle size={18} />
              </span>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 900, color: '#591605', fontFamily: '"Fraunces", serif' }}>Predictive Crisis Alert</div>
                <div style={{ fontSize: '0.7rem', color: '#822710', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>48h Prior to Acute Event</div>
              </div>
            </div>
            <span style={{ fontSize: '0.72rem', backgroundColor: '#822710', color: '#FAF4EB', padding: '4px 10px', borderRadius: '3px', border: '1px solid #591605', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              CRITICAL
            </span>
          </div>

          {/* Probability Dial / Bar */}
          <div style={{ backgroundColor: '#F8ECE7', padding: '14px', borderRadius: '6px', border: '1.5px solid #822710', marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#591605', fontFamily: '"Space Mono", monospace' }}>Crisis Probability Escalation:</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 900, color: '#822710', fontFamily: '"Fraunces", serif' }}>78%</span>
            </div>
            <div style={{ height: '8px', backgroundColor: '#E4CFB8', borderRadius: '2px', overflow: 'hidden', border: '1px solid #822710' }}>
              <div style={{ width: '78%', height: '100%', backgroundColor: '#822710' }} />
            </div>
          </div>

          {/* Action Routing List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: '#F4ECE0', border: '1px solid #3A2312', borderRadius: '4px', fontSize: '0.75rem', fontFamily: '"Space Mono", monospace' }}>
              <span style={{ color: '#1C120C', fontWeight: 700 }}>District Magistrate Nodal SLA</span>
              <span style={{ color: '#822710', fontWeight: 800 }}>2-Hour SLA Timer</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: '#F4ECE0', border: '1px solid #3A2312', borderRadius: '4px', fontSize: '0.75rem', fontFamily: '"Space Mono", monospace' }}>
              <span style={{ color: '#1C120C', fontWeight: 700 }}>Counsellor Notification</span>
              <span style={{ color: '#443F24', fontWeight: 800 }}>Dispatched</span>
            </div>
          </div>
        </div>
      );

    case 'counsellor_dispatch':
      return (
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#FAF4EB',
          borderRadius: '8px',
          padding: '24px',
          border: '2px solid #3A2312',
          boxShadow: '4px 4px 0px #3A2312',
        }}>
          {/* Counsellor Profile Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px', paddingBottom: '12px', borderBottom: '1.5px solid #3A2312' }}>
            <div style={{ width: '46px', height: '46px', borderRadius: '6px', backgroundColor: '#E4CFB8', border: '2px solid #3A2312', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
              👩‍⚕️
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 900, color: '#1C120C', fontFamily: '"Fraunces", serif' }}>Dr. Priya Sharma, Ph.D.</div>
              <div style={{ fontSize: '0.72rem', color: '#543118', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>Lead Clinical Psychologist • NIMHANS Reg #8821</div>
            </div>
            <span style={{ fontSize: '0.7rem', backgroundColor: '#F3F1E7', color: '#443F24', border: '1.5px solid #443F24', padding: '3px 8px', borderRadius: '3px', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              Assigned
            </span>
          </div>

          {/* Statutory Countdown Clock */}
          <div style={{ backgroundColor: '#F4ECE0', padding: '12px', borderRadius: '6px', border: '1.5px solid #3A2312', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#543118', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              <Clock size={16} color="#543118" /> Statutory SLA Window:
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 900, color: '#543118', letterSpacing: '0.04em', fontFamily: '"Space Mono", monospace' }}>
              01:48:12
            </div>
          </div>

          {/* Outreach Channels */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div style={{ backgroundColor: '#FAF4EB', padding: '8px 10px', borderRadius: '4px', border: '1.5px solid #3A2312', textAlign: 'center', fontSize: '0.72rem', color: '#1C120C', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
              📞 Encrypted Voice Call
            </div>
            <div style={{ backgroundColor: '#FAF4EB', padding: '8px 10px', borderRadius: '4px', border: '1.5px solid #3A2312', textAlign: 'center', fontSize: '0.72rem', color: '#1C120C', fontWeight: 800, fontFamily: '"Space Mono", monospace' }}>
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
          backgroundColor: '#FAF4EB',
          borderRadius: '8px',
          padding: '24px',
          border: '2px solid #3A2312',
          boxShadow: '4px 4px 0px #3A2312',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '10px', borderBottom: '1.5px solid #3A2312' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 900, color: '#1C120C', display: 'flex', alignItems: 'center', gap: '6px', fontFamily: '"Fraunces", serif' }}>
              <Scale size={16} color="#543118" /> 8 Statutory Deliverables
            </span>
            <span style={{ fontSize: '0.7rem', backgroundColor: '#E4CFB8', color: '#3E210E', fontWeight: 800, padding: '3px 8px', borderRadius: '3px', border: '1px solid #3A2312', fontFamily: '"Space Mono", monospace' }}>
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
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#F4ECE0', padding: '6px 10px', borderRadius: '4px', border: '1px solid #3A2312', fontSize: '0.72rem', fontFamily: '"Space Mono", monospace' }}>
                <span style={{ color: '#1C120C', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <CheckCircle2 size={13} color="#543118" /> {item.label}
                </span>
                <span style={{ color: '#543118', fontWeight: 800, fontSize: '0.68rem' }}>{item.status}</span>
              </div>
            ))}
          </div>

          {/* Recovery Stats */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#E4CFB8', padding: '10px 14px', borderRadius: '4px', border: '1.5px solid #3A2312' }}>
            <span style={{ fontSize: '0.74rem', color: '#3E210E', fontWeight: 700, fontFamily: '"Space Mono", monospace' }}>Total All-India Resolved:</span>
            <span style={{ fontSize: '1rem', fontWeight: 900, color: '#1C120C', fontFamily: '"Fraunces", serif' }}>87.4% Success</span>
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
          borderRadius: '12px',
          background: card.gradientBg,
          border: '2.5px solid #3A2312',
          boxShadow: '6px 6px 0px #3A2312',
          position: 'relative',
          overflow: 'hidden',
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
            color: '#3A2312',
            opacity: 0.09,
            pointerEvents: 'none',
            userSelect: 'none',
            zIndex: 0,
            letterSpacing: '-0.06em',
            fontFamily: '"Fraunces", serif',
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
                  borderRadius: '3px',
                  backgroundColor: card.badgeBg,
                  color: card.badgeColor,
                  border: '1.5px solid #3A2312',
                  boxShadow: '2px 2px 0px #3A2312',
                  fontFamily: '"Space Mono", monospace',
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
                  fontWeight: 900,
                  color: '#1C120C',
                  lineHeight: '1.25',
                  marginBottom: '8px',
                  letterSpacing: '-0.02em',
                  fontFamily: '"Fraunces", "Playfair Display", Georgia, serif',
                }}
              >
                {card.title}
              </h3>
              <p
                style={{
                  fontSize: '0.96rem',
                  fontWeight: 700,
                  color: card.accentColor,
                  lineHeight: '1.4',
                  fontFamily: '"Space Mono", monospace',
                }}
              >
                {card.subtitle}
              </p>
            </div>

            {/* Description */}
            <p
              style={{
                fontSize: '0.92rem',
                color: '#4A3423',
                lineHeight: '1.65',
                fontFamily: '"Space Mono", monospace',
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
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    padding: '4px 10px',
                    borderRadius: '3px',
                    backgroundColor: '#FAF4EB',
                    color: '#1C120C',
                    border: '1.5px solid #3A2312',
                    boxShadow: '2px 2px 0px #3A2312',
                    fontFamily: '"Space Mono", monospace',
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
        backgroundColor: 'var(--ux4g-bg)',
        borderTop: '2px solid #3A2312',
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
