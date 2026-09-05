import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  FileText, 
  Bell, 
  Menu, 
  Shield, 
  AlertCircle, 
  Clock, 
  CheckSquare, 
  MapPin, 
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';

export const DashboardShell = ({ children, title, subtitle }) => {
  const { currentUser } = useAuth();
  const { openOffcanvas } = useThemeAccessibility();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const location = useLocation();

  // Navigation items customized strictly by role
  const getNavItems = () => {
    switch (currentUser?.role) {
      case 'VICTIM':
        return [
          { id: 'overview', label: 'My Care Space', path: '/dashboard/victim', icon: LayoutDashboard },
          { id: 'checkin', label: 'Check-In & Voice', path: '/dashboard/victim', icon: Activity, badge: 'Active' },
          { id: 'consent', label: 'Consent & Privacy', path: '/dashboard/victim', icon: Shield },
          { id: 'support', label: 'Support & Counsellor', path: '/dashboard/victim', icon: Users },
        ];
      case 'COUNSELLOR':
        return [
          { id: 'overview', label: 'Caseload Overview', path: '/dashboard/counsellor', icon: LayoutDashboard },
          { id: 'cases', label: 'Assigned Cases', path: '/dashboard/counsellor', icon: Users, badge: '18 Active' },
          { id: 'interventions', label: 'Interventions & SLA', path: '/dashboard/counsellor', icon: CheckSquare },
          { id: 'outcomes', label: 'Outcomes & Notes', path: '/dashboard/counsellor', icon: FileText },
        ];
      case 'DISTRICT':
        return [
          { id: 'overview', label: 'District Operations', path: '/dashboard/district', icon: LayoutDashboard },
          { id: 'cases', label: 'District Caseload', path: '/dashboard/district', icon: Users },
          { id: 'escalations', label: 'Escalations & Alerts', path: '/dashboard/district', icon: AlertCircle, badge: '3 Alerts' },
          { id: 'workload', label: 'Counsellor Workload', path: '/dashboard/district', icon: Activity },
        ];
      case 'STATE':
        return [
          { id: 'overview', label: 'State-wide Dashboard', path: '/dashboard/state', icon: LayoutDashboard },
          { id: 'districts', label: 'District Comparison', path: '/dashboard/state', icon: MapPin },
          { id: 'performance', label: 'SLA Performance', path: '/dashboard/state', icon: Clock },
          { id: 'reports', label: 'State Reports', path: '/dashboard/state', icon: FileText },
        ];
      case 'NATIONAL':
        return [
          { id: 'overview', label: 'National Directorate', path: '/dashboard/national', icon: LayoutDashboard },
          { id: 'states', label: 'State Comparison', path: '/dashboard/national', icon: MapPin },
          { id: 'trends', label: 'Aggregated Trends', path: '/dashboard/national', icon: Activity },
          { id: 'coverage', label: 'Monitoring Coverage', path: '/dashboard/national', icon: Shield },
        ];
      case 'ADMIN':
        return [
          { id: 'overview', label: 'System Overview', path: '/dashboard/admin', icon: LayoutDashboard },
          { id: 'rbac', label: 'Role Management', path: '/dashboard/admin', icon: Users },
          { id: 'audit', label: 'Security & Audit Log', path: '/dashboard/admin', icon: Shield, badge: 'Verified' },
          { id: 'health', label: 'System Health & APIs', path: '/dashboard/admin', icon: Activity },
        ];
      default:
        return [];
    }
  };

  const navItems = getNavItems();

  const handleOpenNotifications = () => {
    openOffcanvas({
      title: 'Authorized Notifications',
      subtitle: `${currentUser.name} (${currentUser.role})`,
      type: 'notifications'
    });
  };

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 120px)', backgroundColor: 'var(--ux4g-bg)' }}>
      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <div
          onClick={() => setMobileSidebarOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(26, 14, 61, 0.4)',
            zIndex: 998,
          }}
        />
      )}

      {/* Collapsible Sidebar */}
      <aside
        style={{
          width: sidebarCollapsed ? '76px' : '260px',
          backgroundColor: '#FFFFFF',
          borderRight: '1px solid var(--ux4g-border)',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          zIndex: 999,
          position: 'sticky',
          top: '72px',
          height: 'calc(100vh - 72px)',
          boxShadow: 'var(--elevation-1)',
        }}
        className={`dashboard-sidebar ${mobileSidebarOpen ? 'mobile-open' : ''}`}
      >
        {/* Sidebar Header */}
        <div
          style={{
            padding: '16px',
            borderBottom: '1px solid var(--ux4g-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: sidebarCollapsed ? 'center' : 'space-between',
          }}
        >
          {!sidebarCollapsed && (
            <div>
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--ux4g-violet-700)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Operational Scope
              </span>
              <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--ux4g-violet-950)' }}>
                {currentUser?.roleTitle || currentUser?.role}
              </h4>
            </div>
          )}

          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="ux4g-focus-glow"
            style={{
              background: 'var(--ux4g-bg-subtle)',
              border: '1px solid var(--ux4g-border)',
              borderRadius: 'var(--radius-sm)',
              width: '30px',
              height: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--ux4g-text-secondary)',
            }}
          >
            <Menu size={16} />
          </button>
        </div>

        {/* Sidebar Nav Links */}
        <nav style={{ padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.id}
                to={item.path}
                title={sidebarCollapsed ? item.label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  textDecoration: 'none',
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 700 : 500,
                  backgroundColor: isActive ? 'var(--ux4g-violet-50)' : 'transparent',
                  color: isActive ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-secondary)',
                  border: isActive ? '1px solid var(--ux4g-violet-200)' : '1px solid transparent',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  transition: 'var(--transition-fast)',
                }}
              >
                <Icon size={18} color={isActive ? 'var(--ux4g-violet-700)' : 'currentColor'} />
                {!sidebarCollapsed && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flex: 1 }}>
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="ux4g-badge ux4g-badge-primary" style={{ padding: '2px 6px', fontSize: '0.68rem' }}>
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Card at bottom of sidebar */}
        <div style={{ padding: '14px', borderTop: '1px solid var(--ux4g-border-subtle)', backgroundColor: 'var(--ux4g-bg-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: 'var(--ux4g-violet-700)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.85rem',
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {currentUser?.avatar}
            </div>
            {!sidebarCollapsed && (
              <div style={{ overflow: 'hidden', flex: 1 }}>
                <div style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--ux4g-text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                  {currentUser?.name}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--ux4g-text-muted)' }}>
                  ID: {currentUser?.idBadge}
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main style={{ flex: 1, minWidth: 0, padding: '24px 28px' }}>
        {/* Top Operational Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            {/* Breadcrumb path */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--ux4g-text-muted)', marginBottom: '4px' }}>
              <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>AAROH</Link>
              <ChevronRight size={13} />
              <span>Portals</span>
              <ChevronRight size={13} />
              <span style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600 }}>{currentUser?.role} Dashboard</span>
            </div>

            <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--ux4g-violet-950)', letterSpacing: '-0.015em' }}>
              {title || `${currentUser?.roleTitle || currentUser?.role} Space`}
            </h1>
            {subtitle && (
              <p style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-secondary)', marginTop: '2px' }}>
                {subtitle}
              </p>
            )}
          </div>

          {/* Quick Actions & Role Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                backgroundColor: 'var(--ux4g-violet-50)',
                color: 'var(--ux4g-violet-800)',
                fontSize: '0.78rem',
                fontWeight: 700,
                padding: '6px 14px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--ux4g-violet-200)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Shield size={14} color="var(--ux4g-violet-700)" />
              <span>Role: {currentUser?.role}</span>
            </span>

            <button
              type="button"
              onClick={handleOpenNotifications}
              aria-label="View notifications"
              className="ux4g-focus-glow"
              style={{
                background: '#FFFFFF',
                border: '1px solid var(--ux4g-border)',
                borderRadius: 'var(--radius-md)',
                width: '38px',
                height: '38px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                position: 'relative',
                boxShadow: 'var(--elevation-1)',
              }}
            >
              <Bell size={18} color="var(--ux4g-text-secondary)" />
              <span
                style={{
                  position: 'absolute',
                  top: '6px',
                  right: '6px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--ux4g-danger)',
                }}
              />
            </button>
          </div>
        </div>

        {/* Child Dashboard View */}
        {children}
      </main>

      <style>{`
        @media (max-width: 768px) {
          .dashboard-sidebar {
            position: fixed !important;
            top: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease !important;
          }
          .dashboard-sidebar.mobile-open {
            transform: translateX(0) !important;
          }
        }
      `}</style>
    </div>
  );
};
