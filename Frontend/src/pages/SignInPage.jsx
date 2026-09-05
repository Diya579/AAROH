import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, User, KeyRound, ArrowRight, Info } from 'lucide-react';
import { useAuth, DEMO_USERS } from '../context/AuthContext';
import { UX4GCard } from '../components/common/UX4GCard';
import { UX4GButton } from '../components/common/UX4GButton';
import { UX4GInput } from '../components/common/UX4GInput';
import { UX4GAlert } from '../components/common/UX4GAlert';

export const SignInPage = () => {
  const { signIn, isLoading, error, setError, getDashboardPath } = useAuth();
  const [userId, setUserId] = useState('meera.s@citizen');
  const [password, setPassword] = useState('password123');
  const [validationError, setValidationError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

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

  // Helper to pre-populate credentials for sprint review
  const selectRolePersona = (roleKey) => {
    const user = DEMO_USERS[roleKey];
    if (user) {
      setUserId(user.userId);
      setPassword(user.password);
      setValidationError('');
      setError('');
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

          {/* Quick Persona Switcher for Day 1 Sprint Evaluation */}
          <div style={{ marginTop: '32px', paddingTop: '22px', borderTop: '1px solid var(--ux4g-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--ux4g-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Day 1 Test Personas (Click to Load)
              </span>
              <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.68rem' }}>
                All 6 Roles
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              <button
                type="button"
                onClick={() => selectRolePersona('victim')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.victim.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.victim.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                1. Citizen / Victim
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Meera Sharma
                </span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePersona('counsellor')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.counsellor.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.counsellor.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                2. Counsellor
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Dr. Rajesh Varma
                </span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePersona('district')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.district.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.district.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                3. District Official
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Ananya Sen, IAS
                </span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePersona('state')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.state.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.state.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                4. State Official
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Shri K. Ramanathan
                </span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePersona('national')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.national.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.national.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                5. National Director
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Dr. P. Venkatachalam
                </span>
              </button>

              <button
                type="button"
                onClick={() => selectRolePersona('admin')}
                className="ux4g-focus-glow"
                style={{
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: userId === DEMO_USERS.admin.userId ? 'var(--ux4g-violet-100)' : 'var(--ux4g-bg)',
                  border: `1px solid ${userId === DEMO_USERS.admin.userId ? 'var(--ux4g-violet-400)' : 'var(--ux4g-border)'}`,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'var(--transition-fast)',
                }}
              >
                6. System Authority
                <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--ux4g-text-muted)', fontWeight: 400 }}>
                  Security & Audit
                </span>
              </button>
            </div>
          </div>
        </UX4GCard>
      </div>
    </div>
  );
};
