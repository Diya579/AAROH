import React, { useRef, useState } from 'react';
import { motion, useSpring } from 'framer-motion';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';

export const KineticTiltCard = ({
  children,
  elevation = 1,
  className = '',
  style = {},
  maxTilt = 12,
  glare = true,
  onClick,
}) => {
  const { reducedMotion } = useThemeAccessibility();
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50 });

  const springConfig = { damping: 20, stiffness: 260, mass: 0.5 };
  const rotateX = useSpring(0, springConfig);
  const rotateY = useSpring(0, springConfig);

  const handleMouseMove = (e) => {
    if (reducedMotion || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const xPct = (mouseX / width) - 0.5;
    const yPct = (mouseY / height) - 0.5;

    // Invert Y for standard natural 3D tilt
    rotateX.set(-yPct * maxTilt);
    rotateY.set(xPct * maxTilt);

    setGlarePosition({
      x: (mouseX / width) * 100,
      y: (mouseY / height) * 100,
    });
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    rotateX.set(0);
    rotateY.set(0);
  };

  if (reducedMotion) {
    return (
      <div
        className={`ux4g-card elevation-${elevation} ${className}`}
        style={{
          borderRadius: 'var(--radius-lg)',
          backgroundColor: '#FFFFFF',
          border: '1px solid var(--ux4g-border)',
          padding: '24px',
          ...style,
        }}
        onClick={onClick}
      >
        {children}
      </div>
    );
  }

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        perspective: 1000,
        transformStyle: 'preserve-3d',
      }}
      className={`kinetic-tilt-card-container ${className}`}
    >
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: 'preserve-3d',
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--ux4g-border)',
          boxShadow: isHovered ? 'var(--elevation-3)' : 'var(--elevation-1)',
          padding: '24px',
          position: 'relative',
          overflow: 'hidden',
          transition: 'box-shadow 0.25s ease, border-color 0.25s ease',
          borderColor: isHovered ? 'var(--ux4g-violet-200)' : 'var(--ux4g-border)',
          cursor: onClick ? 'pointer' : 'default',
          ...style,
        }}
      >
        {/* Specular Glare Glow */}
        {glare && isHovered && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              borderRadius: 'inherit',
              background: `radial-gradient(circle 240px at ${glarePosition.x}% ${glarePosition.y}%, rgba(109, 52, 236, 0.08), transparent 70%)`,
              zIndex: 2,
            }}
          />
        )}

        {/* 3D Elevated Parallax Content Layer */}
        <div style={{ transform: 'translateZ(20px)', position: 'relative', zIndex: 3 }}>
          {children}
        </div>
      </motion.div>
    </motion.div>
  );
};
