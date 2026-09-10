import React from 'react';

/**
 * AarohBrandMark Component
 * Sleek, globally accepted minimalist brand glyph representing
 * Acoustic Resonance, Longitudinal Care & Human Dignity.
 */
export const AshokaEmblem = ({ height = 40, className = '', style = {} }) => {
  return (
    <div
      className={`aaroh-brand-mark ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: `${height}px`,
        width: `${height}px`,
        borderRadius: '10px',
        backgroundColor: '#3A2312',
        color: '#F7F1E6',
        border: '1.5px solid #2B1508',
        boxShadow: '2px 2px 0px #2B1508',
        flexShrink: 0,
        userSelect: 'none',
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
      title="AAROH — Acoustic Intelligence & Care"
      aria-label="AAROH Brand Mark"
    >
      <svg
        width={height * 0.65}
        height={height * 0.65}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Modern Stylized A with Soundwave Core */}
        <path
          d="M12 2L4 21H7.8L9.7 16.2H14.3L16.2 21H20L12 2Z"
          fill="#F7F1E6"
        />
        {/* Inner Waveform Accent */}
        <path
          d="M12 7.2L10.5 12.8H13.5L12 7.2Z"
          fill="#3A2312"
        />
        {/* Kinetic Resonance Spark */}
        <circle cx="12" cy="11.5" r="1.2" fill="#CDB397" />
      </svg>
    </div>
  );
};
