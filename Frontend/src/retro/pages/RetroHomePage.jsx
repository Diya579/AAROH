import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowRight, 
  Mic, 
  Activity, 
  ShieldCheck, 
  Clock, 
  FileText, 
  HeartHandshake, 
  Radio, 
  ChevronDown, 
  AlertCircle,
  Sparkles,
  Award
} from 'lucide-react';
import { RetroTiltCard } from '../components/RetroTiltCard';
import { RetroStamp } from '../components/RetroStamp';
import { RetroTicker } from '../components/RetroTicker';
import { caseService } from '../../services/caseService';
import { analyticsService } from '../../services/analyticsService';

export const RetroHomePage = () => {
  const [cases, setCases] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [expandedStep, setExpandedStep] = useState(1);

  useEffect(() => {
    async function loadData() {
      try {
        const caseList = await caseService.getCases();
        setCases(caseList.slice(0, 3)); // Featured top 3 dispatches

        const stats = await analyticsService.getDistrictAnalytics('South Delhi');
        setAnalytics(stats);
      } catch (err) {
        console.error('Error loading gazette data:', err);
      }
    }
    loadData();
  }, []);

  const editorialSteps = [
    {
      num: 'I',
      title: 'Consensual Multimodal Check-in',
      subtitle: 'Speech audio and text recorded strictly within the citizen’s designated safe hours',
      desc: 'Survivors interact via conversational speech audio or text questionnaires at their chosen daily window. The pipeline utilizes bilingual Hindi and English Automatic Speech Recognition (ASR) with explicit cryptographic consent verification.',
      stamp: 'INPUT PROTOCOL',
    },
    {
      num: 'II',
      title: 'Acoustic & Dynamic Baseline Calibration',
      subtitle: 'Algorithmic assessment relative to calibrated 30-day personal baseline',
      desc: 'Instead of applying blunt statistical averages, AAROH measures pitch perturbation (jitter), voice shimmer, and linguistic fear markers against the survivor’s individual baseline to flag genuine distress spikes.',
      stamp: 'AI SEISMOGRAPH',
    },
    {
      num: 'III',
      title: 'Clinical SLA Dispatch & Triage',
      subtitle: 'Automated urgency tiering with strict response deadlines',
      desc: 'Cases with severe distress deviation are routed instantly to assigned clinical psychologists and district legal officers, enforced by countdown SLAs: Emergency (≤2h), Urgent (≤4h), Standard (≤24h), and Routine.',
      stamp: 'SLA ENFORCEMENT',
    },
    {
      num: 'IV',
      title: 'Holistic Multi-Agency Rehabilitation',
      subtitle: 'Coordinated psychological, legal, and witness protection interventions',
      desc: 'Seamless inter-agency handoffs integrate Tele-MANAS mental health counselling, NALSA legal aid, witness protection relocation, and state victim compensation funds under SC/ST PoA mandates.',
      stamp: 'FULL RESOLUTION',
    },
  ];

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Ticker Tape */}
      <div style={{ marginBottom: '24px' }}>
        <RetroTicker />
      </div>

      {/* Hero / Lead Headline Section */}
      <section style={{ marginBottom: '40px' }}>
        <div
          style={{
            border: '2.5px solid var(--retro-ink-black)',
            backgroundColor: 'var(--retro-bg-paper-light)',
            padding: '32px 28px',
            boxShadow: 'var(--retro-shadow-lg)',
            position: 'relative',
          }}
        >
          {/* Top Headline Tag */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1.5px solid var(--retro-ink-black)',
              paddingBottom: '10px',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <RetroStamp type="urgent" label="FRONT-PAGE LEAD" size="sm" />
              <span
                style={{
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                SPECIAL DISPATCH • SECTION 15A STATUTORY FRAMEWORK
              </span>
            </div>
            <span
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.75rem',
                color: 'var(--retro-ink-faint)',
              }}
            >
              CIRCULATION: ALL 766 DISTRICT BUREAUS
            </span>
          </div>

          {/* Grand Banner Headline */}
          <h2 className="retro-headline-lg" style={{ textAlign: 'center', margin: '14px 0 16px 0' }}>
            AI-POWERED DISTRESS PREDICTION DEPLOYED TO SHIELD ATROCITY SURVIVORS
          </h2>

          <div
            style={{
              textAlign: 'center',
              fontFamily: 'var(--retro-font-serif)',
              fontStyle: 'italic',
              fontSize: '1.15rem',
              color: 'var(--retro-ink-muted)',
              marginBottom: '24px',
            }}
          >
            "A sovereign algorithmic safety net measuring psychological shifts, acoustic tremors, and linguistic signals to avert trauma escalation before it occurs."
          </div>

          <div className="retro-rule-double" />

          {/* Multi-Column Newspaper Article */}
          <div className="retro-columns-2" style={{ marginBottom: '24px' }}>
            <p className="retro-dropcap retro-typewriter">
              Last week, the Central Clinical & Rehabilitation Bureau marked a pivotal milestone with the operational deployment of the AAROH dynamic monitoring architecture. Built to uphold statutory directives under the Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, the platform continuously interprets consensual survivor check-ins without intrusive electronic surveillance.
            </p>
            <p className="retro-typewriter">
              By combining calibrated voice acoustic analysis (pitch perturbation, speech latency, harmonic perturbation) with multilingual linguistic sentiment models, the system flags high-probability distress spikes with an unprecedented 89% clinical confidence rating. Emergency interventions are tied directly to statutory countdown SLAs, guaranteeing that no victim faces psychological distress alone.
            </p>
          </div>

          {/* Call to Actions */}
          <div
            style={{
              display: 'flex',
              gap: '14px',
              justifyContent: 'center',
              flexWrap: 'wrap',
              paddingTop: '12px',
              borderTop: '1px solid var(--retro-border-light)',
            }}
          >
            <Link to="/retro/victim" className="retro-btn retro-btn-urgent">
              <span>ENTER BENEFICIARY CHECK-IN</span>
              <ArrowRight size={14} />
            </Link>
            <Link to="/retro/counsellor" className="retro-btn">
              <span>CHIEF EDITOR & CLINICAL BUREAU</span>
              <ArrowRight size={14} />
            </Link>
            <Link to="/retro/analytics" className="retro-btn">
              <span>VIEW STATISTICAL SUPPLEMENT</span>
              <Activity size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* Bento Newspaper Feature Grid (Tactile 3D Tilt Cards) */}
      <section style={{ marginBottom: '48px' }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <span
            style={{
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--retro-ink-muted)',
            }}
          >
            ✦ THE FOUR PILLARS OF SURVEILLANCE & TRIAGE ✦
          </span>
          <h3 className="retro-headline-md" style={{ marginTop: '6px' }}>
            Anatomy of the AAROH Autonomous Safety Net
          </h3>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px',
          }}
        >
          {/* Bento Card 1: Multimodal Acoustic Pipeline */}
          <RetroTiltCard cardboard>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <Mic size={24} style={{ color: 'var(--retro-stamp-red)' }} />
              <RetroStamp type="urgent" label="VOICE PIPELINE" size="sm" />
            </div>
            <h4
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.25rem',
                fontWeight: 800,
                marginBottom: '8px',
              }}
            >
              Acoustic Jitter & Voice Paralinguistics
            </h4>
            <p className="retro-typewriter" style={{ fontSize: '0.82rem', marginBottom: '14px' }}>
              Extracts micro-tremors in pitch, decibel variability, and speech cadence deceleration to screen for acute trauma even when verbal responses are guarded.
            </p>
            <div
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.72rem',
                backgroundColor: 'var(--retro-bg-paper-light)',
                padding: '6px 8px',
                border: '1px solid var(--retro-ink-black)',
              }}
            >
              TELE-MANAS 14416 • HINDI & ENGLISH ASR
            </div>
          </RetroTiltCard>

          {/* Bento Card 2: Dynamic Baseline Seismograph */}
          <RetroTiltCard paper>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <Activity size={24} style={{ color: 'var(--retro-stamp-green)' }} />
              <RetroStamp type="verified" label="CALIBRATED" size="sm" />
            </div>
            <h4
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.25rem',
                fontWeight: 800,
                marginBottom: '8px',
              }}
            >
              Personal Baseline Calibration
            </h4>
            <p className="retro-typewriter" style={{ fontSize: '0.82rem', marginBottom: '14px' }}>
              Scores are never compared to generic populations. Each survivor’s 30-day baseline prevents false positives while pinpointing sudden +15% distress spikes.
            </p>
            <div
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.72rem',
                backgroundColor: 'var(--retro-bg-cardboard)',
                padding: '6px 8px',
                border: '1px solid var(--retro-ink-black)',
              }}
            >
              30-DAY CALIBRATION • ROLLING INDEX
            </div>
          </RetroTiltCard>

          {/* Bento Card 3: Statutory SLA Clockwork */}
          <RetroTiltCard cardboard>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <Clock size={24} style={{ color: 'var(--retro-stamp-amber)' }} />
              <RetroStamp type="amber" label="STRICT SLA" size="sm" />
            </div>
            <h4
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.25rem',
                fontWeight: 800,
                marginBottom: '8px',
              }}
            >
              Clockwork Intervention Deadlines
            </h4>
            <p className="retro-typewriter" style={{ fontSize: '0.82rem', marginBottom: '14px' }}>
              Emergency (≤2 Hours), Urgent (≤4 Hours), Standard (≤24 Hours). Escalation protocols automatically trigger secondary senior psychologists if SLA thresholds near expiration.
            </p>
            <div
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.72rem',
                backgroundColor: 'var(--retro-bg-paper-light)',
                padding: '6px 8px',
                border: '1px solid var(--retro-ink-black)',
              }}
            >
              ZERO CURRENT OVERDUE BREACHES
            </div>
          </RetroTiltCard>

          {/* Bento Card 4: Safe Hours & Sovereign Privacy */}
          <RetroTiltCard paper>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <ShieldCheck size={24} style={{ color: 'var(--retro-stamp-blue)' }} />
              <RetroStamp type="sovereign" label="SECURE" size="sm" />
            </div>
            <h4
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.25rem',
                fontWeight: 800,
                marginBottom: '8px',
              }}
            >
              Sovereign Safe Hours Vault
            </h4>
            <p className="retro-typewriter" style={{ fontSize: '0.82rem', marginBottom: '14px' }}>
              Notifications and check-in windows occur strictly within user-configured safe hours (e.g. 17:00 – 19:00 IST), eliminating domestic surveillance risks.
            </p>
            <div
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.72rem',
                backgroundColor: 'var(--retro-bg-cardboard)',
                padding: '6px 8px',
                border: '1px solid var(--retro-ink-black)',
              }}
            >
              ZERO UNSOLICITED REACH-OUT
            </div>
          </RetroTiltCard>
        </div>
      </section>

      {/* Featured Telegram Dispatch Desk (Consuming caseService.js Data) */}
      <section style={{ marginBottom: '48px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            borderBottom: '2px solid var(--retro-ink-black)',
            paddingBottom: '8px',
            marginBottom: '20px',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={16} style={{ color: 'var(--retro-stamp-red)' }} />
              <span
                style={{
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                }}
              >
                LIVE TELEGRAPHIC LOG
              </span>
            </div>
            <h3 className="retro-headline-md" style={{ margin: '4px 0 0 0' }}>
              Active Clinical Dossiers
            </h3>
          </div>

          <Link to="/retro/counsellor" className="retro-btn" style={{ fontSize: '0.75rem' }}>
            <span>VIEW ALL 142 DOSSIERS IN BUREAU</span>
            <ArrowRight size={13} />
          </Link>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {cases.map((c) => (
            <motion.div
              key={c.id}
              whileHover={{ y: -2 }}
              style={{
                backgroundColor: 'var(--retro-bg-paper)',
                border: '2px solid var(--retro-ink-black)',
                boxShadow: 'var(--retro-shadow-sm)',
                padding: '18px 20px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
                alignItems: 'center',
              }}
            >
              {/* Column 1: Identification */}
              <div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--retro-font-mono)',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      backgroundColor: 'var(--retro-bg-cardboard-dark)',
                      padding: '2px 6px',
                      border: '1px solid var(--retro-ink-black)',
                    }}
                  >
                    {c.id}
                  </span>
                  <RetroStamp
                    type={c.priority === 'HIGH' ? 'urgent' : 'verified'}
                    label={c.riskLevel.toUpperCase()}
                    size="sm"
                  />
                </div>
                <div style={{ fontFamily: 'var(--retro-font-headline)', fontWeight: 700, fontSize: '1.05rem' }}>
                  {c.beneficiaryName}
                </div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', color: 'var(--retro-ink-muted)' }}>
                  District: {c.district}, {c.state} • Registered: {c.registrationDate}
                </div>
              </div>

              {/* Column 2: Distress Seismograph Index */}
              <div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', color: 'var(--retro-ink-muted)' }}>
                  DISTRESS SCORE / DEVIATION
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--retro-font-headline)',
                      fontSize: '1.6rem',
                      fontWeight: 900,
                      color: c.distressScore > 70 ? 'var(--retro-stamp-red)' : 'var(--retro-ink-black)',
                    }}
                  >
                    {c.distressScore}/100
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--retro-font-mono)',
                      fontSize: '0.85rem',
                      fontWeight: 800,
                      color: c.baselineDeviation.startsWith('+') ? 'var(--retro-stamp-red)' : 'var(--retro-stamp-green)',
                    }}
                  >
                    {c.baselineDeviation} vs Baseline
                  </span>
                </div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.72rem', color: 'var(--retro-ink-charcoal)' }}>
                  Trajectory: <strong>{c.trend}</strong> • Escalation Prob: <strong>{c.escalationProbability}</strong>
                </div>
              </div>

              {/* Column 3: SLA Countdown & Official */}
              <div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', color: 'var(--retro-ink-muted)' }}>
                  SLA TIMER & ASSIGNED OFFICIAL
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: '4px 0' }}>
                  <Clock size={13} style={{ color: 'var(--retro-stamp-amber)' }} />
                  <span style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.85rem', fontWeight: 800 }}>
                    {c.slaHoursRemaining} Hours Remaining ({c.slaStatus})
                  </span>
                </div>
                <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem' }}>
                  {c.assignedOfficial}
                </div>
              </div>

              {/* Column 4: Action */}
              <div style={{ textAlign: 'right' }}>
                <Link
                  to="/retro/counsellor"
                  className="retro-btn"
                  style={{ fontSize: '0.75rem', padding: '8px 14px' }}
                >
                  <span>INSPECT DOSSIER</span>
                  <ArrowRight size={13} />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Accordion: How AAROH Works (Tactile Paper Fold) */}
      <section style={{ marginBottom: '48px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <span
            style={{
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.8rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              color: 'var(--retro-ink-muted)',
            }}
          >
            ✦ OPERATIONAL PROTOCOL ✦
          </span>
          <h3 className="retro-headline-md">Four Steps of Statutory Protection</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {editorialSteps.map((step, idx) => {
            const isSelected = expandedStep === idx + 1;
            return (
              <div
                key={step.num}
                style={{
                  border: '2px solid var(--retro-ink-black)',
                  backgroundColor: isSelected ? 'var(--retro-bg-paper-light)' : 'var(--retro-bg-paper)',
                  boxShadow: isSelected ? 'var(--retro-shadow-md)' : 'var(--retro-shadow-sm)',
                  transition: 'all 0.2s ease',
                }}
              >
                <div
                  onClick={() => setExpandedStep(isSelected ? null : idx + 1)}
                  style={{
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <span
                      style={{
                        fontFamily: 'var(--retro-font-headline)',
                        fontSize: '1.4rem',
                        fontWeight: 900,
                        width: '32px',
                      }}
                    >
                      {step.num}.
                    </span>
                    <div>
                      <h4
                        style={{
                          fontFamily: 'var(--retro-font-headline)',
                          fontSize: '1.15rem',
                          fontWeight: 800,
                          margin: 0,
                        }}
                      >
                        {step.title}
                      </h4>
                      <p
                        style={{
                          fontFamily: 'var(--retro-font-mono)',
                          fontSize: '0.78rem',
                          color: 'var(--retro-ink-muted)',
                          margin: '2px 0 0 0',
                        }}
                      >
                        {step.subtitle}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <RetroStamp type="verified" label={step.stamp} size="sm" />
                    <motion.div animate={{ rotate: isSelected ? 180 : 0 }} transition={{ duration: 0.2 }}>
                      <ChevronDown size={18} />
                    </motion.div>
                  </div>
                </div>

                {isSelected && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    style={{
                      padding: '0 20px 20px 66px',
                      borderTop: '1px dashed var(--retro-border-light)',
                    }}
                  >
                    <p className="retro-typewriter" style={{ marginTop: '12px' }}>
                      {step.desc}
                    </p>
                  </motion.div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Statistical Summary Strip (analyticsService.js) */}
      {analytics && (
        <section
          style={{
            border: '2px solid var(--retro-ink-black)',
            backgroundColor: 'var(--retro-bg-cardboard-dark)',
            padding: '24px',
            boxShadow: 'var(--retro-shadow-md)',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.78rem',
              fontWeight: 800,
              textTransform: 'uppercase',
              marginBottom: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span>STATISTICAL DISPATCH FOR {analytics.district.toUpperCase()} PILOT JURISDICTION</span>
            <RetroStamp type="verified" label="AUDITED DATA" size="sm" />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '16px',
              textAlign: 'center',
            }}
          >
            <div style={{ backgroundColor: 'var(--retro-bg-paper-light)', padding: '14px', border: '1.5px solid var(--retro-ink-black)' }}>
              <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2rem', fontWeight: 900 }}>
                {analytics.totalCases}
              </div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
                TOTAL BENEFICIARIES
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--retro-bg-paper-light)', padding: '14px', border: '1.5px solid var(--retro-ink-black)' }}>
              <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2rem', fontWeight: 900, color: 'var(--retro-stamp-red)' }}>
                {analytics.criticalCount + analytics.highCount}
              </div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
                CRITICAL & HIGH ALERTS
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--retro-bg-paper-light)', padding: '14px', border: '1.5px solid var(--retro-ink-black)' }}>
              <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2rem', fontWeight: 900, color: 'var(--retro-stamp-green)' }}>
                {analytics.completedInterventions}
              </div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
                COMPLETED RESOLUTIONS
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--retro-bg-paper-light)', padding: '14px', border: '1.5px solid var(--retro-ink-black)' }}>
              <div style={{ fontFamily: 'var(--retro-font-headline)', fontSize: '2rem', fontWeight: 900 }}>
                {analytics.overdueInterventions}
              </div>
              <div style={{ fontFamily: 'var(--retro-font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
                OVERDUE SLA BREACHES
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

export default RetroHomePage;
