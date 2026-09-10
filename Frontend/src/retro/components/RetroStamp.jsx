import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, ShieldAlert, Sparkles, Clock, Lock } from 'lucide-react';

export const RetroStamp = ({ 
  type = 'verified', 
  label, 
  rotation = -2.5, 
  size = 'md',
  icon = true 
}) => {
  let stampClass = 'retro-stamp-verified';
  let IconComponent = CheckCircle2;
  let defaultLabel = 'VERIFIED';

  switch (type.toLowerCase()) {
    case 'critical':
    case 'urgent':
    case 'high':
      stampClass = 'retro-stamp-urgent';
      IconComponent = ShieldAlert;
      defaultLabel = 'URGENT DISPATCH';
      break;
    case 'amber':
    case 'warning':
    case 'medium':
    case 'pending':
      stampClass = 'retro-stamp-amber';
      IconComponent = Clock;
      defaultLabel = 'PENDING SLA';
      break;
    case 'sovereign':
    case 'nalsa':
    case 'legal':
      stampClass = 'retro-stamp-sovereign';
      IconComponent = Lock;
      defaultLabel = 'SOVEREIGN CONFIDENTIAL';
      break;
    case 'tele-manas':
    case 'verified':
    case 'low':
    case 'resolved':
    default:
      stampClass = 'retro-stamp-verified';
      IconComponent = CheckCircle2;
      defaultLabel = 'VERIFIED RECORD';
      break;
  }

  const displayText = label || defaultLabel;

  return (
    <motion.div
      className={`retro-stamp ${stampClass}`}
      style={{
        transform: `rotate(${rotation}deg)`,
        fontSize: size === 'sm' ? '0.68rem' : size === 'lg' ? '0.85rem' : '0.75rem',
        padding: size === 'sm' ? '2px 6px' : size === 'lg' ? '6px 14px' : '4px 10px',
      }}
      whileHover={{ 
        scale: 1.06, 
        rotate: 0,
        transition: { type: 'spring', stiffness: 400, damping: 15 } 
      }}
      whileTap={{ scale: 0.95 }}
    >
      {icon && <IconComponent size={size === 'sm' ? 11 : size === 'lg' ? 15 : 13} />}
      <span>{displayText}</span>
    </motion.div>
  );
};

export default RetroStamp;
