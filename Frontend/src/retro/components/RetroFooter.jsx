import React from 'react';
import { ArrowUp, ShieldCheck, HeartHandshake, PhoneCall, Scale } from 'lucide-react';
import { RetroStamp } from './RetroStamp';

export const RetroFooter = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer
      style={{
        background: 'var(--retro-bg-cardboard-dark)',
        borderTop: '3px double var(--retro-ink-black)',
        color: 'var(--retro-ink-black)',
        padding: '36px 24px 28px 24px',
        marginTop: '60px',
        position: 'relative',
      }}
    >
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        {/* Top Colophon Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
            paddingBottom: '24px',
            borderBottom: '1.5px solid var(--retro-ink-black)',
          }}
        >
          {/* Column 1: Gazette Imprint */}
          <div>
            <h3
              style={{
                fontFamily: 'var(--retro-font-headline)',
                fontSize: '1.2rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                marginBottom: '8px',
              }}
            >
              The AAROH Gazette
            </h3>
            <p
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.82rem',
                lineHeight: '1.6',
                color: 'var(--retro-ink-charcoal)',
                marginBottom: '12px',
              }}
            >
              An automated, multimodal digital broadsheet tracking psychological distress baselines, acoustic sentiment markers, and clinical intervention SLAs for survivors of systemic atrocities.
            </p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <RetroStamp type="verified" label="DE-IDENTIFIED SYNTHETIC DATA" size="sm" />
              <RetroStamp type="sovereign" label="NALSA INTEGRATED" size="sm" />
            </div>
          </div>

          {/* Column 2: Emergency Dispatches */}
          <div
            style={{
              border: '2px dashed var(--retro-stamp-red)',
              padding: '16px',
              backgroundColor: 'var(--retro-stamp-red-bg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <PhoneCall size={16} style={{ color: 'var(--retro-stamp-red)' }} />
              <span
                style={{
                  fontFamily: 'var(--retro-font-mono)',
                  fontSize: '0.8rem',
                  fontWeight: 800,
                  color: 'var(--retro-stamp-red)',
                  textTransform: 'uppercase',
                }}
              >
                Immediate Distress Hotlines
              </span>
            </div>
            <ul
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.78rem',
                lineHeight: '1.7',
                paddingLeft: '18px',
                margin: 0,
                color: 'var(--retro-ink-charcoal)',
              }}
            >
              <li><strong>Tele-MANAS:</strong> 14416 / 1800-891-4416 (24×7 Toll-Free)</li>
              <li><strong>KIRAN Mental Health:</strong> 1800-599-0019</li>
              <li><strong>National Emergency:</strong> 112</li>
              <li><strong>Women Helpline:</strong> 1091 / 181</li>
              <li><strong>Childline India:</strong> 1098</li>
            </ul>
          </div>

          {/* Column 3: Legal & Regulatory Framework */}
          <div>
            <h4
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.82rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Scale size={14} /> Statutory Governance
            </h4>
            <p
              style={{
                fontFamily: 'var(--retro-font-mono)',
                fontSize: '0.78rem',
                lineHeight: '1.6',
                color: 'var(--retro-ink-muted)',
              }}
            >
              Operated under Section 15A (Victim & Witness Protection) of the SC & ST (PoA) Act, 1989 (Amended 2015). All clinical protocols adhere to the Mental Healthcare Act (MHCA), 2017 with de-identification and explicit consent encryption.
            </p>
          </div>
        </div>

        {/* Bottom Colophon & Scroll to Top */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '18px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--retro-font-mono)',
              fontSize: '0.75rem',
              color: 'var(--retro-ink-muted)',
            }}
          >
            © 2026 MINISTRY OF SOCIAL JUSTICE & EMPOWERMENT • CENTRAL CLINICAL BUREAU • ALL RIGHTS RESERVED
          </div>

          <button
            onClick={scrollToTop}
            className="retro-btn"
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
          >
            <ArrowUp size={13} /> BACK TO MASTHEAD
          </button>
        </div>
      </div>
    </footer>
  );
};

export default RetroFooter;
