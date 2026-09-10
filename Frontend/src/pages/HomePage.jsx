import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
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
              The technological pillars that make AAROH a sovereign, trustworthy platform.
            </p>
          </div>

          <BentoGrid columns={3} gap="24px">
            {/* Bento Item 1: Large Span Continuous Monitoring */}
            <BentoItem colSpan={2} rowSpan={1}>
              <motion.div
                initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
                whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: 0.6, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
                style={{ height: '100%' }}
              >
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
              </motion.div>
            </BentoItem>

            {/* Bento Item 2: Multimodal Speech ASR */}
            <BentoItem colSpan={1} rowSpan={1}>
              <motion.div
                initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
                whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
                style={{ height: '100%' }}
              >
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
              </motion.div>
            </BentoItem>

            {/* Bento Item 3: Early Escalation Alert */}
            <BentoItem colSpan={1} rowSpan={1}>
              <motion.div
                initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
                whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: 0.6, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
                style={{ height: '100%' }}
              >
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
              </motion.div>
            </BentoItem>

            {/* Bento Item 4: Coordinated Governance & SLAs */}
            <BentoItem colSpan={2} rowSpan={1}>
              <motion.div
                initial={reducedMotion ? {} : { opacity: 0, y: 32 }}
                whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.15 }}
                transition={{ duration: 0.6, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
                style={{ height: '100%' }}
              >
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
              </motion.div>
            </BentoItem>
          </BentoGrid>
        </div>
      </section>

      {/* =========================================================================
          NEW SECTION 1: STATUTORY 4-PILLAR REHABILITATION FRAMEWORK
          ========================================================================= */}
      <section id="safety" style={{ padding: '68px 0', backgroundColor: 'var(--ux4g-bg)', borderTop: '1px solid var(--ux4g-border)' }}>
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
            <motion.div
              initial={reducedMotion ? {} : { opacity: 0, y: 34, scale: 0.98 }}
              whileInView={reducedMotion ? {} : { opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ duration: 0.55, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
              whileHover={reducedMotion ? {} : { y: -6, transition: { duration: 0.25, ease: 'easeOut' } }}
            >
              <KineticTiltCard maxTilt={10} elevation={1} padding="24px" style={{ height: '100%' }}>
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
            </motion.div>

            {/* Pillar 2 */}
            <motion.div
              initial={reducedMotion ? {} : { opacity: 0, y: 34, scale: 0.98 }}
              whileInView={reducedMotion ? {} : { opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ duration: 0.55, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
              whileHover={reducedMotion ? {} : { y: -6, transition: { duration: 0.25, ease: 'easeOut' } }}
            >
              <KineticTiltCard maxTilt={10} elevation={1} padding="24px" style={{ height: '100%' }}>
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
            </motion.div>

            {/* Pillar 3 */}
            <motion.div
              initial={reducedMotion ? {} : { opacity: 0, y: 34, scale: 0.98 }}
              whileInView={reducedMotion ? {} : { opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ duration: 0.55, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
              whileHover={reducedMotion ? {} : { y: -6, transition: { duration: 0.25, ease: 'easeOut' } }}
            >
              <KineticTiltCard maxTilt={10} elevation={1} padding="24px" style={{ height: '100%' }}>
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
            </motion.div>

            {/* Pillar 4 */}
            <motion.div
              initial={reducedMotion ? {} : { opacity: 0, y: 34, scale: 0.98 }}
              whileInView={reducedMotion ? {} : { opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{ duration: 0.55, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
              whileHover={reducedMotion ? {} : { y: -6, transition: { duration: 0.25, ease: 'easeOut' } }}
            >
              <KineticTiltCard maxTilt={10} elevation={1} padding="24px" style={{ height: '100%' }}>
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
            </motion.div>
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

          <motion.div
            initial={reducedMotion ? {} : { opacity: 0, y: 28 }}
            whileInView={reducedMotion ? {} : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.15 }}
            transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
            style={{ maxWidth: '860px', margin: '0 auto' }}
          >
            <UX4GAccordion items={faqItems} allowMultiple={false} />
          </motion.div>
        </div>
      </section>


    </div>
  );
};
