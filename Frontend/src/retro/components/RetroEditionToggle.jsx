import React from 'react';
import { motion } from 'framer-motion';
import { Newspaper, LayoutGrid } from 'lucide-react';

export const RetroEditionToggle = ({ isGazette, onToggle }) => {
  return (
    <motion.button
      onClick={onToggle}
      className="retro-floating-seal"
      title={isGazette ? 'Switch to Classic UX4G Gov Edition' : 'Switch to Newspaper Gazette Edition'}
      aria-label="Toggle Interface Edition"
      whileHover={{ scale: 1.15, rotate: 6 }}
      whileTap={{ scale: 0.92 }}
    >
      {isGazette ? (
        <>
          <LayoutGrid size={18} style={{ marginBottom: '2px' }} />
          <span>CLASSIC</span>
          <span style={{ fontSize: '0.55rem', opacity: 0.85 }}>UX4G</span>
        </>
      ) : (
        <>
          <Newspaper size={18} style={{ marginBottom: '2px' }} />
          <span>GAZETTE</span>
          <span style={{ fontSize: '0.55rem', opacity: 0.85 }}>RETRO</span>
        </>
      )}
    </motion.button>
  );
};

export default RetroEditionToggle;
