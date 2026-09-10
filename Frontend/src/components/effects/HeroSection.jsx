import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Shield, ArrowRight, PhoneCall, CheckCircle2,
  Brain, HeartHandshake, Clock, Lock,
} from 'lucide-react';
import { RiskBadge } from '../common/UX4GBadge';
import { KineticTiltCard } from './KineticTiltCard';
import { LanguageSelector } from '../common/LanguageSelector';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { useAuth } from '../../context/AuthContext';

/* ─── Operational Framework Card content ────────────────────────────────── */
const OperationalCardContent = () => {
  const features = [
    {
      icon: <Brain size={20} />,
      bg: 'rgba(109,40,217,0.08)', color: '#7C3AED',
      title: 'AI Distress Modeling',
      desc: 'Multimodal speech & linguistic feature analysis with individualized baseline deviation scoring.',
    },
    {
      icon: <HeartHandshake size={20} />,
      bg: 'rgba(5,150,105,0.08)', color: '#059669',
      title: 'Human-Centered Care',
      desc: 'Certified clinical counsellors and district social justice authorities take all final care actions.',
    },
    {
      icon: <Shield size={20} />,
      bg: 'rgba(245,158,11,0.08)', color: '#D97706',
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
          <motion.div
            animate={{ scale: [1, 1.28, 1], opacity: [0.85, 1, 0.85] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
            style={{
              width: '9px', height: '9px', borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 0 3px rgba(34,197,94,0.25)',
            }}
          />
          <span style={{
            fontSize: '0.8rem', fontWeight: 700,
            color: 'var(--ux4g-violet-950)',
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}>
            Operational Framework
          </span>
        </div>
        <span style={{
          fontSize: '0.68rem', fontWeight: 800,
          background: '#EDE9FE', color: '#5B21B6',
          padding: '2px 9px', borderRadius: '999px',
          letterSpacing: '0.06em',
        }}>
          LIVE
        </span>
      </div>

      {/* Feature rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
        {features.map((f, i) => (
          <motion.div
            key={i}
            whileHover={{ x: 5, transition: { duration: 0.2, ease: 'easeOut' } }}
            style={{
              display: 'flex', gap: '12px', alignItems: 'flex-start',
              padding: '10px 12px', borderRadius: '12px',
              backgroundColor: 'var(--ux4g-bg)',
              border: '1px solid var(--ux4g-border-subtle)',
              cursor: 'default',
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
          </motion.div>
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
        background: 'linear-gradient(180deg, #F3EFFE 0%, #F8F9FE 100%)',
        padding: '64px 0 60px',
        borderBottom: '1px solid var(--ux4g-border)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Subtle decorative gliding glow blobs (light) */}
      <div aria-hidden="true" style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        <motion.div
          animate={reducedMotion ? {} : {
            x: [0, 32, -20, 0],
            y: [0, -38, 22, 0],
            scale: [1, 1.09, 0.95, 1],
          }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute', top: '-120px', right: '-80px',
            width: '480px', height: '480px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)',
            filter: 'blur(30px)',
          }}
        />
        <motion.div
          animate={reducedMotion ? {} : {
            x: [0, -28, 25, 0],
            y: [0, 32, -25, 0],
            scale: [1, 0.94, 1.07, 1],
          }}
          transition={{ duration: 21, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            position: 'absolute', bottom: '-80px', left: '-60px',
            width: '340px', height: '340px', borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(109,40,217,0.09) 0%, transparent 70%)',
            filter: 'blur(40px)',
          }}
        />
      </div>

      <div className="container" style={{ position: 'relative', zIndex: 2 }}>
        {/* Trust badges & Homepage Language Selector */}
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
          <LanguageSelector variant="hero" />
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
              fontSize: 'clamp(2.3rem, 4.6vw, 3.5rem)',
              fontWeight: 900,
              lineHeight: '1.1',
              letterSpacing: '-0.03em',
              marginBottom: '20px',
              fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif',
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
                  background: 'linear-gradient(92deg, #6D28D9 0%, #7C3AED 40%, #4F46E5 80%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  filter: reducedMotion ? 'none' : 'drop-shadow(0 2px 14px rgba(109,40,217,0.2))',
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
                        ? 'linear-gradient(90deg, #7C3AED, #6D28D9)'
                        : 'linear-gradient(90deg, #6D28D9, #5B21B6)',
                      color: '#fff',
                      border: btnHover === 'primary'
                        ? '1.5px solid rgba(109,40,217,0.7)'
                        : '1.5px solid rgba(109,40,217,0.4)',
                      padding: '13px 26px', borderRadius: '12px',
                      fontSize: '0.97rem', fontWeight: 700, cursor: 'pointer',
                      display: 'inline-flex', alignItems: 'center', gap: '8px',
                      boxShadow: btnHover === 'primary'
                        ? '0 8px 30px -8px rgba(109,40,217,0.55)'
                        : '0 4px 14px -4px rgba(109,40,217,0.35)',
                      transform: btnHover === 'primary' ? 'translateY(-2px)' : 'translateY(0)',
                      transition: 'all 0.22s ease',
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
                        ? 'linear-gradient(90deg, #7C3AED, #6D28D9)'
                        : 'linear-gradient(90deg, #6D28D9, #5B21B6)',
                      color: '#fff',
                      border: btnHover === 'primary'
                        ? '1.5px solid rgba(109,40,217,0.7)'
                        : '1.5px solid rgba(109,40,217,0.4)',
                      padding: '13px 26px', borderRadius: '12px',
                      fontSize: '0.97rem', fontWeight: 700, cursor: 'pointer',
                      display: 'inline-flex', alignItems: 'center', gap: '8px',
                      boxShadow: btnHover === 'primary'
                        ? '0 8px 30px -8px rgba(109,40,217,0.55)'
                        : '0 4px 14px -4px rgba(109,40,217,0.35)',
                      transform: btnHover === 'primary' ? 'translateY(-2px)' : 'translateY(0)',
                      transition: 'all 0.22s ease',
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
                  backgroundColor: btnHover === 'crisis' ? '#FEF2F2' : 'var(--ux4g-surface)',
                  color: btnHover === 'crisis' ? '#B91C1C' : 'var(--ux4g-violet-900)',
                  border: btnHover === 'crisis'
                    ? '1.5px solid rgba(185,28,28,0.35)'
                    : '1.5px solid var(--ux4g-violet-300)',
                  padding: '13px 22px', borderRadius: '12px',
                  fontSize: '0.97rem', fontWeight: 600, cursor: 'pointer',
                  display: 'inline-flex', alignItems: 'center', gap: '8px',
                  boxShadow: btnHover === 'crisis'
                    ? '0 4px 20px -4px rgba(239,68,68,0.2)'
                    : 'var(--elevation-1)',
                  transform: btnHover === 'crisis' ? 'translateY(-2px)' : 'translateY(0)',
                  transition: 'all 0.22s ease',
                }}
              >
                <PhoneCall size={18} color={btnHover === 'crisis' ? '#DC2626' : 'var(--ux4g-danger)'} />
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
