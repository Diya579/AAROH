import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, User, KeyRound, ArrowRight, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UX4GCard } from '../components/common/UX4GCard';
import { UX4GButton } from '../components/common/UX4GButton';
import { UX4GInput } from '../components/common/UX4GInput';
import { UX4GAlert } from '../components/common/UX4GAlert';

export const SignInPage = () => {
  const { signIn, isLoading, error, setError, getDashboardPath } = useAuth();
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [validationError, setValidationError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    setError('');

    if (!userId.trim()) {
      setValidationError('Please enter your authorized Government User ID or identifier.');
      return;
    }
    if (!password) {
      setValidationError('Please enter your access password.');
      return;
    }

    const result = await signIn(userId, password);
    if (result.success) {
      const from = location.state?.from?.pathname || getDashboardPath(result.role);
      navigate(from, { replace: true });
    }
  };

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 180px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        backgroundColor: 'var(--ux4g-bg)',
      }}
    >
      <div style={{ width: '100%', maxWidth: '520px' }}>
        {/* Authentication Card */}
        <UX4GCard elevation={3} liftOnHover={false} padding="36px 32px">
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div
              style={{
                width: '54px',
                height: '54px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-50)',
                color: 'var(--ux4g-violet-700)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
                border: '1.5px solid var(--ux4g-violet-200)',
                boxShadow: 'var(--elevation-1)',
              }}
            >
              <Shield size={28} />
            </div>

            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', letterSpacing: '-0.01em' }}>
              Authorized Portal Sign In
            </h2>
            <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-muted)', marginTop: '6px' }}>
              AAROH Mental Health Monitoring & Distress Prediction System
            </p>
          </div>

          {/* Critical Architecture Rule: NO Public Registration Notice */}
          <div
            style={{
              padding: '10px 14px',
              backgroundColor: 'var(--ux4g-violet-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-violet-200)',
              fontSize: '0.8rem',
              color: 'var(--ux4g-violet-900)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '20px',
            }}
          >
            <Info size={18} color="var(--ux4g-violet-700)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Authorized Access Only:</strong> Beneficiary and official accounts are provisioned exclusively through authorized government departments. <em>No public registration is permitted.</em>
            </div>
          </div>

          {/* Error notifications */}
          {(error || validationError) && (
            <UX4GAlert variant="danger" dismissible onDismiss={() => { setError(''); setValidationError(''); }}>
              {error || validationError}
            </UX4GAlert>
          )}

          {/* Sign In Form */}
          <form onSubmit={handleSubmit} noValidate>
            <UX4GInput
              label="Authorized User ID / Identifier"
              id="signin-user-id"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="e.g. meera.s@citizen or official@nic.in"
              leadingIcon={User}
              required
              helperText="Assigned by District Welfare Officer or Ministry Authority"
            />

            <UX4GInput
              label="Secure Password"
              id="signin-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your security password"
              leadingIcon={KeyRound}
              allowShowPassword={true}
              required
            />

            <div style={{ marginTop: '24px' }}>
              <UX4GButton
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                style={{ width: '100%' }}
                icon={ArrowRight}
                iconPosition="right"
              >
                Authenticate & Access Portal
              </UX4GButton>
            </div>
          </form>
        </UX4GCard>
      </div>
    </div>
  );
};
