import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  PhoneCall, 
  Eye, 
  Sparkles, 
  LogOut, 
  UserCheck, 
  LayoutDashboard
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { UX4GButton } from './UX4GButton';
import { AshokaEmblem } from './AshokaEmblem';
import { GoogleTranslateWidget } from '../../retro/components/GoogleTranslateWidget';

export const UX4GHeader = () => {
  const { currentUser, isAuthenticated, signOut, getDashboardPath } = useAuth();
  const { 
    reducedMotion, 
    toggleReducedMotion, 
    highContrast, 
    toggleHighContrast, 
    fontScale, 
    adjustFontScale,
    openOffcanvas
  } = useThemeAccessibility();

  const navigate = useNavigate();
  const location = useLocation();

  const openEmergencyHelp = () => {
    openOffcanvas({
      title: 'Emergency Crisis & Support',
      subtitle: 'Immediate government mental health assistance',
      type: 'emergency'
    });
  };

  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 900, backgroundColor: 'var(--ux4g-surface)', borderBottom: '1px solid var(--ux4g-border)', boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)' }}>
      {/* UX4G National Tricolor Accent Bar */}
      <div className="ux4g-tricolor-bar" />

      {/* Top Accessibility & National Identity Strip */}
      <div
        style={{
          backgroundColor: 'var(--ux4g-bg-subtle)',
          borderBottom: '1px solid var(--ux4g-border)',
          padding: '6px 0',
          fontSize: '0.78rem',
          color: 'var(--ux4g-text-secondary)',
        }}
      >
        <div className="container flex-between" style={{ flexWrap: 'wrap', gap: '10px' }}>
          {/* Government of India Official Header Text */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, color: '#0F172A', letterSpacing: '0.03em', fontSize: '0.76rem' }}>
              भारत सरकार | GOVERNMENT OF INDIA
            </span>
            <span style={{ color: '#CBD5E1' }}>•</span>
            <span style={{ color: '#475569', fontSize: '0.76rem' }}>Ministry of Social Justice & Empowerment</span>
          </div>

          {/* Accessibility & Helpline Strip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            {/* Helpline Link */}
            <button
              type="button"
              onClick={openEmergencyHelp}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: '#FEF2F2',
                color: '#991B1B',
                border: '1px solid #FECACA',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '0.74rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
              aria-label="24x7 Emergency Mental Health Helpline"
            >
              <PhoneCall size={11} />
              <span>Tele-MANAS: 14416 (24x7)</span>
            </button>

            {/* Google Translate Language Selector */}
            <GoogleTranslateWidget compact={true} />

            {/* Font Scaling */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1px', borderLeft: '1px solid #E2E8F0', paddingLeft: '10px' }}>
              <button
                type="button"
                onClick={() => adjustFontScale(0.9)}
                title="Decrease font size"
                style={{
                  background: fontScale === 0.9 ? '#E2E8F0' : 'transparent',
                  border: 'none',
                  padding: '2px 5px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 0.9 ? 700 : 500,
                  fontSize: '0.72rem',
                  color: '#334155'
                }}
              >
                A-
              </button>
              <button
                type="button"
                onClick={() => adjustFontScale(1.0)}
                title="Normal font size"
                style={{
                  background: fontScale === 1.0 ? '#E2E8F0' : 'transparent',
                  border: 'none',
                  padding: '2px 5px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 1.0 ? 700 : 500,
                  fontSize: '0.72rem',
                  color: '#334155'
                }}
              >
                A
              </button>
              <button
                type="button"
                onClick={() => adjustFontScale(1.15)}
                title="Increase font size"
                style={{
                  background: fontScale === 1.15 ? '#E2E8F0' : 'transparent',
                  border: 'none',
                  padding: '2px 5px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 1.15 ? 700 : 500,
                  fontSize: '0.72rem',
                  color: '#334155'
                }}
              >
                A+
              </button>
            </div>

            {/* High Contrast */}
            <button
              type="button"
              onClick={toggleHighContrast}
              title="Toggle High Contrast Mode"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: highContrast ? '#0F172A' : 'transparent',
                color: highContrast ? '#FFFFFF' : '#475569',
                border: '1px solid #CBD5E1',
                padding: '2px 7px',
                borderRadius: '4px',
                fontSize: '0.72rem',
                cursor: 'pointer',
              }}
            >
              <Eye size={11} />
              <span>{highContrast ? 'Standard' : 'Contrast'}</span>
            </button>

            {/* Motion */}
            <button
              type="button"
              onClick={toggleReducedMotion}
              title="Toggle UI animations"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: reducedMotion ? '#1E3A8A' : 'transparent',
                color: reducedMotion ? '#FFFFFF' : '#1E3A8A',
                border: '1px solid #CBD5E1',
                padding: '2px 7px',
                borderRadius: '4px',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Sparkles size={11} />
              <span>Motion: {reducedMotion ? 'Off' : 'On'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar (Clean, Formal, Spacious) */}
      <div style={{ padding: '14px 0' }}>
        <div className="container flex-between">
          {/* Logo & National Identity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AshokaEmblem height={46} />

              <div
                style={{
                  width: '1px',
                  height: '34px',
                  backgroundColor: '#E2E8F0',
                  margin: '0 2px',
                }}
                aria-hidden="true"
              />

              {/* Title & Subtitle */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
                    AAROH
                  </span>
                  <span style={{ fontSize: '0.7rem', backgroundColor: '#EFF6FF', color: '#1E3A8A', fontWeight: 700, padding: '2px 6px', borderRadius: '4px', border: '1px solid #DBEAFE' }}>
                    PORTAL
                  </span>
                </div>
                <p style={{ fontSize: '0.75rem', color: '#64748B', lineHeight: 1.2, marginTop: '2px' }}>
                  Mental Health Monitoring & Distress Prediction System
                </p>
              </div>
            </Link>
          </div>

          {/* Navigation Links (Spacious, Formal) */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
            <div style={{ display: 'none', gap: '24px', alignItems: 'center' }} className="desktop-links">
              {isAuthenticated ? (
                <Link
                  to={getDashboardPath(currentUser?.role)}
                  style={{
                    textDecoration: 'none',
                    color: location.pathname.startsWith('/dashboard') ? '#1E3A8A' : '#475569',
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    letterSpacing: '-0.01em',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    backgroundColor: location.pathname.startsWith('/dashboard') ? '#EFF6FF' : 'transparent',
                    border: location.pathname.startsWith('/dashboard') ? '1px solid #DBEAFE' : '1px solid transparent',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    if (!location.pathname.startsWith('/dashboard')) e.currentTarget.style.color = '#1E3A8A';
                  }}
                  onMouseLeave={(e) => {
                    if (!location.pathname.startsWith('/dashboard')) e.currentTarget.style.color = '#475569';
                  }}
                >
                  <LayoutDashboard size={16} />
                  <span>
                    {(currentUser?.role === 'CITIZEN' || currentUser?.role === 'VICTIM')
                      ? 'Citizen Dashboard'
                      : currentUser?.role === 'COUNSELLOR'
                      ? 'Counsellor Dashboard'
                      : currentUser?.role === 'DISTRICT'
                      ? 'District Dashboard'
                      : currentUser?.role === 'STATE'
                      ? 'State Dashboard'
                      : currentUser?.role === 'NATIONAL'
                      ? 'National Dashboard'
                      : currentUser?.role === 'ADMIN'
                      ? 'System Authority Dashboard'
                      : 'Dashboard'}
                  </span>
                </Link>
              ) : (
                <>
                  <Link
                    to="/"
                    style={{
                      textDecoration: 'none',
                      color: location.pathname === '/' ? '#1E3A8A' : '#475569',
                      fontWeight: location.pathname === '/' ? 700 : 500,
                      fontSize: '0.9rem',
                      letterSpacing: '-0.01em',
                      transition: 'color 0.15s ease',
                    }}
                  >
                    Home
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      if (location.pathname === '/') {
                        const el = document.getElementById('about');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/#about');
                      }
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      color: '#475569',
                      fontWeight: 500,
                      fontSize: '0.9rem',
                      letterSpacing: '-0.01em',
                      fontFamily: 'inherit',
                      transition: 'color 0.15s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = '#1E3A8A'}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#475569'}
                  >
                    About AAROH
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (location.pathname === '/') {
                        const el = document.getElementById('workflow');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                      } else {
                        navigate('/#workflow');
                      }
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      color: '#475569',
                      fontWeight: 500,
                      fontSize: '0.9rem',
                      letterSpacing: '-0.01em',
                      fontFamily: 'inherit',
                      transition: 'color 0.15s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = '#1E3A8A'}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#475569'}
                  >
                    Workflow
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (location.pathname === '/') {
                        const el = document.getElementById('safety');
                        if (el) el.scrollIntoView({ behavior: 'smooth' });
                        else openEmergencyHelp();
                      } else {
                        navigate('/#safety');
                      }
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      color: '#475569',
                      fontWeight: 500,
                      fontSize: '0.9rem',
                      letterSpacing: '-0.01em',
                      fontFamily: 'inherit',
                      transition: 'color 0.15s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = '#1E3A8A'}
                    onMouseLeave={(e) => e.currentTarget.style.color = '#475569'}
                  >
                    Safety & Support
                  </button>
                </>
              )}
            </div>

            {/* Auth Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {isAuthenticated ? (
                <>
                  <Link to={getDashboardPath(currentUser.role)} style={{ textDecoration: 'none' }}>
                    <UX4GButton variant="secondary" size="sm" icon={LayoutDashboard}>
                      {currentUser.role} Portal
                    </UX4GButton>
                  </Link>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '4px 10px',
                      backgroundColor: '#F8FAFC',
                      borderRadius: '6px',
                      border: '1px solid #E2E8F0',
                    }}
                  >
                    <div
                      style={{
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        backgroundColor: '#1E3A8A',
                        color: '#FFFFFF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                      }}
                    >
                      {currentUser.avatar}
                    </div>
                    <div style={{ display: 'none' }} className="user-text-pill">
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#0F172A' }}>
                        {currentUser.name}
                      </span>
                    </div>
                  </div>

                  <UX4GButton
                    variant="ghost"
                    size="sm"
                    icon={LogOut}
                    onClick={() => {
                      signOut();
                      navigate('/signin');
                    }}
                    ariaLabel="Sign out of system"
                  >
                    Sign Out
                  </UX4GButton>
                </>
              ) : (
                <Link to="/signin" style={{ textDecoration: 'none' }}>
                  <UX4GButton variant="primary" size="md" icon={UserCheck}>
                    Authorized Sign In
                  </UX4GButton>
                </Link>
              )}
            </div>
          </nav>
        </div>
      </div>

      <style>{`
        @media (min-width: 900px) {
          .desktop-links {
            display: flex !important;
          }
          .user-text-pill {
            display: block !important;
          }
        }
      `}</style>
    </header>
  );
};
