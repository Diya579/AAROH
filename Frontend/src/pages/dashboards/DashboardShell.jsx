import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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

export const DashboardShell = ({ 
  children, 
  title, 
  subtitle,
  activeTab = 'overview',
  onTabChange,
}) => {
  const { currentUser } = useAuth();
  const { openOffcanvas } = useThemeAccessibility();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Determine operational scope from current URL pathname
  const getScopeRole = () => {
    if (location.pathname.startsWith('/dashboard/victim')) return 'VICTIM';
    if (location.pathname.startsWith('/dashboard/counsellor')) return 'COUNSELLOR';
    if (location.pathname.startsWith('/dashboard/district')) return 'DISTRICT';
    if (location.pathname.startsWith('/dashboard/state')) return 'STATE';
    if (location.pathname.startsWith('/dashboard/national')) return 'NATIONAL';
    if (location.pathname.startsWith('/dashboard/admin')) return 'ADMIN';
    return currentUser?.role || 'VICTIM';
  };

  const scopeRole = getScopeRole();

  const getScopeTitle = (role) => {
    switch (role) {
      case 'VICTIM': return 'Citizen / Beneficiary';
      case 'COUNSELLOR': return 'Clinical Counsellor';
      case 'DISTRICT': return 'District Magistrate & DM Cell';
      case 'STATE': return 'State Nodal Director';
      case 'NATIONAL': return 'National Program Director';
      case 'ADMIN': return 'System Authority';
      default: return role;
    }
  };

  const isOfficial = ['COUNSELLOR', 'DISTRICT', 'STATE', 'NATIONAL', 'ADMIN'].includes(currentUser?.role);

  // Navigation items customized strictly by current dashboard operational scope
  const getNavItems = () => {
    switch (scopeRole) {
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
  const activeNavItem = navItems.find(item => item.id === activeTab) || navItems[0];

  const handleOpenNotifications = () => {
    openOffcanvas({
      title: 'Authorized Notifications',
      subtitle: `${currentUser?.name || 'Authorized Official'} (${currentUser?.role || scopeRole})`,
      type: 'notifications',
      role: currentUser?.role || scopeRole,
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
          minWidth: sidebarCollapsed ? '76px' : '260px',
          flexShrink: 0,
          backgroundColor: 'var(--ux4g-surface)',
          borderRight: '2px solid #3A2312',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
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
                {getScopeTitle(scopeRole)}
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

        {/* Portal Switcher for Officials with RBAC removed */}
        {!sidebarCollapsed && isOfficial && (
          <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--ux4g-border-subtle)', backgroundColor: 'var(--ux4g-bg-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--ux4g-violet-800)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Portal Oversight Switcher
              </span>
              <span className="ux4g-badge ux4g-badge-low" style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
                Unrestricted
              </span>
            </div>
            <select
              value={scopeRole}
              onChange={(e) => {
                const targetPath = {
                  VICTIM: '/dashboard/victim',
                  COUNSELLOR: '/dashboard/counsellor',
                  DISTRICT: '/dashboard/district',
                  STATE: '/dashboard/state',
                  NATIONAL: '/dashboard/national',
                  ADMIN: '/dashboard/admin',
                }[e.target.value];
                if (targetPath) navigate(targetPath);
              }}
              aria-label="Switch portal view"
              className="ux4g-focus-glow"
              style={{
                width: '100%',
                padding: '5px 8px',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid #3A2312',
                fontSize: '0.8rem',
                fontWeight: 700,
                color: 'var(--ux4g-violet-950)',
                backgroundColor: 'var(--ux4g-surface)',
                cursor: 'pointer',
                fontFamily: '"Space Mono", monospace',
              }}
            >
              <option value="VICTIM">🛡️ Citizen / Beneficiary</option>
              <option value="COUNSELLOR">🩺 Counsellor Portal</option>
              <option value="DISTRICT">🏛️ District Portal</option>
              <option value="STATE">🏢 State Portal</option>
              <option value="NATIONAL">🇮🇳 National Portal</option>
              <option value="ADMIN">⚙️ System Authority</option>
            </select>
          </div>
        )}

        {/* Sidebar Nav Links */}
        <nav style={{ padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  if (onTabChange) {
                    onTabChange(item.id);
                  }
                  if (mobileSidebarOpen) {
                    setMobileSidebarOpen(false);
                  }
                }}
                title={sidebarCollapsed ? item.label : undefined}
                className="ux4g-focus-glow"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 700 : 500,
                  backgroundColor: isActive ? 'var(--ux4g-violet-50)' : 'transparent',
                  color: isActive ? 'var(--ux4g-violet-700)' : 'var(--ux4g-text-secondary)',
                  border: isActive ? '1px solid var(--ux4g-violet-200)' : '1px solid transparent',
                  justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                  transition: 'var(--transition-fast)',
                  cursor: 'pointer',
                  width: '100%',
                  textAlign: 'left',
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
              </button>
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
                color: '#FAF4EB',
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
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            {/* Mobile Hamburger Menu Button */}
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Open navigation menu"
              className="dashboard-mobile-toggle ux4g-focus-glow"
              style={{
                display: 'none',
                background: 'var(--ux4g-surface)',
                border: '1.5px solid #3A2312',
                boxShadow: '2px 2px 0px #3A2312',
                borderRadius: 'var(--radius-sm)',
                padding: '8px',
                cursor: 'pointer',
                color: 'var(--ux4g-violet-950)',
                marginTop: '4px',
              }}
            >
              <Menu size={18} />
            </button>

            <div>
              {/* Breadcrumb path */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--ux4g-text-muted)', marginBottom: '4px' }}>
                <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>AAROH</Link>
                <ChevronRight size={13} />
                <span>Portals</span>
                <ChevronRight size={13} />
                <span 
                  onClick={() => onTabChange && onTabChange('overview')}
                  style={{ color: 'var(--ux4g-violet-700)', fontWeight: 600, cursor: onTabChange ? 'pointer' : 'default' }}
                >
                  {currentUser?.role} Dashboard
                </span>
                {activeNavItem && activeNavItem.id !== 'overview' && (
                  <>
                    <ChevronRight size={13} />
                    <span style={{ color: 'var(--ux4g-violet-950)', fontWeight: 700 }}>
                      {activeNavItem.label}
                    </span>
                  </>
                )}
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
                background: 'var(--ux4g-surface)',
                border: '1.5px solid #3A2312',
                boxShadow: '2px 2px 0px #3A2312',
                borderRadius: 'var(--radius-sm)',
                width: '38px',
                height: '38px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                position: 'relative',
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
          .dashboard-mobile-toggle {
            display: inline-flex !important;
          }
          .dashboard-sidebar {
            position: fixed !important;
            top: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            z-index: 1000 !important;
            transform: translateX(-100%);
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
          }
          .dashboard-sidebar.mobile-open {
            transform: translateX(0) !important;
          }
        }
      `}</style>
    </div>
  );
};
