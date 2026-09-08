import React from 'react';
import ashokaEmblemImg from '../../assets/ashoka-emblem.png';

/**
 * AshokaEmblem Component
 * Uses the official State Emblem of India (Ashoka Stambh / Satyameva Jayate)
 * provided by the user, adhering strictly to UX4G Government of India standards.
 */
export const AshokaEmblem = ({ height = 52, className = '', style = {} }) => {
  return (
    <div
      className={`ashoka-stambh-emblem ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: `${height}px`,
        flexShrink: 0,
        userSelect: 'none',
        ...style,
      }}
      title="State Emblem of India — सत्यमेव जयते"
      aria-label="State Emblem of India — सत्यमेव जयते"
    >
      <img
        src={ashokaEmblemImg}
        alt="State Emblem of India — सत्यमेव जयते"
        style={{
          height: `${height}px`,
          width: 'auto',
          maxHeight: '100%',
          objectFit: 'contain',
          display: 'block',
        }}
      />
    </div>
  );
};
