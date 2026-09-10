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
const OperationalCardContent = () => {
  const features = [
    {
      icon: <Brain size={20} />,
      bg: 'rgba(84,49,24,0.1)', color: '#543118',
      title: 'AI Distress Modeling',
      desc: 'Multimodal speech & linguistic feature analysis with individualized baseline deviation scoring.',
    },
    {
      icon: <HeartHandshake size={20} />,
      bg: 'rgba(68,63,36,0.12)', color: '#443F24',
      title: 'Human-Centered Care',
      desc: 'Certified clinical counsellors and district social justice authorities take all final care actions.',
    },
    {
      icon: <Shield size={20} />,
      bg: 'rgba(162,104,41,0.12)', color: '#804F18',
      title: 'SLA-Bound Interventions',
      desc: 'Transparent escalation routing across District, State, and National tiers with strict audit logging.',
    },
  ];

  return (
    <>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '18px', paddingBottom: '12px',
        borderBottom: '1px solid var(--ux4g-border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '9px', height: '9px', borderRadius: '50%',
            backgroundColor: '#8C6240',
            boxShadow: '0 0 0 2px rgba(140,98,64,0.25)',
          }} />
          <span style={{
            fontSize: '0.8rem', fontWeight: 800,
            color: 'var(--ux4g-violet-950)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            fontFamily: '"Space Mono", "Courier Prime", monospace',
          }}>
            Operational Framework
          </span>
        </div>
        <span style={{
          fontSize: '0.68rem', fontWeight: 800,
          background: '#E4CFB8', color: '#3E210E',
          border: '1px solid #AB8867',
          padding: '2px 9px', borderRadius: '4px',
          letterSpacing: '0.06em',
          fontFamily: '"Space Mono", "Courier Prime", monospace',
        }}>
          LIVE
        </span>
      </div>

      {/* Feature rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
        {features.map((f, i) => (
          <div
            key={i}
            style={{
              display: 'flex', gap: '12px', alignItems: 'flex-start',
              padding: '10px 12px', borderRadius: '12px',
              backgroundColor: 'var(--ux4g-bg)',
              border: '1px solid var(--ux4g-border-subtle)',
            }}
          >
            <div style={{
              width: '34px', height: '34px', borderRadius: '8px',
              background: f.bg, color: f.color,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {f.icon}
            </div>
            <div>
              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                {f.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px', lineHeight: '1.5' }}>
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
        {/* Trust badges */}
        <motion.div
          initial="hidden" animate="show" variants={fadeUp}
          transition={{ duration: 0.45 }}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' }}
        >
          <span style={{
            backgroundColor: 'var(--ux4g-surface)',
            color: 'var(--ux4g-violet-800)',
            fontSize: '0.78rem', fontWeight: 700,
            padding: '5px 14px', borderRadius: '999px',
            border: '1px solid var(--ux4g-violet-200)',
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            boxShadow: 'var(--elevation-1)',
          }}>
            <Shield size={13} color="var(--ux4g-violet-700)" />
            National Welfare & Mental Health Initiative
          </span>
          <span style={{
            backgroundColor: 'var(--ux4g-success-bg)',
            color: 'var(--ux4g-success-text)',
            fontSize: '0.78rem', fontWeight: 700,
            padding: '5px 12px', borderRadius: '999px',
            border: '1px solid var(--ux4g-success-border)',
            display: 'inline-flex', alignItems: 'center', gap: '5px',
          }}>
            <CheckCircle2 size={12} />
            DPDP Act 2023 Compliant
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
            {/* Pop headline — 3 individually staggered lines */}
            <h1 style={{
              fontSize: 'clamp(2.3rem, 4.6vw, 3.8rem)',
              fontWeight: 900,
              lineHeight: '1.08',
              letterSpacing: '-0.02em',
              marginBottom: '20px',
              fontFamily: '"Fraunces", "Playfair Display", Georgia, serif',
              overflow: 'hidden',
            }}>
              {/* Line 1 — scale + translateY pop */}
              <motion.span
                style={{ display: 'block', color: 'var(--ux4g-violet-950)' }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.08)}
              >
                AAROH Platform
              </motion.span>

              {/* Line 2 — gradient pop, delayed */}
              <motion.span
                style={{
                  display: 'block',
                  background: 'linear-gradient(92deg, #543118 0%, #8C6240 50%, #3E210E 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  filter: reducedMotion ? 'none' : 'drop-shadow(0 2px 10px rgba(84,49,24,0.25))',
                }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.18)}
              >
                AI-Powered Dynamic Mental Health
              </motion.span>

              {/* Line 3 — solid dark, most delayed */}
              <motion.span
                style={{ display: 'block', color: 'var(--ux4g-violet-950)' }}
                initial="hidden"
                animate="show"
                variants={lineVariant}
                transition={lineTransition(0.28)}
              >
                Monitoring &amp; Distress Prediction
              </motion.span>
            </h1>

            <motion.p
              initial="hidden" animate="show" variants={fadeUp}
              transition={{ duration: 0.6, delay: 0.2 }}
              style={{
                fontSize: '1.04rem',
                color: 'var(--ux4g-text-secondary)',
                lineHeight: '1.7',
                marginBottom: '32px',
                maxWidth: '540px',
              }}
            >
              A proactive, government-grade psychological support infrastructure built to identify escalating distress in victims of atrocities through consensual multimodal interactions, enabling timely human intervention and holistic rehabilitation.
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
                      padding: '13px 26px', borderRadius: '6px',
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
                      padding: '13px 26px', borderRadius: '6px',
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
                    Sign In to Authorized Portal <ArrowRight size={18} />
                  </button>
                </Link>
              )}

              <button
                type="button"
                onMouseEnter={() => setBtnHover('crisis')}
                onMouseLeave={() => setBtnHover(null)}
                onClick={() => openOffcanvas({
                  title: 'AAROH Rapid Emergency Support',
                  subtitle: '24x7 crisis intervention and victim helpline contacts',
                  type: 'emergency',
                })}
                style={{
                  backgroundColor: btnHover === 'crisis' ? '#F8ECE7' : 'var(--ux4g-surface)',
                  color: 'var(--ux4g-danger)',
                  border: '2px solid var(--ux4g-danger)',
                  padding: '13px 22px', borderRadius: '4px',
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
                Immediate Crisis Support
              </button>
            </motion.div>

            {/* Security note */}
            <motion.div
              initial="hidden" animate="show" variants={fadeUp}
              transition={{ duration: 0.5, delay: 0.44 }}
              style={{
                display: 'flex', alignItems: 'center', gap: '7px',
                fontSize: '0.82rem', color: 'var(--ux4g-text-muted)',
              }}
            >
              <Lock size={13} />
              <span>
                Restricted Government System.{' '}
                <strong style={{ color: 'var(--ux4g-violet-700)' }}>No public registration.</strong>{' '}
                Authorized sign-in only.
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
