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
    <header style={{ position: 'sticky', top: 0, zIndex: 900, backgroundColor: 'var(--ux4g-surface)', boxShadow: 'var(--elevation-1)' }}>
      {/* UX4G National Tricolor Accent Bar */}
      <div className="ux4g-tricolor-bar" />

      {/* Top Accessibility & National Identity Strip */}
      <div
        style={{
          backgroundColor: 'var(--ux4g-bg-subtle)',
          borderBottom: '1px solid var(--ux4g-border)',
          padding: '6px 0',
          fontSize: '0.8rem',
          color: 'var(--ux4g-text-secondary)',
        }}
      >
        <div className="container flex-between" style={{ flexWrap: 'wrap', gap: '8px' }}>
          {/* Government of India Emblem & Initiative */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', letterSpacing: '0.02em' }}>
                GOVERNMENT OF INDIA
              </span>
              <span style={{ color: 'var(--ux4g-border)' }}>|</span>
              <span>Ministry of Social Justice & Empowerment</span>
            </div>
          </div>

          {/* Accessibility Controls & Universal Motion Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            {/* Emergency Hotline Quick Access */}
            <button
              type="button"
              onClick={openEmergencyHelp}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: 'var(--ux4g-danger-bg)',
                color: 'var(--ux4g-danger-text)',
                border: '1px solid var(--ux4g-danger-border)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
              aria-label="24x7 Emergency Mental Health Helpline"
            >
              <PhoneCall size={12} />
              <span>Tele-MANAS: 14416 (24x7 Free)</span>
            </button>

            {/* Font Scaling Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '2px', borderLeft: '1px solid var(--ux4g-border)', paddingLeft: '8px' }}>
              <button
                type="button"
                onClick={() => adjustFontScale(0.9)}
                title="Decrease font size"
                style={{
                  background: fontScale === 0.9 ? 'var(--ux4g-violet-200)' : 'transparent',
                  border: 'none',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 0.9 ? 700 : 500,
                  fontSize: '0.75rem',
                }}
              >
                A-
              </button>
              <button
                type="button"
                onClick={() => adjustFontScale(1.0)}
                title="Normal font size"
                style={{
                  background: fontScale === 1.0 ? 'var(--ux4g-violet-200)' : 'transparent',
                  border: 'none',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 1.0 ? 700 : 500,
                  fontSize: '0.75rem',
                }}
              >
                A
              </button>
              <button
                type="button"
                onClick={() => adjustFontScale(1.15)}
                title="Increase font size"
                style={{
                  background: fontScale === 1.15 ? 'var(--ux4g-violet-200)' : 'transparent',
                  border: 'none',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontWeight: fontScale === 1.15 ? 700 : 500,
                  fontSize: '0.75rem',
                }}
              >
                A+
              </button>
            </div>

            {/* High Contrast Mode Toggle */}
            <button
              type="button"
              onClick={toggleHighContrast}
              title="Toggle High Contrast Mode"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: highContrast ? '#000000' : 'transparent',
                color: highContrast ? '#FFFFFF' : 'inherit',
                border: '1px solid var(--ux4g-border)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                cursor: 'pointer',
              }}
            >
              <Eye size={12} />
              <span>{highContrast ? 'Standard' : 'High Contrast'}</span>
            </button>

            {/* Universal Motion Toggle */}
            <button
              type="button"
              onClick={toggleReducedMotion}
              title="Toggle all UI animations & transitions globally"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: reducedMotion ? 'var(--ux4g-violet-700)' : 'transparent',
                color: reducedMotion ? '#FFFFFF' : 'var(--ux4g-violet-800)',
                border: '1px solid var(--ux4g-violet-300)',
                padding: '2px 9px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'var(--transition-fast)',
              }}
            >
              <Sparkles size={12} />
              <span>Motion: {reducedMotion ? 'PAUSED' : 'ACTIVE'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div style={{ padding: '12px 0' }}>
        <div className="container flex-between">
          {/* System Brand / Logo with Ashoka Stambh (State Emblem of India) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '14px' }}>
              {/* Ashoka Stambh (State Emblem of India) */}
              <AshokaEmblem height={50} />

              {/* Subtle Vertical Divider bar matching UX4G specifications */}
              <div
                style={{
                  width: '1px',
                  height: '38px',
                  backgroundColor: 'var(--ux4g-border)',
                  margin: '0 2px',
                }}
                aria-hidden="true"
              />

              {/* AAROH Logo Icon */}
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--ux4g-violet-700)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  boxShadow: '0 4px 10px rgba(75, 35, 184, 0.25)',
                  flexShrink: 0,
                }}
              >
                {/* Ashoka Chakra / Protective Symbol Icon */}
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" />
                  <circle cx="12" cy="12" r="4" fill="currentColor" fillOpacity="0.2" />
                  <path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" strokeWidth="1.5" />
                </svg>
              </div>

              {/* Title & Subtitle */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', letterSpacing: '-0.02em' }}>
                    AAROH
                  </span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)', lineHeight: 1.2 }}>
                  Mental Health Monitoring & Distress Prediction System
                </p>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ display: 'none', gap: '20px' }} className="desktop-links">
              <Link
                to="/"
                style={{
                  textDecoration: 'none',
                  color: location.pathname === '/' ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-secondary)',
                  fontWeight: location.pathname === '/' ? 700 : 500,
                  fontSize: '0.92rem',
                }}
              >
                Home
              </Link>
              <a
                href="#about"
                style={{
                  textDecoration: 'none',
                  color: 'var(--ux4g-text-secondary)',
                  fontWeight: 500,
                  fontSize: '0.92rem',
                }}
              >
                About AAROH
              </a>
              <a
                href="#workflow"
                style={{
                  textDecoration: 'none',
                  color: 'var(--ux4g-text-secondary)',
                  fontWeight: 500,
                  fontSize: '0.92rem',
                }}
              >
                Workflow
              </a>
              <a
                href="#safety"
                style={{
                  textDecoration: 'none',
                  color: 'var(--ux4g-text-secondary)',
                  fontWeight: 500,
                  fontSize: '0.92rem',
                }}
              >
                Safety & Support
              </a>
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
                      backgroundColor: 'var(--ux4g-bg-subtle)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--ux4g-border)',
                    }}
                  >
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--ux4g-violet-700)',
                        color: '#FFFFFF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                      }}
                    >
                      {currentUser.avatar}
                    </div>
                    <div style={{ display: 'none' }} className="user-text-pill">
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--ux4g-text-primary)' }}>
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
