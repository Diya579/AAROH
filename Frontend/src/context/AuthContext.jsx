import React, { createContext, useContext, useState } from 'react';

// Authorized Demo Personas for Evaluation & Testing
export const DEMO_USERS = {
  victim: {
    userId: 'meera.s@citizen',
    password: 'password123',
    name: 'Meera Sharma',
    role: 'VICTIM',
    roleTitle: 'Citizen / Beneficiary',
    idBadge: 'AAROH-VIC-9821',
    district: 'South Delhi',
    state: 'Delhi NCT',
    avatar: 'MS',
    status: 'Active Monitoring',
    consentGranted: true,
  },
  counsellor: {
    userId: 'dr.rajesh@aaroh.gov.in',
    password: 'password123',
    name: 'Dr. Rajesh Varma',
    role: 'COUNSELLOR',
    roleTitle: 'Lead Clinical Counsellor',
    idBadge: 'GOV-CNS-4402',
    district: 'South Delhi',
    state: 'Delhi NCT',
    avatar: 'RV',
    assignedCaseload: 18,
    slaCompliance: '98.4%',
  },
  district: {
    userId: 'ananya.sen@ias.nic.in',
    password: 'password123',
    name: 'Ananya Sen, IAS',
    role: 'DISTRICT',
    roleTitle: 'District Nodal Officer',
    idBadge: 'GOV-DST-1049',
    district: 'South Delhi',
    state: 'Delhi NCT',
    avatar: 'AS',
    activeInterventions: 42,
  },
  state: {
    userId: 'k.ramanathan@delhi.gov.in',
    password: 'password123',
    name: 'Shri K. Ramanathan',
    role: 'STATE',
    roleTitle: 'State Monitoring Authority',
    idBadge: 'GOV-STA-3320',
    state: 'Delhi NCT',
    avatar: 'KR',
    totalDistricts: 11,
  },
  national: {
    userId: 'p.venkat@socialjustice.gov.in',
    password: 'password123',
    name: 'Dr. P. Venkatachalam',
    role: 'NATIONAL',
    roleTitle: 'National Program Director',
    idBadge: 'GOV-NAT-0081',
    ministry: 'Ministry of Social Justice & Empowerment',
    avatar: 'PV',
    nationalCoverage: '28 States / 8 UTs',
  },
  admin: {
    userId: 'sysadmin@aaroh.nic.in',
    password: 'password123',
    name: 'Central System Admin',
    role: 'ADMIN',
    roleTitle: 'System Authority & Security Auditor',
    idBadge: 'SYS-ADM-0001',
    avatar: 'SA',
    systemStatus: 'Optimal (GIGW 3.0 Verified)',
  },
};

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = sessionStorage.getItem('aaroh_auth_session');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const signIn = async (userId, password) => {
    setIsLoading(true);
    setError('');

    // Simulate backend network latency & authentication verification
    await new Promise(resolve => setTimeout(resolve, 600));

    const matchedKey = Object.keys(DEMO_USERS).find(
      key => DEMO_USERS[key].userId.toLowerCase() === userId.trim().toLowerCase()
    );

    if (matchedKey && password === DEMO_USERS[matchedKey].password) {
      const user = DEMO_USERS[matchedKey];
      setCurrentUser(user);
      sessionStorage.setItem('aaroh_auth_session', JSON.stringify(user));
      setIsLoading(false);
      return { success: true, role: user.role };
    } else {
      // Check if user is recognized by quick identifier format
      if (matchedKey && password !== DEMO_USERS[matchedKey].password) {
        setError('Invalid security credentials. Please verify your password or contact system admin.');
      } else {
        setError('Authorized user identifier not found in the Government AAROH registry.');
      }
      setIsLoading(false);
      return { success: false };
    }
  };

  const signOut = () => {
    setCurrentUser(null);
    sessionStorage.removeItem('aaroh_auth_session');
  };

  const getDashboardPath = (role) => {
    switch (role) {
      case 'VICTIM':
        return '/dashboard/victim';
      case 'COUNSELLOR':
        return '/dashboard/counsellor';
      case 'DISTRICT':
        return '/dashboard/district';
      case 'STATE':
        return '/dashboard/state';
      case 'NATIONAL':
        return '/dashboard/national';
      case 'ADMIN':
        return '/dashboard/admin';
      default:
        return '/signin';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        role: currentUser?.role || null,
        signIn,
        signOut,
        getDashboardPath,
        isLoading,
        error,
        setError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
