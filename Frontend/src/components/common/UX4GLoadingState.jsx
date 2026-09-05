import React from 'react';

export const UX4GLoadingState = ({ message = 'Loading system data...', count = 3 }) => {
  return (
    <div style={{ width: '100%', padding: '24px 0' }} role="status" aria-live="polite">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <div
          style={{
            width: '18px',
            height: '18px',
            border: '2.5px solid var(--ux4g-violet-300)',
            borderTopColor: 'var(--ux4g-violet-700)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <span style={{ fontSize: '0.9rem', color: 'var(--ux4g-text-secondary)', fontWeight: 500 }}>
          {message}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            style={{
              height: '76px',
              backgroundColor: 'var(--ux4g-surface)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-border)',
              padding: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--ux4g-bg-subtle)',
                animation: 'pulse 1.5s ease-in-out infinite',
              }}
            />
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div
                style={{
                  width: '40%',
                  height: '14px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--ux4g-bg-subtle)',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
              <div
                style={{
                  width: '70%',
                  height: '12px',
                  borderRadius: '4px',
                  backgroundColor: 'var(--ux4g-bg-subtle)',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.25; }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
