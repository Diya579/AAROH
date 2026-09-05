import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

export const UX4GAccordionItem = ({
  title,
  subtitle,
  children,
  isOpen,
  onToggle,
  id,
  stepNumber,
  badge,
}) => {
  const contentRef = useRef(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (isOpen && contentRef.current) {
      setHeight(contentRef.current.scrollHeight);
    } else {
      setHeight(0);
    }
  }, [isOpen]);

  const itemId = id || `accordion-${title.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <div
      style={{
        border: '1px solid var(--ux4g-border)',
        borderRadius: 'var(--radius-md)',
        marginBottom: '10px',
        backgroundColor: 'var(--ux4g-surface)',
        overflow: 'hidden',
        transition: 'var(--transition-fast)',
        boxShadow: isOpen ? 'var(--elevation-2)' : 'var(--elevation-1)',
      }}
    >
      <button
        type="button"
        id={`${itemId}-header`}
        aria-expanded={isOpen}
        aria-controls={`${itemId}-content`}
        onClick={onToggle}
        className="ux4g-focus-glow"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          background: isOpen ? 'var(--ux4g-violet-50)' : 'var(--ux4g-surface)',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          transition: 'var(--transition-fast)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1 }}>
          {stepNumber !== undefined && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                backgroundColor: isOpen ? 'var(--ux4g-violet-700)' : 'var(--ux4g-bg-subtle)',
                color: isOpen ? '#FFFFFF' : 'var(--ux4g-text-secondary)',
                fontSize: '0.85rem',
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {stepNumber}
            </span>
          )}
          <div>
            <h4
              style={{
                fontSize: '0.975rem',
                fontWeight: 600,
                color: isOpen ? 'var(--ux4g-violet-900)' : 'var(--ux4g-text-primary)',
              }}
            >
              {title}
            </h4>
            {subtitle && (
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>
                {subtitle}
              </p>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {badge}
          <div
            style={{
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              color: isOpen ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-muted)',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <ChevronDown size={20} />
          </div>
        </div>
      </button>

      {/* Smooth height transition collapsible container */}
      <div
        id={`${itemId}-content`}
        role="region"
        aria-labelledby={`${itemId}-header`}
        style={{
          height: `${height}px`,
          overflow: 'hidden',
          transition: 'height 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        <div ref={contentRef} style={{ padding: '18px 20px', borderTop: '1px solid var(--ux4g-border-subtle)' }}>
          {children}
        </div>
      </div>
    </div>
  );
};

export const UX4GAccordion = ({ items = [], allowMultiple = false, className = '' }) => {
  const [openIndexes, setOpenIndexes] = useState([0]);

  const handleToggle = (index) => {
    if (allowMultiple) {
      setOpenIndexes((prev) =>
        prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
      );
    } else {
      setOpenIndexes((prev) => (prev.includes(index) ? [] : [index]));
    }
  };

  return (
    <div className={`ux4g-accordion-group ${className}`}>
      {items.map((item, index) => (
        <UX4GAccordionItem
          key={item.id || index}
          title={item.title}
          subtitle={item.subtitle}
          stepNumber={item.stepNumber ?? (index + 1)}
          badge={item.badge}
          isOpen={openIndexes.includes(index)}
          onToggle={() => handleToggle(index)}
        >
          {item.content}
        </UX4GAccordionItem>
      ))}
    </div>
  );
};
