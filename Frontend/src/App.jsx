import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { UX4GHeader } from './components/common/UX4GHeader';
import { UX4GFooter } from './components/common/UX4GFooter';
import { GlobalOffcanvasDrawer } from './components/common/GlobalOffcanvasDrawer';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ScrollToTop } from './components/common/ScrollToTop';

// Pages
import { HomePage } from './pages/HomePage';
import { SignInPage } from './pages/SignInPage';
import { VictimDashboard } from './pages/dashboards/VictimDashboard';
import { CounsellorDashboard } from './pages/dashboards/CounsellorDashboard';
import { DistrictDashboard } from './pages/dashboards/DistrictDashboard';
import { StateDashboard } from './pages/dashboards/StateDashboard';
import { NationalDashboard } from './pages/dashboards/NationalDashboard';
import { AdminDashboard } from './pages/dashboards/AdminDashboard';
import { UnauthorizedPage, NotFoundPage } from './pages/dashboards/UnauthorizedPage';

export const App = () => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Universal Route Scroll Reset */}
      <ScrollToTop />

      {/* Global Accessible UX4G Header with Universal Motion Toggle */}
      <UX4GHeader />

      {/* Main Routed Content Viewport */}
      <div style={{ flex: 1 }}>
        <Routes>
          {/* Public Home & Sign In (Strictly NO Sign-Up) */}
          <Route path="/" element={<HomePage />} />
          <Route path="/signin" element={<SignInPage />} />

          {/* Protected Role-Based Dashboards (RBAC removed for Counsellor, District, State, National, Admin) */}
          <Route
            path="/dashboard/victim"
            element={
              <ProtectedRoute allowedRoles={['VICTIM', 'COUNSELLOR', 'DISTRICT', 'STATE', 'NATIONAL', 'ADMIN']}>
                <VictimDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/counsellor"
            element={
              <ProtectedRoute allowedRoles={['COUNSELLOR', 'DISTRICT', 'STATE', 'NATIONAL', 'ADMIN']}>
                <CounsellorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/district"
            element={
              <ProtectedRoute allowedRoles={['DISTRICT', 'STATE', 'NATIONAL', 'ADMIN', 'COUNSELLOR']}>
                <DistrictDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/state"
            element={
              <ProtectedRoute allowedRoles={['STATE', 'NATIONAL', 'ADMIN', 'DISTRICT', 'COUNSELLOR']}>
                <StateDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/national"
            element={
              <ProtectedRoute allowedRoles={['NATIONAL', 'ADMIN', 'STATE', 'DISTRICT', 'COUNSELLOR']}>
                <NationalDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN', 'NATIONAL', 'STATE', 'DISTRICT', 'COUNSELLOR']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          {/* Fallbacks */}
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>

      {/* Global Frictionless Offcanvas Flyout Drawer */}
      <GlobalOffcanvasDrawer />

      {/* UX4G GIGW 3.0 Standard Footer */}
      <UX4GFooter />
    </div>
  );
};

export default App;
