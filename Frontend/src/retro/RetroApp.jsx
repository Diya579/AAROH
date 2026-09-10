import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { RetroHeader } from './components/RetroHeader';
import { RetroFooter } from './components/RetroFooter';
import { RetroEditionToggle } from './components/RetroEditionToggle';
import { RetroHomePage } from './pages/RetroHomePage';
import { RetroVictimView } from './pages/RetroVictimView';
import { RetroCounsellorView } from './pages/RetroCounsellorView';
import { RetroAnalyticsView } from './pages/RetroAnalyticsView';

// Import Retro Newspaper & Cardboard Stylesheet
import './styles/retro-newspaper.css';

export const RetroApp = ({ onSwitchEdition }) => {
  return (
    <div className="retro-gazette-wrapper">
      {/* Tactile Cardboard & Paper Grain Overlay */}
      <div className="retro-grain-overlay" aria-hidden="true" />

      {/* Newspaper Masthead Header */}
      <RetroHeader onSwitchToClassic={onSwitchEdition} />

      {/* Main Newspaper Viewport */}
      <main style={{ minHeight: 'calc(100vh - 280px)' }}>
        <Routes>
          <Route path="/" element={<RetroHomePage />} />
          <Route path="/retro/victim" element={<RetroVictimView />} />
          <Route path="/retro/counsellor" element={<RetroCounsellorView />} />
          <Route path="/retro/analytics" element={<RetroAnalyticsView />} />
          {/* Fallback to home */}
          <Route path="*" element={<RetroHomePage />} />
        </Routes>
      </main>

      {/* Newsroom Colophon Footer */}
      <RetroFooter />

      {/* Floating Wax-Seal / Brass Edition Toggle Button */}
      <RetroEditionToggle isGazette={true} onToggle={onSwitchEdition} />
    </div>
  );
};

export default RetroApp;
