import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UX4GCard } from '../../components/common/UX4GCard';
import { UX4GButton } from '../../components/common/UX4GButton';

export const UnauthorizedPage = () => {
  const { currentUser, getDashboardPath } = useAuth();

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 200px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        backgroundColor: 'var(--ux4g-bg)',
      }}
    >
      <UX4GCard elevation={3} liftOnHover={false} style={{ maxWidth: '540px', textAlign: 'center', padding: '40px 32px' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'var(--ux4g-danger-bg)',
            color: 'var(--ux4g-danger)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
          }}
        >
          <ShieldAlert size={36} />
        </div>

        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', marginBottom: '10px' }}>
          403 — Unauthorized Scope
        </h2>

        <p style={{ fontSize: '0.92rem', color: 'var(--ux4g-text-secondary)', lineHeight: 1.6, marginBottom: '24px' }}>
          Under Government of India AAROH RBAC rules (Rule 3 & Section 23), your current identity is restricted from accessing this operational view.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
          {currentUser ? (
            <Link to={getDashboardPath(currentUser.role)} style={{ textDecoration: 'none' }}>
              <UX4GButton variant="primary" size="md">
                Return to My {currentUser.role} Portal
              </UX4GButton>
            </Link>
          ) : (
            <Link to="/signin" style={{ textDecoration: 'none' }}>
              <UX4GButton variant="primary" size="md">
                Sign In with Authorized Credentials
              </UX4GButton>
            </Link>
          )}
        </div>
      </UX4GCard>
    </div>
  );
};

export const NotFoundPage = () => {
  return (
    <div
      style={{
        minHeight: 'calc(100vh - 200px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        backgroundColor: 'var(--ux4g-bg)',
      }}
    >
      <UX4GCard elevation={2} liftOnHover={false} style={{ maxWidth: '480px', textAlign: 'center', padding: '40px 32px' }}>
        <h2 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--ux4g-violet-700)', marginBottom: '10px' }}>
          404
        </h2>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '12px' }}>
          Page Not Found
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--ux4g-text-secondary)', marginBottom: '24px' }}>
          The requested system endpoint does not exist or has been relocated.
        </p>
        <Link to="/" style={{ textDecoration: 'none' }}>
          <UX4GButton variant="primary" size="md" icon={ArrowLeft}>
            Return to Home Page
          </UX4GButton>
        </Link>
      </UX4GCard>
    </div>
  );
};
