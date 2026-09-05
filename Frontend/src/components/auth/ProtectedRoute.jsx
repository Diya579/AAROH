import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UX4GAlert } from '../common/UX4GAlert';
import { UX4GButton } from '../common/UX4GButton';

export const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, currentUser, getDashboardPath } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to sign in page preserving intended destination
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  // Check if current user's role is permitted
  if (allowedRoles.length > 0 && !allowedRoles.includes(currentUser.role)) {
    return (
      <div style={{ maxWidth: '640px', margin: '60px auto', padding: '0 20px' }}>
        <UX4GAlert
          variant="danger"
          title="Access Restricted (RBAC Enforcement)"
        >
          <p style={{ marginBottom: '12px' }}>
            Your authenticated identity (<strong>{currentUser.name}</strong>, Role: <strong>{currentUser.role}</strong>) does not hold authorization to inspect or manage this portal scope.
          </p>
          <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', marginBottom: '16px' }}>
            In accordance with Government of India AAROH RBAC specifications (Rule 3 & Rule 23), cross-jurisdiction or elevated privileges cannot be accessed without system authority delegation.
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <UX4GButton
              variant="primary"
              size="sm"
              onClick={() => window.location.href = getDashboardPath(currentUser.role)}
            >
              Return to My Authorized Dashboard
            </UX4GButton>
          </div>
        </UX4GAlert>
      </div>
    );
  }

  return children;
};
