import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Shield, 
  Activity, 
  Brain, 
  HeartHandshake, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  Clock, 
  Lock, 
  AlertTriangle, 
  PhoneCall, 
  Volume2, 
  Users, 
  Sliders,
  HelpCircle,
  Scale,
  Heart,
  Landmark
} from 'lucide-react';
import { UX4GButton } from '../components/common/UX4GButton';
import { UX4GCard } from '../components/common/UX4GCard';
import { RiskBadge, StatusBadge } from '../components/common/UX4GBadge';
import { UX4GAccordion } from '../components/common/UX4GAccordion';
import { useAuth } from '../context/AuthContext';
import { useThemeAccessibility } from '../context/ThemeAccessibilityContext';

// Animation Framework Components
import { TextMaskReveal } from '../components/effects/TextMaskReveal';
import { KineticTiltCard } from '../components/effects/KineticTiltCard';
import { MarqueeTicker } from '../components/effects/MarqueeTicker';
import { BentoGrid, BentoItem } from '../components/effects/BentoGrid';
import { StackedCardSection } from '../components/effects/StackedCardSection';
import { HeroSection } from '../components/effects/HeroSection';

export const HomePage = () => {
  const { isAuthenticated, currentUser, getDashboardPath } = useAuth();
  const { openOffcanvas, reducedMotion, toggleReducedMotion } = useThemeAccessibility();

  useEffect(() => {
    if (window.location.hash) {
      const id = window.location.hash.replace('#', '');
      const el = document.getElementById(id);
      if (el) {
        setTimeout(() => {
          el.scrollIntoView({ behavior: 'smooth' });
        }, 150);
      }
    }
  }, []);

  const workflowSteps = [
    {
      stepNumber: 1,
      title: 'Multimodal Interaction',
      subtitle: 'Safe, consensual check-in via speech audio or text',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Participants interact at their chosen safe hour and channel using conversational voice or text prompts, supported in multiple languages without intrusive surveillance.
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="ux4g-badge ux4g-badge-primary">Multilingual ASR Pipeline</span>
            <span className="ux4g-badge ux4g-badge-low">Explicit Consent Verified</span>
          </div>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-primary">Input</span>
    },
    {
      stepNumber: 2,
      title: 'Distress & Acoustic Assessment',
      subtitle: 'Dynamic baseline calibration and acoustic sentiment screening',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Backend models calculate linguistic, acoustic, and temporal distress deviations relative to the individual's baseline, preventing generic statistical bias.
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="ux4g-badge ux4g-badge-primary">Temporal Smoothing</span>
            <span className="ux4g-badge ux4g-badge-medium">Baseline Shift Tracking</span>
          </div>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-primary">AI Inference</span>
    },
    {
      stepNumber: 3,
      title: 'Longitudinal Monitoring',
      subtitle: 'Continuous tracking across 30-day and 90-day recovery horizons',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Rather than relying on single-point snapshot questionnaires, AAROH evaluates emotional trajectories over time to observe natural coping vs. compounding trauma.
          </p>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-primary">Timeline</span>
    },
    {
      stepNumber: 4,
      title: 'Early Risk & Escalation Detection',
      subtitle: 'Predictive flags for sudden distress spikes before crisis onset',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            When escalation probability passes verified thresholds, proactive flags alert authorized clinical counsellors and regional directors with explainable contributing factors.
          </p>
          <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
            <RiskBadge level="High" size="sm" />
            <RiskBadge level="Critical" size="sm" />
          </div>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-high">Risk Alert</span>
    },
    {
      stepNumber: 5,
      title: 'Human-Centred Clinical Support',
      subtitle: 'Direct assignment to certified trauma counsellors',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            AI never takes automated unilateral decisions. Certified mental health specialists conduct compassionate outreach, structured psychological evaluations, and safety reviews.
          </p>
          <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
            <StatusBadge status="ASSIGNED" size="sm" />
            <StatusBadge status="IN_PROGRESS" size="sm" />
          </div>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-low">Human Action</span>
    },
    {
      stepNumber: 6,
      title: 'Outcome Tracking & Continuous Follow-up',
      subtitle: 'Closed-loop accountability through verified clinical SLAs',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Intervention results (counselling sessions, medical referral, legal assistance, rehabilitation) feed back into the monitoring system to sustain recovery trajectories.
          </p>
          <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
            <StatusBadge status="COMPLETED" size="sm" />
          </div>
        </div>
      ),
      badge: <span className="ux4g-badge ux4g-badge-low">Closed Loop</span>
    },
  ];

  // Frequently Asked Questions
  const faqItems = [
    {
      id: 'faq-1',
      title: 'How does AAROH ensure privacy and data sovereignty?',
      subtitle: 'Strict privacy standards & cryptographic security',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          All participant interactions require unambiguous, revocable consent. Data is encrypted using AES-256 at rest and stored in sovereign, isolated cloud enclaves. Audio telemetry is processed through an ephemeral pipeline with zero-knowledge de-identification, ensuring only authorized clinical specialists assigned to your case can ever review records.
        </p>
      ),
    },
    {
      id: 'faq-2',
      title: 'Can the AI take punitive or automated care decisions?',
      subtitle: 'Human-in-the-loop ethical AI guarantee',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          <strong>No, strictly never.</strong> Under AAROH's ethical AI charter, artificial intelligence is strictly assistive. It flags potential distress shifts to accredited specialists. All decisions regarding restitution, protective sanctuary, clinical diagnoses, and legal advocacy are made exclusively by licensed psychologists, legal ombudsmen, and certified care supervisors.
        </p>
      ),
    },
    {
      id: 'faq-3',
      title: 'What happens if a participant misses a scheduled check-in?',
      subtitle: 'Non-punitive care protocols',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          Missing a check-in is never treated as a penalty or violation. The platform respects personal autonomy. If consecutive check-ins are missed during an elevated recovery phase, the assigned specialist gently reaches out during the participant's registered "safe hours" to ensure their safety and well-being.
        </p>
      ),
    },
    {
      id: 'faq-4',
      title: 'How is distress scored without intrusive surveillance?',
      subtitle: 'Dynamic baseline deviation vs. surveillance',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          AAROH does not perform surveillance or background tracking. It only evaluates consensual check-in sessions. Acoustic pitch variance, speaking cadence, and linguistic emotional markers are calibrated against the participant's own self-established baseline, allowing longitudinal tracking without intrusive device permissions.
        </p>
      ),
    },
    {
      id: 'faq-5',
      title: 'Who has access to active case telemetry?',
      subtitle: 'Role-Based Access Control (RBAC) boundaries',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          Access is strictly compartmentalized via Role-Based Access Control. Only your assigned clinical counsellor and designated regional supervisor have visibility into active case records. Executive leadership only views anonymized, aggregate metrics to monitor platform health and resilience.
        </p>
      ),
    },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* =========================================================================
          ANIMATED HERO SECTION — Particle Canvas, Glow Sphere, Unscramble Text
          ========================================================================= */}
      <HeroSection />

      {/* =========================================================================
          CONTENT DIVIDER: SEAMLESS INFINITE MARQUEE TICKER
          ========================================================================= */}
      <MarqueeTicker speed={28} />

      {/* =========================================================================
          STAGGERED BENTO GRID: REVOLUTIONARY SYSTEM CAPABILITIES
          ========================================================================= */}
      <section id="about" style={{ padding: '72px 0', backgroundColor: 'var(--ux4g-surface)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 48px' }}>
            <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Intelligent Care Ecosystem
            </span>
            <TextMaskReveal
              as="h2"
              lines={["Architectural Bento Highlights"]}
              style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginTop: '8px', marginBottom: '14px' }}
            />
            <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '1rem', lineHeight: '1.6' }}>
              The technological architecture powering AAROH's acoustic distress modeling and human-first resilience.
            </p>
          </div>

          <BentoGrid columns={3} gap="24px">
            {/* Bento Item 1: Large Span Continuous Monitoring */}
            <BentoItem colSpan={2} rowSpan={1}>
              <KineticTiltCard maxTilt={8} elevation={2} style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ width: '46px', height: '46px', borderRadius: '12px', backgroundColor: 'var(--ux4g-violet-50)', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <Activity size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                    Longitudinal Trajectory vs. Snapshot Bias
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.92rem', lineHeight: '1.65', marginBottom: '16px' }}>
                    Trauma cannot be understood in a single day. AAROH builds an adaptive, individualized baseline over time, filtering temporary stress variations from true compounding psychological deterioration.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <span className="ux4g-badge ux4g-badge-low">Adaptive Baseline</span>
                  <span className="ux4g-badge ux4g-badge-primary">30/90-Day Trajectory</span>
                </div>
              </KineticTiltCard>
            </BentoItem>

            {/* Bento Item 2: Multimodal Speech ASR */}
            <BentoItem colSpan={1} rowSpan={1}>
              <KineticTiltCard maxTilt={10} elevation={2} style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ width: '46px', height: '46px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-success-bg)', color: 'var(--ux4g-success-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <Volume2 size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                    Multimodal Acoustic ASR
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.85rem', lineHeight: '1.6' }}>
                    Inclusive spoken voice check-ins with paralinguistic jitter, pitch, and shiver analysis across dialects.
                  </p>
                </div>
                <span className="ux4g-badge" style={{ backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', border: '1.5px solid #3A2312' }}>Multilingual Neural ASR</span>
              </KineticTiltCard>
            </BentoItem>

            {/* Bento Item 3: Early Escalation Alert */}
            <BentoItem colSpan={1} rowSpan={1}>
              <KineticTiltCard maxTilt={10} elevation={2} style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ width: '46px', height: '46px', borderRadius: '12px', backgroundColor: 'var(--ux4g-danger-bg)', color: 'var(--ux4g-danger)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <AlertTriangle size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                    Predictive Escalation
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.85rem', lineHeight: '1.6' }}>
                    Early flags triggered 48 hours prior to acute crises, enabling proactive de-escalation outreach.
                  </p>
                </div>
                <RiskBadge level="High" size="sm" />
              </KineticTiltCard>
            </BentoItem>

            {/* Bento Item 4: Coordinated Governance & SLAs */}
            <BentoItem colSpan={2} rowSpan={1}>
              <KineticTiltCard maxTilt={8} elevation={2} style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ width: '46px', height: '46px', borderRadius: '12px', backgroundColor: 'var(--ux4g-violet-50)', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <Users size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                    Multi-Tier Clinical & Crisis Coordination
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.92rem', lineHeight: '1.65', marginBottom: '16px' }}>
                    Connects clinical directors, emergency crisis coordinators, and specialized caseworkers into a synchronized command center, guaranteeing rapid case allocation and sub-120ms response SLAs.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <StatusBadge status="IN_PROGRESS" size="sm" />
                  <span className="ux4g-badge ux4g-badge-low">100% SLA Audited</span>
                </div>
              </KineticTiltCard>
            </BentoItem>
          </BentoGrid>
        </div>
      </section>

      {/* =========================================================================
          CARE ARCHITECTURE: 4 DIMENSIONS OF RESILIENCE & CRISIS LIAISON
          ========================================================================= */}
      <section id="safety" style={{ padding: '68px 0', backgroundColor: 'var(--ux4g-bg)', borderTop: '1px solid var(--ux4g-border)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 44px' }}>
            <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Care Architecture
            </span>
            <TextMaskReveal
              as="h2"
              lines={["The 4 Dimensions of Trauma Rehabilitation & Justice Liaison"]}
              style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginTop: '8px', marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.98rem' }}>
              A synchronized framework bridging clinical psychological stabilization with physical sanctuary, judicial advocacy, and economic rehabilitation.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '22px' }}>
            {/* Pillar 1 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Heart size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                1. Clinical Trauma Mitigation
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Continuous linkage to certified trauma psychologists, tele-mental health networks, and compassionate individual cognitive therapy.
              </p>
            </KineticTiltCard>

            {/* Pillar 2 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-success-bg)', color: 'var(--ux4g-success-text)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Shield size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                2. Sanctuary & Rapid Crisis Routing
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Protocols for safe housing shelter routing, emergency dispatch integration, and proactive sanctuary security during safe windows.
              </p>
            </KineticTiltCard>

            {/* Pillar 3 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: 'var(--ux4g-saffron-50)', color: 'var(--ux4g-saffron-500)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Landmark size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                3. Emergency Relief & Restitution
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Direct ledger tracking of emergency restitution funds, clinical grants, and livelihood support disbursed with zero bureaucratic latency.
              </p>
            </KineticTiltCard>

            {/* Pillar 4 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '6px', border: '1.5px solid #3A2312', backgroundColor: 'var(--ux4g-violet-100)', color: 'var(--ux4g-violet-800)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Scale size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                4. Human Rights & Legal Advocacy
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Objective psychosocial assessment dossiers and expedited representation through dedicated legal defense partners.
              </p>
            </KineticTiltCard>
          </div>
        </div>
      </section>

      {/* How AAROH Works: Premium Stacked Card Scroll Animation */}
      <StackedCardSection />

      {/* =========================================================================
          NEW SECTION 2: COMPREHENSIVE FREQUENTLY ASKED QUESTIONS (FAQ)
          ========================================================================= */}
      <section style={{ padding: '68px 0', backgroundColor: 'var(--ux4g-bg)', borderTop: '1px solid var(--ux4g-border)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 40px' }}>
            <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Common Inquiries
            </span>
            <TextMaskReveal
              as="h2"
              lines={["Frequently Asked Questions"]}
              style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginTop: '8px', marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.98rem' }}>
              Transparent answers regarding data privacy, human-in-the-loop governance, and citizen protections.
            </p>
          </div>

          <div style={{ maxWidth: '860px', margin: '0 auto' }}>
            <UX4GAccordion items={faqItems} allowMultiple={false} />
          </div>
        </div>
      </section>


    </div>
  );
};
