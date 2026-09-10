import React, { useEffect, useState } from 'react';
import { Globe } from 'lucide-react';

export const GoogleTranslateWidget = ({ compact = false }) => {
  const [selectedLang, setSelectedLang] = useState('en');

  useEffect(() => {
    // Define global callback for Google Translate initialization
    window.googleTranslateElementInit = () => {
      if (window.google && window.google.translate) {
        new window.google.translate.TranslateElement(
          {
            pageLanguage: 'en',
            includedLanguages: 'en,hi,bn,te,ta,mr,gu,kn,ml,ur,pa',
            autoDisplay: false,
          },
          'google_translate_element'
        );
      }
    };

    // Check if script is already present
    if (!document.getElementById('google-translate-script')) {
      const script = document.createElement('script');
      script.id = 'google-translate-script';
      script.type = 'text/javascript';
      script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
      script.async = true;
      document.body.appendChild(script);
    }
  }, []);

  const handleLanguageChange = (langCode) => {
    setSelectedLang(langCode);

    // Set cookie that Google Translate reads
    document.cookie = `googtrans=/en/${langCode}; path=/; domain=${window.location.hostname}`;
    document.cookie = `googtrans=/en/${langCode}; path=/;`;

    // Attempt to trigger the native Google select box if available
    const selectEl = document.querySelector('.goog-te-combo');
    if (selectEl) {
      selectEl.value = langCode;
      selectEl.dispatchEvent(new Event('change'));
    } else {
      // Fallback reload if combo element isn't populated yet
      window.location.reload();
    }
  };

  const languages = [
    { code: 'en', label: 'English (EN)', native: 'English' },
    { code: 'hi', label: 'हिन्दी (Hindi)', native: 'हिन्दी' },
    { code: 'bn', label: 'বাংলা (Bengali)', native: 'বাংলা' },
    { code: 'te', label: 'తెలుగు (Telugu)', native: 'తెలుగు' },
    { code: 'ta', label: 'தமிழ் (Tamil)', native: 'தமிழ்' },
    { code: 'mr', label: 'मराठी (Marathi)', native: 'मराठी' },
    { code: 'gu', label: 'ગુજરાતી (Gujarati)', native: 'ગુજરાતી' },
    { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', native: 'ಕನ್ನಡ' },
    { code: 'ml', label: 'മലയാളം (Malayalam)', native: 'മലയാളം' },
    { code: 'ur', label: 'اردو (Urdu)', native: 'اردو' },
    { code: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)', native: 'ਪੰਜਾਬੀ' },
  ];

  return (
    <div className="retro-translate-container" style={{ display: 'inline-flex', alignItems: 'center' }}>
      {/* Hidden container where Google mounts its combo select */}
      <div id="google_translate_element" style={{ display: 'none' }}></div>

      <div className="retro-translate-picker" title="Google Translate Language Selector">
        <Globe size={14} style={{ color: 'var(--retro-ink-black)' }} />
        <span style={{ fontSize: '0.72rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          {compact ? 'LANG:' : 'DISPATCH LANG:'}
        </span>
        <select
          value={selectedLang}
          onChange={(e) => handleLanguageChange(e.target.value)}
          className="retro-translate-select"
          aria-label="Select Dispatch Language via Google Translate"
        >
          {languages.map((l) => (
            <option key={l.code} value={l.code}>
              {compact ? `${l.code.toUpperCase()} • ${l.native}` : `${l.label}`}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default GoogleTranslateWidget;
