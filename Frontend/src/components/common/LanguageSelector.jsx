import React, { useState, useEffect, useRef } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English',       nativeLabel: 'English'     },
  { code: 'hi', label: 'Hindi',         nativeLabel: 'हिन्दी'        },
  { code: 'bn', label: 'Bengali',       nativeLabel: 'বাংলা'         },
  { code: 'te', label: 'Telugu',        nativeLabel: 'తెలుగు'        },
  { code: 'mr', label: 'Marathi',       nativeLabel: 'मराठी'         },
  { code: 'ta', label: 'Tamil',         nativeLabel: 'தமிழ்'         },
  { code: 'gu', label: 'Gujarati',      nativeLabel: 'ગુજરાતી'       },
  { code: 'kn', label: 'Kannada',       nativeLabel: 'ಕನ್ನಡ'         },
  { code: 'ml', label: 'Malayalam',     nativeLabel: 'മലയാളം'        },
  { code: 'pa', label: 'Punjabi',       nativeLabel: 'ਪੰਜਾਬੀ'        },
  { code: 'or', label: 'Odia',          nativeLabel: 'ଓଡ଼ିଆ'          },
  { code: 'as', label: 'Assamese',      nativeLabel: 'অসমীয়া'       },
  { code: 'ur', label: 'Urdu',          nativeLabel: 'اردو'          },
  { code: 'sa', label: 'Sanskrit',      nativeLabel: 'संस्कृतम्'      },
  { code: 'kok', label: 'Konkani',      nativeLabel: 'कोंकणी'        },
];

/**
 * Triggers Google Translate to switch to the given language code.
 * Sets the necessary googtrans cookies and dispatches events on .goog-te-combo.
 */
function triggerGoogleTranslate(langCode) {
  if (langCode === 'en') {
    // Restore original (English) by clearing cookie and triggering combo
    document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.' + window.location.hostname;
    document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + window.location.hostname;

    const select = document.querySelector('.goog-te-combo');
    if (select) {
      select.value = 'en';
      select.dispatchEvent(new Event('change'));
    }
    setTimeout(() => {
      window.location.reload();
    }, 100);
    return;
  }

  // Set cookies for both /auto/<code/ and /en/<code>
  const cookieValue = `/en/${langCode}`;
  document.cookie = `googtrans=${cookieValue}; path=/;`;
  document.cookie = `googtrans=${cookieValue}; path=/; domain=.${window.location.hostname};`;
  document.cookie = `googtrans=${cookieValue}; path=/; domain=${window.location.hostname};`;

  const select = document.querySelector('.goog-te-combo');
  if (select) {
    select.value = langCode;
    select.dispatchEvent(new Event('change'));
  } else {
    // If widget combo is not ready, reload to let the translate script parse the cookie
    setTimeout(() => {
      window.location.reload();
    }, 100);
  }
}

export const LanguageSelector = ({ variant = 'header' }) => {
  const [open, setOpen]             = useState(false);
  const [selected, setSelected]     = useState(LANGUAGES[0]);
  const dropdownRef                 = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Detect page language from existing cookie on mount
  useEffect(() => {
    const match = document.cookie.match(/googtrans=\/(?:en|auto)\/([a-z]+)/);
    if (match) {
      const found = LANGUAGES.find(l => l.code === match[1]);
      if (found) setSelected(found);
    }
  }, []);

  const handleSelect = (lang) => {
    setSelected(lang);
    setOpen(false);
    triggerGoogleTranslate(lang.code);
  };

  const isHero = variant === 'hero';

  return (
    <div
      ref={dropdownRef}
      style={{ position: 'relative', zIndex: 1000, userSelect: 'none' }}
    >
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select language"
        style={isHero ? {
          display: 'inline-flex',
          alignItems: 'center',
          gap: '7px',
          background: open ? '#F3EFFE' : '#FFFFFF',
          color: 'var(--ux4g-violet-900)',
          border: open ? '1.5px solid var(--ux4g-violet-500)' : '1.5px solid var(--ux4g-violet-200)',
          padding: '5px 14px',
          borderRadius: '999px',
          fontSize: '0.78rem',
          fontWeight: 700,
          cursor: 'pointer',
          boxShadow: 'var(--elevation-1)',
          transition: 'all 0.18s ease',
        } : {
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          background: open ? '#EFF6FF' : 'transparent',
          color: open ? '#1D4ED8' : '#475569',
          border: '1px solid ' + (open ? '#BFDBFE' : '#CBD5E1'),
          padding: '2px 7px',
          borderRadius: '4px',
          fontSize: '0.72rem',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
      >
        <Globe size={isHero ? 13 : 11} color={isHero ? 'var(--ux4g-violet-700)' : 'currentColor'} />
        <span>
          {isHero ? `Language: ${selected.nativeLabel}` : selected.nativeLabel}
        </span>
        <ChevronDown
          size={isHero ? 12 : 10}
          style={{
            transform: open ? 'rotate(180deg)' : 'rotate(0)',
            transition: 'transform 0.2s ease',
          }}
        />
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          role="listbox"
          aria-label="Available languages"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            minWidth: '190px',
            maxHeight: '280px',
            overflowY: 'auto',
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '8px',
            boxShadow: '0 8px 30px rgba(15,23,42,0.12), 0 2px 8px rgba(15,23,42,0.06)',
            animation: 'langDropFadeIn 0.18s cubic-bezier(0.16,1,0.3,1)',
          }}
        >
          {/* Header label */}
          <div
            style={{
              padding: '8px 12px 6px',
              fontSize: '0.66rem',
              fontWeight: 800,
              color: '#94A3B8',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              borderBottom: '1px solid #F1F5F9',
            }}
          >
            Select Language
          </div>

          {LANGUAGES.map((lang) => {
            const isActive = lang.code === selected.code;
            return (
              <button
                key={lang.code}
                role="option"
                type="button"
                aria-selected={isActive}
                onClick={() => handleSelect(lang)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '7px 12px',
                  border: 'none',
                  background: isActive ? '#F5F3FF' : 'transparent',
                  color: isActive ? '#5B21B6' : '#334155',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.12s ease',
                  gap: '8px',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = '#F8FAFC';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'transparent';
                }}
              >
                <span>
                  <span style={{ fontSize: '0.82rem', fontWeight: isActive ? 700 : 500 }}>
                    {lang.nativeLabel}
                  </span>
                  {lang.label !== lang.nativeLabel && (
                    <span style={{ fontSize: '0.7rem', color: '#94A3B8', marginLeft: '6px' }}>
                      {lang.label}
                    </span>
                  )}
                </span>
                {isActive && <Check size={13} color="#7C3AED" />}
              </button>
            );
          })}
        </div>
      )}

      {/* Dropdown fade-in keyframe */}
      <style>{`
        @keyframes langDropFadeIn {
          from { opacity: 0; transform: translateY(-6px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)   scale(1);    }
        }
      `}</style>
    </div>
  );
};
