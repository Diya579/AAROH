import React, { useState } from 'react';
import { Info, AlertTriangle, AlertOctagon, CheckCircle2, X } from 'lucide-react';

export const UX4GAlert = ({
  variant = 'info', // 'info' | 'warning' | 'danger' | 'success'
  title,
  children,
  dismissible = false,
  onDismiss,
  className = '',
}) => {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  const getAlertStyles = () => {
    switch (variant) {
      case 'warning':
        return {
          bg: 'var(--ux4g-warning-bg)',
          border: 'var(--ux4g-warning-border)',
          color: 'var(--ux4g-warning-text)',
          Icon: AlertTriangle,
        };
      case 'danger':
        return {
          bg: 'var(--ux4g-danger-bg)',
          border: 'var(--ux4g-danger-border)',
          color: 'var(--ux4g-danger-text)',
          Icon: AlertOctagon,
        };
      case 'success':
        return {
          bg: 'var(--ux4g-success-bg)',
          border: 'var(--ux4g-success-border)',
          color: 'var(--ux4g-success-text)',
          Icon: CheckCircle2,
        };
      case 'info':
      default:
        return {
          bg: 'var(--ux4g-info-bg)',
          border: 'var(--ux4g-info-border)',
          color: 'var(--ux4g-info-text)',
          Icon: Info,
        };
    }
  };

  const { bg, border, color, Icon } = getAlertStyles();

  const handleClose = () => {
    setVisible(false);
    if (onDismiss) onDismiss();
  };

  return (
    <div
      role="alert"
      className={`ux4g-alert ${className}`}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '14px 18px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: bg,
        border: `1px solid ${border}`,
        color: color,
        marginBottom: '16px',
        boxShadow: 'var(--elevation-1)',
        position: 'relative',
        transition: 'var(--transition-fast)',
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>
        <Icon size={20} />
      </div>

      <div style={{ flex: 1 }}>
        {title && (
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px', color: 'inherit' }}>
            {title}
          </h4>
        )}
        <div style={{ fontSize: '0.88rem', lineHeight: '1.5', opacity: 0.95 }}>{children}</div>
      </div>

      {dismissible && (
        <button
          type="button"
          onClick={handleClose}
          aria-label="Dismiss alert"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'inherit',
            opacity: 0.7,
            padding: '2px',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <X size={18} />
        </button>
      )}
    </div>
  );
};
