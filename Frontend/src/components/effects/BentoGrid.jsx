import React from 'react';
import { motion } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';

export const BentoGrid = ({ children, className = '', columns = 3, gap = '20px' }) => {
  const { reducedMotion } = useThemeAccessibility();

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.12,
        delayChildren: 0.05,
      },
    },
  };

  if (reducedMotion) {
    return (
      <div
        className={`bento-grid ${className}`}
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
          gap: gap,
        }}
      >
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={`bento-grid ${className}`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        gap: gap,
      }}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-50px' }}
      variants={containerVariants}
    >
      {children}
    </motion.div>
  );
};

export const BentoItem = ({
  children,
  colSpan = 1,
  rowSpan = 1,
  className = '',
  style = {},
}) => {
  const { reducedMotion } = useThemeAccessibility();

  const itemVariants = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      y: 20,
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: 'spring',
        damping: 20,
        stiffness: 180,
        mass: 0.6,
      },
    },
  };

  const gridStyle = {
    gridColumn: `span ${colSpan}`,
    gridRow: `span ${rowSpan}`,
    ...style,
  };

  if (reducedMotion) {
    return (
      <div className={`bento-item ${className}`} style={gridStyle}>
        {children}
      </div>
    );
  }

  return (
    <motion.div
      variants={itemVariants}
      className={`bento-item ${className}`}
      style={gridStyle}
    >
      {children}
    </motion.div>
  );
};
