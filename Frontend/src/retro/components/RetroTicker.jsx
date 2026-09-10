import React from 'react';
import { motion } from 'framer-motion';
import { Radio, AlertTriangle, CheckCircle, ShieldCheck, Flame } from 'lucide-react';

export const RetroTicker = ({ items }) => {
  const defaultItems = [
    { icon: Radio, text: 'LIVE DISPATCH: 142 ATROCITY-LINKED CASES UNDER ACTIVE CLINICAL VIGILANCE' },
    { icon: ShieldCheck, text: 'ZERO (0) OVERDUE SLAs RECORDED ACROSS PILOT DISTRICTS' },
    { icon: CheckCircle, text: 'ALGORITHMIC CONFIDENCE SCORE INDEX CALIBRATED AT 89%' },
    { icon: Flame, text: 'VOICE ACOUSTIC JITTER & PITCH DEVIATION PIPELINE OPERATIONAL' },
    { icon: Radio, text: 'TELE-MANAS 14416 & NALSA LEGAL AID SECURE DIRECTORY CONNECTED' },
  ];

  const tickerList = items || defaultItems;
  // Double list for infinite seamless loop
  const duplicatedList = [...tickerList, ...tickerList, ...tickerList];

  return (
    <div className="retro-ticker-tape" aria-label="Live Dispatch Ticker Tape">
      <motion.div
        style={{ display: 'flex', gap: '36px', width: 'max-content' }}
        animate={{ x: ['0%', '-33.333%'] }}
        transition={{
          repeat: Infinity,
          ease: 'linear',
          duration: 35,
        }}
        whileHover={{ animationPlayState: 'paused' }}
      >
        {duplicatedList.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {Icon && <Icon size={13} style={{ color: '#FDE68A' }} />}
              <span>{item.text}</span>
              <span style={{ opacity: 0.45, marginLeft: '16px' }}>✦</span>
            </div>
          );
        })}
      </motion.div>
    </div>
  );
};

export default RetroTicker;
