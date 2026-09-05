import React from 'react';
import { Inbox } from 'lucide-react';
import { UX4GButton } from './UX4GButton';

export const UX4GEmptyState = ({
  icon: Icon = Inbox,
  title = 'No records found',
  description = 'There are no active records matching the current criteria or filters.',
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        padding: '48px 24px',
        textAlign: 'center',
        backgroundColor: 'var(--ux4g-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px dashed var(--ux4g-border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        maxWidth: '520px',
        margin: '20px auto',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'var(--ux4g-violet-50)',
          color: 'var(--ux4g-violet-700)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '16px',
        }}
      >
        <Icon size={28} />
      </div>

      <h4 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--ux4g-text-primary)', marginBottom: '8px' }}>
        {title}
      </h4>

      <p style={{ fontSize: '0.9rem', color: 'var(--ux4g-text-muted)', marginBottom: actionLabel ? '20px' : 0, maxWidth: '380px' }}>
        {description}
      </p>

      {actionLabel && onAction && (
        <UX4GButton variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </UX4GButton>
      )}
    </div>
  );
};
