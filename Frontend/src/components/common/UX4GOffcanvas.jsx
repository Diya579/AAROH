import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export const UX4GOffcanvas = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  position = 'right', // 'right' | 'left'
  width = '440px',
}) => {
  // Handle ESC key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="ux4g-offcanvas-backdrop"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Frictionless Glide Side Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`ux4g-offcanvas-drawer ${isOpen ? 'open' : ''}`}
        style={{
          width: `min(${width}, 94vw)`,
          [position]: 0,
          borderLeft: position === 'right' ? '1px solid var(--ux4g-border)' : 'none',
          borderRight: position === 'left' ? '1px solid var(--ux4g-border)' : 'none',
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--ux4g-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--ux4g-surface)',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
              {title}
            </h3>
            {subtitle && (
              <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-muted)', marginTop: '2px' }}>
                {subtitle}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close drawer"
            className="ux4g-focus-glow"
            style={{
              background: 'var(--ux4g-bg-subtle)',
              border: '1px solid var(--ux4g-border)',
              borderRadius: 'var(--radius-sm)',
              width: '34px',
              height: '34px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--ux4g-text-secondary)',
              transition: 'var(--transition-fast)',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Drawer Body with clean scroll */}
        <div
          style={{
            padding: '24px',
            overflowY: 'auto',
            flex: 1,
            backgroundColor: 'var(--ux4g-surface)',
          }}
        >
          {children}
        </div>
      </div>
    </>
  );
};
