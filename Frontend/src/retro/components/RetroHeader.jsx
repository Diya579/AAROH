import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Phone, Shield, Feather, Clock, Landmark, Sparkles } from 'lucide-react';
import { GoogleTranslateWidget } from './GoogleTranslateWidget';
import { RetroStamp } from './RetroStamp';

export const RetroHeader = ({ onSwitchToClassic }) => {
  const [currentTime, setCurrentTime] = useState('');
  const location = useLocation();

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleDateString('en-GB', {
          weekday: 'short',
          day: '2-digit',
          month: 'short',
          year: 'numeric',
        }) + ' • ' +
        now.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        }) + ' IST'
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navLinks = [
    { label: 'FRONT PAGE', path: '/' },
    { label: 'BENEFICIARY DESK', path: '/retro/victim' },
    { label: 'CLINICAL BUREAU', path: '/retro/counsellor' },
    { label: 'STATISTICAL SUPPLEMENT', path: '/retro/analytics' },
  ];

  return (
    <header className="retro-masthead">
      {/* Top Dateline Bar */}
      <div className="retro-masthead-dateline">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Feather size={13} />
            VOL. XXIV • ISSUE NO. 2026
          </span>
          <span style={{ opacity: 0.4 }}>|</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Landmark size={13} />
            NEW DELHI CENTRAL DISPATCH
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={12} />
            <span style={{ letterSpacing: '0.04em' }}>{currentTime || 'SYNCHRONIZING...'}</span>
          </div>

          <span style={{ opacity: 0.4 }}>|</span>

          {/* Google Translate Integration Widget */}
          <GoogleTranslateWidget compact={false} />
        </div>
      </div>

      {/* Main Title Masthead */}
      <div style={{ position: 'relative', textAlign: 'center', padding: '10px 0 6px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '18px' }}>
          <span style={{ fontSize: '1.4rem' }}>❖</span>
          <h1 className="retro-masthead-title">
            THE AAROH GAZETTE
          </h1>
          <span style={{ fontSize: '1.4rem' }}>❖</span>
        </div>

        <div className="retro-masthead-subtitle">
          NATIONAL ATROCITY MONITORING, TRAUMA INTERVENTION & MULTIMODAL ACOUSTIC SURVEILLANCE BULLETINS
        </div>
      </div>

      {/* Newspaper Nav & Helpline Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          paddingTop: '6px',
        }}
      >
        <nav style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className="retro-btn"
                style={{
                  fontSize: '0.78rem',
                  padding: '6px 14px',
                  backgroundColor: isActive ? 'var(--retro-bg-cardboard-dark)' : 'var(--retro-bg-paper-light)',
                  borderWidth: isActive ? '2.5px' : '1.5px',
                }}
              >
                {isActive && <span style={{ marginRight: '4px' }}>▶</span>}
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '4px 10px',
              border: '1.5px solid var(--retro-stamp-red)',
              backgroundColor: 'var(--retro-stamp-red-bg)',
              color: 'var(--retro-stamp-red)',
            }}
          >
            <Phone size={12} />
            <span>24/7 HELPLINE: 14416 (TELE-MANAS) • 112 (EMERGENCY)</span>
          </div>

          <RetroStamp type="verified" label="GIGW CERTIFIED" size="sm" />
        </div>
      </div>
    </header>
  );
};

export default RetroHeader;
