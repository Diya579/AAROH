import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Shield, ArrowRight, PhoneCall, CheckCircle2,
  Brain, HeartHandshake, Clock, Lock,
} from 'lucide-react';
import { RiskBadge } from '../common/UX4GBadge';
import { KineticTiltCard } from './KineticTiltCard';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { useAuth } from '../../context/AuthContext';

/* ─── Operational Framework Card content ────────────────────────────────── */
/* ─── Operational Framework Card content ────────────────────────────────── */
const OperationalCardContent = () => {
  const features = [
    {
      icon: <Brain size={20} />,
      bg: 'rgba(84,49,24,0.12)', color: '#543118',
      title: 'Acoustic Distress AI',
      desc: 'Multimodal vocal pitch variance & linguistic indicators calibrated to individual baselines.',
    },
    {
      icon: <HeartHandshake size={20} />,
      bg: 'rgba(68,63,36,0.14)', color: '#443F24',
      title: 'Human Clinical Care',
      desc: 'Certified psychologists and designated authorities take all final care actions.',
    },
    {
      icon: <Shield size={20} />,
      bg: 'rgba(162,104,41,0.14)', color: '#804F18',
      title: 'SLA-Bound Interventions',
      desc: 'Transparent triage dispatch across district and legal aid tiers with full cryptographic audit.',
    },
  ];

  return (
    <>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '16px', paddingBottom: '12px',
        borderBottom: '1.5px solid #3A2312',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '9px', height: '9px', borderRadius: '50%',
            backgroundColor: '#822710',
            boxShadow: '0 0 0 2px rgba(130,39,16,0.25)',
          }} />
          <span style={{
            fontSize: '0.8rem', fontWeight: 800,
            color: '#2B1508',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            fontFamily: '"Space Mono", "Courier Prime", monospace',
          }}>
            Paralinguistic Engine
          </span>
        </div>
        <span style={{
          fontSize: '0.68rem', fontWeight: 800,
          background: '#E6DAC9', color: '#3A2312',
          border: '1.5px solid #3A2312',
          padding: '2px 9px', borderRadius: '4px',
          letterSpacing: '0.06em',
          fontFamily: '"Space Mono", "Courier Prime", monospace',
        }}>
          ACTIVE • v2.4
        </span>
      </div>

      {/* Real-time Simulated Acoustic Waveform Strip */}
      <div style={{
        padding: '12px 14px',
        backgroundColor: '#E6DAC9',
        borderRadius: '8px',
        border: '1.5px solid #3A2312',
        marginBottom: '16px',
        boxShadow: '2px 2px 0px #3A2312',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#2B1508', fontFamily: '"Space Mono", monospace' }}>
            SPECTROGRAM STREAM
          </span>
          <span style={{ fontSize: '0.66rem', fontWeight: 700, color: '#822710', fontFamily: '"Space Mono", monospace' }}>
            F0: 194Hz • Jitter 0.38%
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', height: '32px', justifyContent: 'center' }}>
          {[14, 26, 10, 32, 20, 12, 34, 16, 24, 30, 14, 28, 18, 12, 30, 16, 22, 28, 16, 10].map((h, idx) => (
            <div
              key={idx}
              style={{
                width: '6px',
                height: `${h}px`,
                backgroundColor: idx % 4 === 0 ? '#822710' : '#543118',
                borderRadius: '3px',
                opacity: 0.9,
              }}
            />
          ))}
        </div>
      </div>

      {/* Feature rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
        {features.map((f, i) => (
          <div
            key={i}
            style={{
              display: 'flex', gap: '12px', alignItems: 'flex-start',
              padding: '10px 12px', borderRadius: '8px',
              backgroundColor: 'var(--ux4g-surface)',
              border: '1px solid #CDB397',
            }}
          >
            <div style={{
              width: '32px', height: '32px', borderRadius: '6px',
              background: f.bg, color: f.color,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {f.icon}
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#2B1508', fontFamily: '"Space Mono", monospace' }}>
                {f.title}
              </div>
              <div style={{ fontSize: '0.76rem', color: '#78604F', marginTop: '2px', lineHeight: '1.4' }}>
                {f.desc}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        paddingTop: '12px', borderTop: '1px solid var(--ux4g-border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.74rem', color: 'var(--ux4g-text-muted)' }}>
          <Clock size={12} />
          <span>Average triage response: &lt; 2 hours</span>
        </div>
        <RiskBadge level="Low" size="sm" />
      </div>
    </>
  );
};

/* ─── Main HeroSection ───────────────────────────────────────────────────── */
export const HeroSection = () => {
  const { reducedMotion, openOffcanvas } = useThemeAccessibility();
  const { isAuthenticated, currentUser, getDashboardPath } = useAuth();

  const [btnHover, setBtnHover] = useState(null);

  // Staggered pop-up variant for each headline line
  const lineVariant = {
    hidden: { opacity: 0, y: 15, scale: 0.95 },
    show:   { opacity: 1, y: 0,  scale: 1    },
  };
  const lineTransition = (delay) => ({
    duration: 0.52,
    delay,
    ease: [0.22, 1, 0.36, 1], // custom spring-feel ease
  });

  // Generic fade-up for other content blocks
  const fadeUp = {
    hidden: { opacity: 0, y: 22 },
    show:   { opacity: 1, y: 0  },
  };

  return (
    <section
      style={{
        background: 'linear-gradient(180deg, #E6DAC9 0%, #F4ECE0 100%)',
        padding: '64px 0 60px',
        borderBottom: '2px solid #3A2312',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Subtle decorative glow blobs (warm sepia) */}
      <div aria-hidden="true" style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute', top: '-120px', right: '-80px',
          width: '480px', height: '480px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(140,98,64,0.15) 0%, transparent 70%)',
          filter: 'blur(30px)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-80px', left: '-60px',
          width: '320px', height: '320px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(84,49,24,0.12) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }} />
      </div>

      <div className="container" style={{ position: 'relative', zIndex: 2 }}>
        {/* Editorial Trust Badges */}
        <motion.div
          initial="hidden" animate="show" variants={fadeUp}
          transition={{ duration: 0.45 }}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' }}
        >
          <span style={{
            backgroundColor: 'var(--ux4g-surface)',
            color: '#2B1508',
            fontSize: '0.76rem', fontWeight: 700,
            padding: '5px 14px', borderRadius: '8px',
            border: '1.5px solid #3A2312',
            boxShadow: '2px 2px 0px #3A2312',
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            fontFamily: '"Space Mono", "Courier Prime", monospace',
          }}>
            ✦ Autonomous Paralinguistic AI &amp; Human Care
          </span>
          <span style={{
            backgroundColor: 'var(--ux4g-success-bg)',
            color: 'var(--ux4g-success)',
            fontSize: '0.76rem', fontWeight: 700,
            padding: '5px 12px', borderRadius: '8px',
            border: '1.5px solid var(--ux4g-success-border)',
            display: 'inline-flex', alignItems: 'center', gap: '5px',
            fontFamily: '"Space Mono", "Courier Prime", monospace',
          }}>
            <CheckCircle2 size={12} />
            Privacy-Preserving DPDP Standard
          </span>
        </motion.div>

        {/* Two-column grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '52px',
          alignItems: 'center',
        }}>
          {/* ── LEFT ── */}
          <div>
            {/* Editorial Serif Headline */}
            <h1 style={{
              fontSize: 'clamp(2.4rem, 4.8vw, 4.2rem)',
              fontWeight: 900,
              lineHeight: '1.06',
              letterSpacing: '-0.025em',
              marginBottom: '22px',
              fontFamily: '"Fraunces", "Playfair Display", Georgia, serif',
              overflow: 'hidden',
            }}>
              <motion.span
                style={{ display: 'block', color: '#1C1108', fontStyle: 'italic' }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.08)}
              >
                Intelligent
              </motion.span>
              <motion.span
                style={{
                  display: 'block',
                  color: '#543118',
                }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.18)}
              >
                Distress Modeling.
              </motion.span>
              <motion.span
                style={{ display: 'block', color: '#1C1108' }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.28)}
              >
                Human-First Care.
              </motion.span>
            </h1>

            <motion.p
              initial="hidden" animate="show" variants={fadeUp}
              transition={{ duration: 0.6, delay: 0.2 }}
              style={{
                fontSize: '1.05rem',
                color: '#543118',
                lineHeight: '1.7',
                marginBottom: '32px',
                maxWidth: '540px',
                fontFamily: '"Space Mono", "Courier Prime", monospace',
              }}
            >
              A proactive psychological resilience platform combining paralinguistic acoustic modeling with certified clinical intervention — detecting longitudinal distress deviations and mobilizing rapid relief with zero automated penalties.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              initial="hidden" animate="show" variants={fadeUp}
              transition={{ duration: 0.6, delay: 0.32 }}
              style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '22px' }}
            >
              {isAuthenticated ? (
                <Link to={getDashboardPath(currentUser.role)} style={{ textDecoration: 'none' }}>
                  <button
                    type="button"
                    onMouseEnter={() => setBtnHover('primary')}
                    onMouseLeave={() => setBtnHover(null)}
                    style={{
                      background: btnHover === 'primary'
                        ? 'linear-gradient(90deg, #734828, #543118)'
                        : 'linear-gradient(90deg, #543118, #3E210E)',
                      color: '#FAF4EB',
                      border: '2px solid #2B180D',
                      padding: '13px 26px', borderRadius: '8px',
                      fontSize: '0.92rem', fontWeight: 800, cursor: 'pointer',
                      display: 'inline-flex', alignItems: 'center', gap: '8px',
                      boxShadow: btnHover === 'primary'
                        ? '5px 5px 0px #2B180D'
                        : '3px 3px 0px #2B180D',
                      transform: btnHover === 'primary' ? 'translate(-2px, -2px)' : 'none',
                      transition: 'all 0.18s ease',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      fontFamily: '"Space Mono", "Courier Prime", monospace',
                    }}
                  >
                    Go to {currentUser.role} Portal <ArrowRight size={18} />
                  </button>
                </Link>
              ) : (
                <Link to="/signin" style={{ textDecoration: 'none' }}>
                  <button
                    type="button"
                    onMouseEnter={() => setBtnHover('primary')}
                    onMouseLeave={() => setBtnHover(null)}
                    style={{
                      background: btnHover === 'primary'
                        ? 'linear-gradient(90deg, #734828, #543118)'
                        : 'linear-gradient(90deg, #543118, #3E210E)',
                      color: '#FAF4EB',
                      border: '2px solid #2B180D',
                      padding: '13px 26px', borderRadius: '8px',
                      fontSize: '0.92rem', fontWeight: 800, cursor: 'pointer',
                      display: 'inline-flex', alignItems: 'center', gap: '8px',
                      boxShadow: btnHover === 'primary'
                        ? '5px 5px 0px #2B180D'
                        : '3px 3px 0px #2B180D',
                      transform: btnHover === 'primary' ? 'translate(-2px, -2px)' : 'none',
                      transition: 'all 0.18s ease',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      fontFamily: '"Space Mono", "Courier Prime", monospace',
                    }}
                  >
                    Access Care Portal <ArrowRight size={18} />
                  </button>
                </Link>
              )}

              <button
                type="button"
                onMouseEnter={() => setBtnHover('crisis')}
                onMouseLeave={() => setBtnHover(null)}
                onClick={() => openOffcanvas({
                  title: 'AAROH Rapid Support Safe-Line',
                  subtitle: '24x7 crisis intervention and confidential support',
                  type: 'emergency',
                })}
                style={{
                  backgroundColor: btnHover === 'crisis' ? '#F8ECE7' : 'var(--ux4g-surface)',
                  color: 'var(--ux4g-danger)',
                  border: '2px solid var(--ux4g-danger)',
                  padding: '13px 22px', borderRadius: '8px',
                  fontSize: '0.88rem', fontWeight: 800, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: '8px',
                  boxShadow: btnHover === 'crisis'
                    ? '5px 5px 0px var(--ux4g-danger)'
                    : '3px 3px 0px var(--ux4g-danger)',
                  transform: btnHover === 'crisis' ? 'translate(-2px, -2px)' : 'none',
                  transition: 'all 0.15s ease',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                }}
              >
                <PhoneCall size={16} color="var(--ux4g-danger)" />
                Crisis Support
              </button>
            </motion.div>

            {/* Security note */}
            <motion.div
              initial="hidden" animate="show" variants={fadeUp}
              transition={{ duration: 0.5, delay: 0.44 }}
              style={{
                display: 'flex', alignItems: 'center', gap: '7px',
                fontSize: '0.82rem', color: 'var(--ux4g-text-muted)',
                fontFamily: '"Space Mono", "Courier Prime", monospace',
              }}
            >
              <Lock size={13} />
              <span>
                Authorized Clinical &amp; Case Management System.{' '}
                <strong style={{ color: 'var(--ux4g-violet-700)' }}>Encrypted session credentials required.</strong>
              </span>
            </motion.div>
          </div>

          {/* ── RIGHT — Kinetic Tilt Card ── */}
          <motion.div
            initial={{ opacity: 0, x: 36, y: 8 }}
            animate={{ opacity: 1, x: 0,  y: 0 }}
            transition={{ duration: 0.7, delay: 0.22, ease: 'easeOut' }}
          >
            <KineticTiltCard maxTilt={16} elevation={3} glare={true}>
              <OperationalCardContent />
            </KineticTiltCard>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
