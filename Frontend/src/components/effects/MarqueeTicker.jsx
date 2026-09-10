import React from 'react';
import { motion } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';

export const MarqueeTicker = ({
  items = [
    'AI-POWERED DISTRESS MONITORING',
    'DPDP ACT 2023 COMPLIANT',
    '24X7 TELE-MANAS: 14416',
    'HUMAN-IN-THE-LOOP CLINICAL OVERSIGHT',
    'DIGNITY & REHABILITATION FIRST',
    'ZERO AUTOMATED PENALTIES',
    'STATUTORY DISTRICT MAGISTRATE SLAs',
    'END-TO-END ENCRYPTED SPEECH ASR',
  ],
  speed = 24, // seconds per full loop
  direction = 'left',
  className = '',
}) => {
  const { reducedMotion } = useThemeAccessibility();

  // Duplicate items array 3 times to ensure infinite seamless continuation
  const repeatedItems = [...items, ...items, ...items];

  return (
    <div
      className={`marquee-ticker-wrapper ${className}`}
      style={{
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        display: 'flex',
        alignItems: 'center',
        background: 'linear-gradient(90deg, #F3EFFE 0%, #EDE7F6 50%, #F3EFFE 100%)',
        borderTop: '1px solid var(--ux4g-violet-200)',
        borderBottom: '1px solid var(--ux4g-violet-200)',
        padding: '12px 0',
        position: 'relative',
        userSelect: 'none',
      }}
    >
      {/* Edge Gradient Mask for seamless fade */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '60px',
          background: 'linear-gradient(to right, #F3EFFE, transparent)',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          right: 0,
          top: 0,
          bottom: 0,
          width: '60px',
          background: 'linear-gradient(to left, #F3EFFE, transparent)',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      />

      <motion.div
        style={{
          display: 'flex',
          gap: '32px',
          alignItems: 'center',
          willChange: 'transform',
        }}
        animate={
          reducedMotion
            ? { x: 0 }
            : {
                x: direction === 'left' ? ['0%', '-50%'] : ['-50%', '0%'],
              }
        }
        transition={{
          repeat: Infinity,
          ease: 'linear',
          duration: speed,
        }}
      >
        {repeatedItems.map((text, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '24px',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: 'var(--ux4g-violet-900)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              flexShrink: 0,
            }}
          >
            <span>{text}</span>
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-400)',
                display: 'inline-block',
              }}
            />
          </div>
        ))}
      </motion.div>
    </div>
  );
};
