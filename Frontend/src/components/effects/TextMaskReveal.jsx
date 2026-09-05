import React from 'react';
import { motion } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';

export const TextMaskReveal = ({
  lines = [],
  as: Component = 'h2',
  className = '',
  style = {},
  delay = 0,
  stagger = 0.12,
}) => {
  const { reducedMotion } = useThemeAccessibility();

  if (reducedMotion) {
    return (
      <Component className={className} style={style}>
        {lines.map((line, idx) => (
          <span key={idx} style={{ display: 'block' }}>
            {line}
          </span>
        ))}
      </Component>
    );
  }

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: stagger,
        delayChildren: delay,
      },
    },
  };

  const lineVariants = {
    hidden: {
      y: '115%',
      opacity: 0,
      rotateX: -10,
      clipPath: 'polygon(0 100%, 100% 100%, 100% 100%, 0% 100%)',
    },
    visible: {
      y: '0%',
      opacity: 1,
      rotateX: 0,
      clipPath: 'polygon(0 0%, 100% 0%, 100% 100%, 0% 100%)',
      transition: {
        type: 'spring',
        damping: 24,
        stiffness: 140,
        mass: 0.8,
      },
    },
  };

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-40px' }}
      variants={containerVariants}
      style={{ overflow: 'hidden' }}
    >
      <Component className={className} style={{ ...style, margin: 0 }}>
        {lines.map((line, idx) => (
          <span
            key={idx}
            style={{
              display: 'block',
              overflow: 'hidden',
              paddingBottom: '4px',
              perspective: 1000,
            }}
          >
            <motion.span
              variants={lineVariants}
              style={{
                display: 'inline-block',
                willChange: 'transform, opacity',
              }}
            >
              {line}
            </motion.span>
          </span>
        ))}
      </Component>
    </motion.div>
  );
};
