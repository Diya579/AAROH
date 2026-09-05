import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeAccessibilityContext = createContext(null);

export const ThemeAccessibilityProvider = ({ children }) => {
  // Universal Motion State (persisted & initialized with system preference)
  const [reducedMotion, setReducedMotion] = useState(() => {
    const saved = localStorage.getItem('aaroh_reduced_motion');
    if (saved !== null) return saved === 'true';
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  // High Contrast State
  const [highContrast, setHighContrast] = useState(() => {
    return localStorage.getItem('aaroh_high_contrast') === 'true';
  });

  // Font Scaling (0.9 = A-, 1.0 = A, 1.15 = A+)
  const [fontScale, setFontScale] = useState(() => {
    const saved = localStorage.getItem('aaroh_font_scale');
    return saved ? parseFloat(saved) : 1.0;
  });

  // Global Offcanvas Drawer state
  const [offcanvasOpen, setOffcanvasOpen] = useState(false);
  const [offcanvasContent, setOffcanvasContent] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-reduced-motion', reducedMotion ? 'true' : 'false');
    localStorage.setItem('aaroh_reduced_motion', String(reducedMotion));
  }, [reducedMotion]);

  useEffect(() => {
    document.documentElement.setAttribute('data-contrast', highContrast ? 'high' : 'normal');
    localStorage.setItem('aaroh_high_contrast', String(highContrast));
  }, [highContrast]);

  useEffect(() => {
    document.documentElement.style.setProperty('--font-scale', String(fontScale));
    localStorage.setItem('aaroh_font_scale', String(fontScale));
  }, [fontScale]);

  const toggleReducedMotion = () => {
    setReducedMotion(prev => !prev);
  };

  const toggleHighContrast = () => {
    setHighContrast(prev => !prev);
  };

  const adjustFontScale = (scale) => {
    setFontScale(scale);
  };

  const openOffcanvas = (content) => {
    setOffcanvasContent(content);
    setOffcanvasOpen(true);
  };

  const closeOffcanvas = () => {
    setOffcanvasOpen(false);
  };

  return (
    <ThemeAccessibilityContext.Provider
      value={{
        reducedMotion,
        toggleReducedMotion,
        highContrast,
        toggleHighContrast,
        fontScale,
        adjustFontScale,
        offcanvasOpen,
        offcanvasContent,
        openOffcanvas,
        closeOffcanvas,
      }}
    >
      {children}
    </ThemeAccessibilityContext.Provider>
  );
};

export const useThemeAccessibility = () => {
  const context = useContext(ThemeAccessibilityContext);
  if (!context) {
    throw new Error('useThemeAccessibility must be used within ThemeAccessibilityProvider');
  }
  return context;
};
