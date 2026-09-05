import React, { useState } from 'react';
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

export const HomePage = () => {
  const { isAuthenticated, currentUser, getDashboardPath } = useAuth();
  const { openOffcanvas, reducedMotion, toggleReducedMotion } = useThemeAccessibility();
  const [demoActiveInput, setDemoActiveInput] = useState('');

  const workflowSteps = [
    {
      stepNumber: 1,
      title: 'Multimodal Interaction',
      subtitle: 'Safe, consensual check-in via speech audio or text',
      content: (
        <div>
          <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>
            Victims and beneficiaries interact at their chosen safe hour and channel using conversational voice or text prompts, supported in multiple regional languages without intrusive surveillance.
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="ux4g-badge ux4g-badge-primary">Bilingual ASR Pipeline</span>
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
            When escalation probability passes verified thresholds, proactive flags alert authorized clinical counsellors and district nodal officers with explainable contributing factors.
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
      subtitle: 'Closed-loop accountability through District & State SLAs',
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
      title: 'How does AAROH protect victim privacy under the DPDP Act 2023?',
      subtitle: 'Statutory citizen privacy rights & cryptographic security',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          All citizen interactions require unambiguous, revocable consent. Data is encrypted using AES-256 at rest and stored exclusively in sovereign Indian government servers. Audio files are processed through a confidential pipeline with de-identification so that only authorized trauma counsellors assigned to your specific case can access records.
        </p>
      ),
    },
    {
      id: 'faq-2',
      title: 'Can the AI take punitive or legal decisions on its own?',
      subtitle: 'Human-in-the-loop ethical AI guarantee',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          <strong>No, strictly never.</strong> Under Section 23 of the AAROH mandate, artificial intelligence is strictly assistive. It flags potential distress shifts to human officials. All decisions regarding compensation, protective relocation, clinical diagnoses, and legal aid are made exclusively by licensed psychologists, magistrates, and welfare authorities.
        </p>
      ),
    },
    {
      id: 'faq-3',
      title: 'What happens if a beneficiary misses a scheduled check-in?',
      subtitle: 'Non-punitive welfare protocols',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          Missing a check-in is never treated as a penalty or violation. The system respects personal space. If multiple consecutive check-ins are missed during a high-risk recovery phase, the assigned counsellor gently reaches out during the beneficiary's registered "safe hours" to ensure their safety and well-being.
        </p>
      ),
    },
    {
      id: 'faq-4',
      title: 'How is distress scored without intrusive surveillance?',
      subtitle: 'Dynamic baseline deviation vs. surveillance',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          AAROH does not perform general social monitoring or tracking. It only evaluates consensual check-in sessions. Acoustic pitch variance, speaking rate, and linguistic emotional markers are compared against the beneficiary's own self-established baseline, allowing gentle tracking without intrusive device access.
        </p>
      ),
    },
    {
      id: 'faq-5',
      title: 'Who has access to my case records?',
      subtitle: 'Role-Based Access Control (RBAC) boundaries',
      content: (
        <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.9rem', lineHeight: '1.65' }}>
          Access is strictly compartmentalized. Only your assigned clinical counsellor and the designated District Nodal Officer have visibility into your active case details. State and National directorates only view anonymized, aggregated statistics to monitor overall welfare performance.
        </p>
      ),
    },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* =========================================================================
          HERO SECTION with Text Mask Reveal & 3D Kinetic Tilt
          ========================================================================= */}
      <section
        style={{
          background: 'linear-gradient(180deg, #F3EFFE 0%, #F8F9FE 100%)',
          padding: '64px 0 56px',
          borderBottom: '1px solid var(--ux4g-border)',
          position: 'relative',
        }}
      >
        <div className="container">
          {/* Official Gov Tag */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <span
              style={{
                backgroundColor: 'var(--ux4g-surface)',
                color: 'var(--ux4g-violet-800)',
                fontSize: '0.78rem',
                fontWeight: 700,
                padding: '4px 12px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--ux4g-violet-200)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: 'var(--elevation-1)',
              }}
            >
              <Shield size={14} color="var(--ux4g-violet-700)" />
              National Welfare & Mental Health Initiative
            </span>

            <span
              style={{
                backgroundColor: 'var(--ux4g-success-bg)',
                color: 'var(--ux4g-success-text)',
                fontSize: '0.78rem',
                fontWeight: 600,
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--ux4g-success-border)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}
            >
              <CheckCircle2 size={13} />
              DPDP Act 2023 Compliant
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '48px', alignItems: 'center' }}>
            {/* Hero Left Column with Text Mask Reveal */}
            <div>
              <TextMaskReveal
                as="h1"
                lines={[
                  "AAROH Platform",
                  "AI-Powered Dynamic Mental Health",
                  "Monitoring & Distress Prediction"
                ]}
                style={{
                  fontSize: 'clamp(2.1rem, 4.2vw, 3.2rem)',
                  fontWeight: 800,
                  color: 'var(--ux4g-violet-950)',
                  lineHeight: '1.16',
                  letterSpacing: '-0.025em',
                  marginBottom: '18px',
                }}
              />

              <p
                style={{
                  fontSize: '1.05rem',
                  color: 'var(--ux4g-text-secondary)',
                  lineHeight: '1.65',
                  marginBottom: '28px',
                  maxWidth: '560px',
                }}
              >
                A proactive, government-grade psychological support infrastructure built to identify escalating distress in victims of atrocities through consensual multimodal interactions, enabling timely human intervention and holistic rehabilitation.
              </p>

              {/* CTAs */}
              <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '24px' }}>
                {isAuthenticated ? (
                  <Link to={getDashboardPath(currentUser.role)} style={{ textDecoration: 'none' }}>
                    <UX4GButton variant="primary" size="lg" icon={ArrowRight} iconPosition="right">
                      Go to {currentUser.role} Portal
                    </UX4GButton>
                  </Link>
                ) : (
                  <Link to="/signin" style={{ textDecoration: 'none' }}>
                    <UX4GButton variant="primary" size="lg" icon={ArrowRight} iconPosition="right">
                      Sign In to Authorized Portal
                    </UX4GButton>
                  </Link>
                )}

                <button
                  type="button"
                  onClick={() => {
                    openOffcanvas({
                      title: 'AAROH Rapid Emergency Support',
                      subtitle: '24x7 crisis intervention and victim helpline contacts',
                      type: 'emergency',
                    });
                  }}
                  className="ux4g-focus-glow"
                  style={{
                    backgroundColor: 'var(--ux4g-surface)',
                    color: 'var(--ux4g-violet-900)',
                    border: '1.5px solid var(--ux4g-violet-300)',
                    padding: '12px 22px',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.98rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: 'var(--elevation-1)',
                    transition: 'var(--transition-fast)',
                  }}
                >
                  <PhoneCall size={18} color="var(--ux4g-danger)" />
                  <span>Immediate Crisis Support</span>
                </button>
              </div>

              {/* Security Banner Note */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.825rem', color: 'var(--ux4g-text-muted)' }}>
                <Lock size={14} />
                <span>Restricted Government System. <strong>No public registration.</strong> Authorized sign-in only.</span>
              </div>
            </div>

            {/* Hero Right Column: 3D Kinetic Tilt Card */}
            <div>
              <KineticTiltCard maxTilt={14} elevation={3}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', paddingBottom: '12px', borderBottom: '1px solid var(--ux4g-border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--ux4g-success)' }} />
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Operational Framework
                    </span>
                  </div>
                  <span className="ux4g-badge ux4g-badge-primary">3D Kinetic Tilt</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', padding: '12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--ux4g-violet-50)', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Brain size={20} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                        AI Distress Modeling
                      </h4>
                      <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                        Multimodal speech & linguistic feature analysis with individualized baseline deviation scoring.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', padding: '12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: '#ECFDF5', color: 'var(--ux4g-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <HeartHandshake size={20} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                        Human-Centered Care
                      </h4>
                      <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                        Certified clinical counsellors and district social justice authorities take all final care actions.
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start', padding: '12px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--ux4g-saffron-50)', color: 'var(--ux4g-saffron-500)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Shield size={20} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                        SLA-Bound Interventions
                      </h4>
                      <p style={{ fontSize: '0.82rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                        Transparent escalation routing across District, State, and National tiers with strict audit logging.
                      </p>
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '18px', paddingTop: '14px', borderTop: '1px solid var(--ux4g-border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: 'var(--ux4g-text-muted)' }}>
                    <Clock size={13} />
                    <span>Average triage response: &lt; 2 hours</span>
                  </div>
                  <RiskBadge level="Low" size="sm" />
                </div>
              </KineticTiltCard>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          CONTENT DIVIDER: SEAMLESS INFINITE MARQUEE TICKER
          ========================================================================= */}
      <MarqueeTicker speed={28} />

      {/* =========================================================================
          STAGGERED BENTO GRID: REVOLUTIONARY SYSTEM CAPABILITIES
          ========================================================================= */}
      <section id="about" style={{ padding: '72px 0', backgroundColor: '#FFFFFF' }}>
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
              A modern, staggered Bento Grid showcasing the technological pillars that make AAROH a sovereign, trustworthy platform.
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
                  <div style={{ width: '46px', height: '46px', borderRadius: '12px', backgroundColor: '#ECFDF5', color: 'var(--ux4g-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                    <Volume2 size={24} />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                    Multimodal Speech ASR
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.85rem', lineHeight: '1.6' }}>
                    Inclusive spoken voice check-ins for citizens across diverse educational backgrounds and dialects.
                  </p>
                </div>
                <span className="ux4g-badge" style={{ backgroundColor: '#DBEAFE', color: '#1E40AF' }}>22 Indian Languages</span>
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
                    Statutory District & State Governance
                  </h3>
                  <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.92rem', lineHeight: '1.65', marginBottom: '16px' }}>
                    Connects District Magistrates, Social Justice Commissioners, and the Central Ministry in a single unified dashboard, guaranteeing swift caseworker allocation and statutory SLA adherence.
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
          NEW SECTION 1: STATUTORY 4-PILLAR REHABILITATION FRAMEWORK
          ========================================================================= */}
      <section style={{ padding: '68px 0', backgroundColor: 'var(--ux4g-bg)', borderTop: '1px solid var(--ux4g-border)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 44px' }}>
            <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Statutory Welfare Model
            </span>
            <TextMaskReveal
              as="h2"
              lines={["The 4 Pillars of Atrocity Relief & Recovery"]}
              style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginTop: '8px', marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.98rem' }}>
              A holistic ecosystem connecting psychological stabilization with physical safety, legal justice, and economic rehabilitation.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '22px' }}>
            {/* Pillar 1 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: '#F3EFFE', color: 'var(--ux4g-violet-700)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Heart size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                1. Psychological Trauma Relief
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Integration with the national Tele-MANAS network, trauma-informed clinical psychologists, and compassionate individual counseling.
              </p>
            </KineticTiltCard>

            {/* Pillar 2 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: '#ECFDF5', color: 'var(--ux4g-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Shield size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                2. Witness & Physical Security
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Direct linkage to District Magistrate protection protocols, safe housing shelter routing, and emergency escalation to 112 services.
              </p>
            </KineticTiltCard>

            {/* Pillar 3 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: 'var(--ux4g-saffron-50)', color: 'var(--ux4g-saffron-500)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Landmark size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                3. Compensation & Relief Funds
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Tracking of statutory compensation disbursements under the SC/ST Prevention of Atrocities rules directly to citizen bank accounts.
              </p>
            </KineticTiltCard>

            {/* Pillar 4 */}
            <KineticTiltCard maxTilt={10} elevation={1} padding="24px">
              <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: '#EFF6FF', color: '#1D4ED8', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Scale size={22} />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
                4. Judicial Legal Aid Liaison
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6 }}>
                Fast-track court psychosocial assessment reporting and representation assistance through National Legal Services Authority (NALSA).
              </p>
            </KineticTiltCard>
          </div>
        </div>
      </section>

      {/* How AAROH Works: Journey Stepper with Smooth Collapsibles */}
      <section id="workflow" style={{ padding: '68px 0', backgroundColor: '#FFFFFF' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 40px' }}>
            <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 700, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Process Architecture
            </span>
            <TextMaskReveal
              as="h2"
              lines={["How AAROH Operates (The 6-Step Care Cycle)"]}
              style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginTop: '8px', marginBottom: '12px' }}
            />
            <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.98rem' }}>
              Explore the end-to-end workflow from citizen check-in to clinical resolution. Built with UX4G Smooth Collapsibles.
            </p>
          </div>

          <div style={{ maxWidth: '860px', margin: '0 auto' }}>
            <UX4GAccordion items={workflowSteps} allowMultiple={false} />
          </div>
        </div>
      </section>

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

      {/* UX4G Design System & Micro-Interactions Showcase */}
      <section style={{ padding: '60px 0', backgroundColor: '#FFFFFF', borderTop: '1px solid var(--ux4g-border)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '16px', marginBottom: '32px' }}>
            <div>
              <span className="ux4g-badge ux4g-badge-primary" style={{ marginBottom: '8px' }}>
                Interactive Motion Foundation
              </span>
              <TextMaskReveal
                as="h2"
                lines={["Micro-Interactions & Animation Verification"]}
                style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--ux4g-violet-950)' }}
              />
              <p style={{ color: 'var(--ux4g-text-secondary)', fontSize: '0.92rem', marginTop: '4px' }}>
                Test the 4-level elevated hover lifting, Focus Mode Glow, 3D Kinetic Tilt, Offcanvas flyouts, and Universal Motion Toggle directly.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <UX4GButton
                variant={reducedMotion ? 'primary' : 'outline'}
                size="sm"
                icon={Sliders}
                onClick={toggleReducedMotion}
              >
                Motion Toggle: {reducedMotion ? 'Reduced Motion (ON)' : 'Animations Active'}
              </UX4GButton>

              <UX4GButton
                variant="secondary"
                size="sm"
                icon={Sparkles}
                onClick={() => {
                  openOffcanvas({
                    title: 'UX4G Offcanvas Flyout Drawer',
                    subtitle: 'Demonstrating frictionless side-drawer sliding animation',
                    type: 'showcase',
                  });
                }}
              >
                Test Offcanvas Flyout Glide
              </UX4GButton>
            </div>
          </div>

          {/* Demonstration Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', marginBottom: '32px' }}>
            <UX4GCard elevation={1} liftOnHover={true} hoverElevation={2}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-700)' }}>Level 1 Elevation</span>
                <span className="ux4g-badge ux4g-badge-low">Lifts to L2</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                Base card with subtle 1px border. Hover over to inspect smooth box-shadow elevation lift.
              </p>
              <RiskBadge level="Low" size="sm" />
            </UX4GCard>

            <UX4GCard elevation={2} liftOnHover={true} hoverElevation={3}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-700)' }}>Level 2 Elevation</span>
                <span className="ux4g-badge ux4g-badge-medium">Lifts to L3</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                Raised dashboard container shadow with lavender ambient glow on interaction.
              </p>
              <RiskBadge level="Medium" size="sm" />
            </UX4GCard>

            <UX4GCard elevation={3} liftOnHover={true} hoverElevation={4}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-700)' }}>Level 3 Elevation</span>
                <span className="ux4g-badge ux4g-badge-high">Lifts to L4</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                Prominent priority cards with deeper depth-of-field and smooth cubic-bezier transition.
              </p>
              <RiskBadge level="High" size="sm" />
            </UX4GCard>

            <UX4GCard elevation={4} liftOnHover={false}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--ux4g-violet-700)' }}>Level 4 Elevation</span>
                <span className="ux4g-badge ux4g-badge-critical">Maximum Depth</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                Used for floating dialogs, offcanvas drawers, and high-urgency triage overlays.
              </p>
              <RiskBadge level="Critical" size="sm" />
            </UX4GCard>
          </div>

          {/* Focus Mode Glow Interactive Input Showcase */}
          <div style={{ padding: '24px', backgroundColor: 'var(--ux4g-bg)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--ux4g-border)' }}>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '6px' }}>
              Focus Mode Glow Demonstration
            </h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginBottom: '16px' }}>
              Click inside the field below to observe the subtle expanding lavender-violet focus ring:
            </p>
            <div style={{ maxWidth: '480px' }}>
              <input
                type="text"
                value={demoActiveInput}
                onChange={(e) => setDemoActiveInput(e.target.value)}
                placeholder="Click here to trigger Focus Mode Glow..."
                className="ux4g-focus-glow"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1.5px solid var(--ux4g-border)',
                  backgroundColor: '#FFFFFF',
                  fontSize: '0.95rem',
                  color: 'var(--ux4g-text-primary)',
                }}
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
