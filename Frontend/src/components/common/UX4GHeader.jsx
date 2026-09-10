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
    <header
      style={{
        position: 'sticky',
        top: '16px',
        zIndex: 1000,
        margin: '0 auto',
        maxWidth: '1240px',
        padding: '0 20px',
      }}
    >
      {/* Floating Editorial Pill Navbar */}
      <div
        style={{
          backgroundColor: 'rgba(247, 241, 230, 0.94)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '2px solid #3A2312',
          boxShadow: '4px 4px 0px #3A2312',
          borderRadius: '16px',
          padding: '10px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        {/* Left: Brand Monogram & Wordmark */}
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AshokaEmblem height={38} />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '1.35rem',
                  fontWeight: 900,
                  color: '#2B1508',
                  letterSpacing: '-0.02em',
                  fontFamily: '"Fraunces", "Playfair Display", Georgia, serif',
                  lineHeight: 1,
                }}
              >
                AAROH
              </span>
              <span
                style={{
                  fontSize: '0.62rem',
                  fontWeight: 800,
                  backgroundColor: '#E6DAC9',
                  color: '#543118',
                  padding: '2px 7px',
                  borderRadius: '4px',
                  border: '1px solid #AB8867',
                  letterSpacing: '0.06em',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                }}
              >
                v2.4 / AI CARE
              </span>
            </div>
            <p
              style={{
                fontSize: '0.72rem',
                color: '#78604F',
                margin: '2px 0 0',
                fontFamily: '"Space Mono", "Courier Prime", monospace',
                letterSpacing: '0.01em',
              }}
            >
              Distress Intelligence &amp; Care Orchestration
            </p>
          </div>
        </Link>

        {/* Center: Editorial Navigation Links */}
        <nav style={{ display: 'none', alignItems: 'center', gap: '22px' }} className="desktop-links">
          {isAuthenticated ? (
            <Link
              to={getDashboardPath(currentUser?.role)}
              style={{
                textDecoration: 'none',
                color: '#2B1508',
                fontWeight: 700,
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: '8px',
                backgroundColor: '#E6DAC9',
                border: '1.5px solid #3A2312',
                fontFamily: '"Space Mono", "Courier Prime", monospace',
              }}
            >
              <LayoutDashboard size={15} />
              <span>
                {(currentUser?.role === 'CITIZEN' || currentUser?.role === 'VICTIM')
                  ? 'Care Space'
                  : currentUser?.role === 'COUNSELLOR'
                  ? 'Clinical Console'
                  : currentUser?.role === 'DISTRICT'
                  ? 'District Oversight'
                  : currentUser?.role === 'STATE'
                  ? 'State Overview'
                  : currentUser?.role === 'NATIONAL'
                  ? 'National Triage'
                  : 'System Authority'}
              </span>
            </Link>
          ) : (
            <>
              <Link
                to="/"
                style={{
                  textDecoration: 'none',
                  color: location.pathname === '/' ? '#2B1508' : '#78604F',
                  fontWeight: location.pathname === '/' ? 800 : 600,
                  fontSize: '0.84rem',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  letterSpacing: '0.02em',
                  transition: 'color 0.15s ease',
                }}
              >
                Platform
              </Link>
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
                  color: '#78604F',
                  fontWeight: 600,
                  fontSize: '0.84rem',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  letterSpacing: '0.02em',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#2B1508')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#78604F')}
              >
                Acoustic AI
              </button>
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
                  color: '#78604F',
                  fontWeight: 600,
                  fontSize: '0.84rem',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  letterSpacing: '0.02em',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#2B1508')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#78604F')}
              >
                Architecture
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
                  color: '#78604F',
                  fontWeight: 600,
                  fontSize: '0.84rem',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  letterSpacing: '0.02em',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#2B1508')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#78604F')}
              >
                Safe Care
              </button>
            </>
          )}
        </nav>

        {/* Right: Controls & Portal Access */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Discreet Crisis Hotline Pill */}
          <button
            type="button"
            onClick={openEmergencyHelp}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#F5EBE7',
              color: '#822710',
              border: '1.5px solid #822710',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '0.74rem',
              fontWeight: 700,
              cursor: 'pointer',
              fontFamily: '"Space Mono", "Courier Prime", monospace',
              transition: 'all 0.15s ease',
            }}
            aria-label="24x7 Emergency Helpline"
          >
            <PhoneCall size={12} />
            <span style={{ display: 'none' }} className="helpline-text">Crisis Line</span>
          </button>

          {/* Minimalist Google Translate Selector */}
          <GoogleTranslateWidget compact={true} />

          {/* Auth Button */}
          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  backgroundColor: '#3A2312',
                  color: '#F7F1E6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  border: '1px solid #2B1508',
                }}
                title={currentUser.name}
              >
                {currentUser.avatar}
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
            </div>
          ) : (
            <Link to="/signin" style={{ textDecoration: 'none' }}>
              <button
                type="button"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 16px',
                  borderRadius: '8px',
                  backgroundColor: '#3A2312',
                  color: '#F7F1E6',
                  border: '1.5px solid #1C1108',
                  boxShadow: '2px 2px 0px #1C1108',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontFamily: '"Space Mono", "Courier Prime", monospace',
                  letterSpacing: '0.02em',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translate(-1px, -1px)';
                  e.currentTarget.style.boxShadow = '3px 3px 0px #1C1108';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = '2px 2px 0px #1C1108';
                }}
              >
                <UserCheck size={14} />
                <span>Portal Access</span>
              </button>
            </Link>
          )}
        </div>
      </div>

      <style>{`
        @media (min-width: 860px) {
          .desktop-links {
            display: flex !important;
          }
          .helpline-text {
            display: inline !important;
          }
        }
      `}</style>
    </header>
  );
};
