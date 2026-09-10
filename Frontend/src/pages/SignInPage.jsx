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
              AAROH Paralinguistic Distress Modeling & Resilience Platform
            </p>
          </div>

          {/* Critical Architecture Rule: Restricted Access Notice */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--ux4g-violet-50)',
              borderRadius: 'var(--radius-md)',
              border: '1.5px solid #3A2312',
              fontSize: '0.8rem',
              color: 'var(--ux4g-violet-900)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '20px',
              boxShadow: '2px 2px 0px #3A2312',
            }}
          >
            <Info size={18} color="var(--ux4g-violet-700)" style={{ flexShrink: 0 }} />
            <div>
              <strong>Restricted Access:</strong> Participant and specialist accounts are provisioned exclusively through accredited care networks. <em>Self-registration is disabled for privacy & protection.</em>
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
              placeholder="e.g. meera.s@citizen or dr.rajesh@aaroh.gov.in"
              leadingIcon={User}
              required
              helperText="Provisioned by Clinical Care Director or System Administrator"
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

          {/* Quick Demo Persona Fillers */}
          <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1.5px dashed #3A2312' }}>
            <div style={{ fontSize: '0.74rem', fontWeight: 800, color: 'var(--ux4g-violet-800)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '12px', textAlign: 'center' }}>
              ✦ Demo Evaluation Credentials (Click to Autofill)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { label: 'Participant', id: 'meera.s@citizen' },
                { label: 'Counsellor', id: 'dr.rajesh@aaroh.gov.in' },
                { label: 'Regional Lead', id: 'ananya.sen@ias.nic.in' },
                { label: 'State Director', id: 'k.ramanathan@delhi.gov.in' },
                { label: 'Global Lead', id: 'p.venkat@socialjustice.gov.in' },
                { label: 'Security Admin', id: 'sysadmin@aaroh.nic.in' },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setUserId(p.id);
                    setPassword('password123');
                    setValidationError('');
                    setError('');
                  }}
                  style={{
                    padding: '6px 8px',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    backgroundColor: userId === p.id ? 'var(--ux4g-violet-700)' : '#FAF4EB',
                    color: userId === p.id ? '#FAF4EB' : '#1C120C',
                    border: '1.5px solid #3A2312',
                    borderRadius: '4px',
                    boxShadow: '2px 2px 0px #3A2312',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </UX4GCard>
      </div>
    </div>
  );
};
