import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { UX4GButton } from './UX4GButton';

export const UX4GErrorState = ({
  title = 'Service Unavailable',
  message = 'Unable to securely retrieve monitoring information. Please verify network connectivity or retry shortly.',
  onRetry,
}) => {
  return (
    <div
      role="alert"
      style={{
        padding: '36px 24px',
        textAlign: 'center',
        backgroundColor: 'var(--ux4g-danger-bg)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--ux4g-danger-border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        maxWidth: '520px',
        margin: '24px auto',
      }}
    >
      <div
        style={{
          width: '52px',
          height: '52px',
          borderRadius: '50%',
          backgroundColor: '#FFFFFF',
          color: 'var(--ux4g-danger)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '14px',
          boxShadow: 'var(--elevation-1)',
        }}
      >
        <AlertTriangle size={26} />
      </div>

      <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--ux4g-danger-text)', marginBottom: '8px' }}>
        {title}
      </h4>

      <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-secondary)', marginBottom: onRetry ? '18px' : 0, maxWidth: '400px' }}>
        {message}
      </p>

      {onRetry && (
        <UX4GButton variant="danger" size="sm" onClick={onRetry}>
          Try Again
        </UX4GButton>
      )}
    </div>
  );
};
