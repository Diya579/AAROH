import React, { useState } from 'react';
import { PhoneCall, AlertTriangle, Sparkles, Bell, Shield, CheckCheck, Clock, ArrowUpRight } from 'lucide-react';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { useAuth } from '../../context/AuthContext';
import { UX4GOffcanvas } from './UX4GOffcanvas';
import { UX4GButton } from './UX4GButton';
import { 
  getNotificationsForRole, 
  getRoleNotificationMeta, 
  normalizeNotificationRole 
} from '../../services/notificationService';

export const GlobalOffcanvasDrawer = () => {
  const { offcanvasOpen, offcanvasContent, closeOffcanvas } = useThemeAccessibility();
  const { currentUser } = useAuth();
  const [readIds, setReadIds] = useState(new Set());

  if (!offcanvasContent) return null;

  // Resolve target role strictly based on authenticated persona
  const targetRole = normalizeNotificationRole(currentUser?.role || offcanvasContent?.role || 'VICTIM');
  const roleNotifications = getNotificationsForRole(targetRole);
  const roleMeta = getRoleNotificationMeta(targetRole);

  const toggleMarkAllRead = () => {
    if (readIds.size === roleNotifications.length) {
      setReadIds(new Set());
    } else {
      setReadIds(new Set(roleNotifications.map(n => n.id)));
    }
  };

  const getPriorityStyle = (priority, isRead) => {
    if (isRead) {
      return {
        bg: '#F8FAFC',
        border: '#E2E8F0',
        titleColor: '#64748B',
        badgeClass: 'ux4g-badge',
        badgeBg: '#E2E8F0',
        badgeText: '#475569',
      };
    }
    switch (priority) {
      case 'critical':
        return {
          bg: '#FEF2F2',
          border: '#FECACA',
          titleColor: '#991B1B',
          badgeClass: 'ux4g-badge ux4g-badge-critical',
          badgeBg: 'var(--ux4g-danger-bg)',
          badgeText: 'var(--ux4g-danger-text)',
        };
      case 'warning':
        return {
          bg: 'var(--ux4g-warning-bg)',
          border: 'var(--ux4g-warning-border)',
          titleColor: 'var(--ux4g-warning-text)',
          badgeClass: 'ux4g-badge ux4g-badge-medium',
          badgeBg: 'var(--ux4g-warning-bg)',
          badgeText: 'var(--ux4g-warning-text)',
        };
      case 'success':
        return {
          bg: 'var(--ux4g-success-bg)',
          border: 'var(--ux4g-success-border)',
          titleColor: 'var(--ux4g-success-text)',
          badgeClass: 'ux4g-badge ux4g-badge-low',
          badgeBg: 'var(--ux4g-success-bg)',
          badgeText: 'var(--ux4g-success-text)',
        };
      case 'info':
      case 'primary':
        return {
          bg: 'var(--ux4g-violet-100)',
          border: 'var(--ux4g-violet-300)',
          titleColor: 'var(--ux4g-violet-900)',
          badgeClass: 'ux4g-badge ux4g-badge-low',
          badgeBg: 'var(--ux4g-violet-100)',
          badgeText: 'var(--ux4g-violet-900)',
        };
      default:
        return {
          bg: 'var(--ux4g-surface)',
          border: 'var(--ux4g-border)',
          titleColor: 'var(--ux4g-text-primary)',
          badgeClass: 'ux4g-badge',
          badgeBg: 'var(--ux4g-bg-subtle)',
          badgeText: 'var(--ux4g-text-secondary)',
        };
    }
  };

  return (
    <UX4GOffcanvas
      isOpen={offcanvasOpen}
      onClose={closeOffcanvas}
      title={offcanvasContent.title || 'System Drawer'}
      subtitle={offcanvasContent.subtitle}
      width="440px"
    >
      {/* Emergency Crisis View */}
      {offcanvasContent.type === 'emergency' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              padding: '16px',
              backgroundColor: 'var(--ux4g-danger-bg)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--ux4g-danger-border)',
              color: 'var(--ux4g-danger-text)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, marginBottom: '6px' }}>
              <AlertTriangle size={18} />
              <span>Immediate Life-Safety Escalation</span>
            </div>
            <p style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
              If you or a beneficiary is facing acute physical danger or life-threatening distress, engage the national emergency dispatch immediately.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', border: '1.5px solid var(--ux4g-violet-300)', backgroundColor: 'var(--ux4g-violet-50)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', fontSize: '0.95rem' }}>
                  Tele-MANAS (Mental Health)
                </span>
                <span className="ux4g-badge ux4g-badge-low">24x7 Toll Free</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                Ministry of Health & Family Welfare national tele-mental health programme. Free clinical counselling across 22 languages.
              </p>
              <a href="tel:14416" style={{ textDecoration: 'none' }}>
                <UX4GButton variant="primary" size="sm" icon={PhoneCall} style={{ width: '100%' }}>
                  Call 14416 (Direct Dial)
                </UX4GButton>
              </a>
            </div>

            <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)', backgroundColor: '#FFFFFF' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 700, color: 'var(--ux4g-violet-950)', fontSize: '0.95rem' }}>
                  Emergency Police / Medical Dispatch
                </span>
                <span className="ux4g-badge ux4g-badge-critical">SOS 112</span>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '12px' }}>
                All-India unified emergency helpline for prompt police protection, ambulance, and emergency response.
              </p>
              <a href="tel:112" style={{ textDecoration: 'none' }}>
                <UX4GButton variant="danger" size="sm" icon={PhoneCall} style={{ width: '100%' }}>
                  Call 112 Dispatch
                </UX4GButton>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Role-Specific Notifications Drawer View */}
      {offcanvasContent.type === 'notifications' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Official Scope Indicator */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '10px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Shield size={14} color={roleMeta.color} />
                <span style={{ fontSize: '0.825rem', fontWeight: 700, color: '#0F172A' }}>
                  {roleMeta.badge}
                </span>
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748B', marginTop: '2px' }}>
                {roleMeta.scope}
              </div>
            </div>

            <button
              type="button"
              onClick={toggleMarkAllRead}
              className="ux4g-focus-glow"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '0.74rem',
                color: 'var(--ux4g-violet-700)',
                fontWeight: 600,
                padding: '4px 6px',
                borderRadius: '4px',
              }}
            >
              <CheckCheck size={14} />
              <span>{readIds.size === roleNotifications.length ? 'Unmark All' : 'Mark All Read'}</span>
            </button>
          </div>

          {/* Rendered Notification Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {roleNotifications.map((item) => {
              const isRead = readIds.has(item.id) || item.read;
              const style = getPriorityStyle(item.priority, isRead);

              return (
                <div
                  key={item.id}
                  style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: style.bg,
                    border: `1px solid ${style.border}`,
                    transition: 'var(--transition-fast)',
                    opacity: isRead ? 0.78 : 1,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span
                          style={{
                            fontSize: '0.66rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            backgroundColor: style.badgeBg,
                            color: style.badgeText,
                            letterSpacing: '0.02em',
                          }}
                        >
                          {item.category}
                        </span>
                        {!isRead && (
                          <span
                            style={{
                              width: '6px',
                              height: '6px',
                              borderRadius: '50%',
                              backgroundColor: 'var(--ux4g-violet-700)',
                              display: 'inline-block',
                            }}
                          />
                        )}
                      </div>
                      <strong style={{ fontSize: '0.88rem', color: style.titleColor, lineHeight: 1.3 }}>
                        {item.title}
                      </strong>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.72rem', color: 'var(--ux4g-text-muted)', flexShrink: 0 }}>
                      <Clock size={11} />
                      <span>{item.time}</span>
                    </div>
                  </div>

                  <p style={{ fontSize: '0.8rem', color: isRead ? '#64748B' : 'var(--ux4g-text-secondary)', lineHeight: 1.45, margin: 0 }}>
                    {item.message}
                  </p>

                  {item.actionLabel && (
                    <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: `1px dashed ${style.border}` }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: 'var(--ux4g-violet-700)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          cursor: 'pointer',
                        }}
                      >
                        <span>{item.actionLabel}</span>
                        <ArrowUpRight size={12} />
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ textAlign: 'center', paddingTop: '8px', fontSize: '0.7rem', color: '#94A3B8' }}>
            National Mental Health Monitoring System • DPDP 2023 Compliant
          </div>
        </div>
      )}

      {/* Showcase View */}
      {offcanvasContent.type === 'showcase' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div style={{ padding: '18px', backgroundColor: 'var(--ux4g-violet-50)', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-violet-200)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--ux4g-violet-700)', fontWeight: 700, marginBottom: '6px' }}>
              <Sparkles size={18} />
              <span>Frictionless Flyout Glide Active</span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--ux4g-text-secondary)', lineHeight: '1.6' }}>
              This offcanvas component slides smoothly using cubic-bezier motion physics (`cubic-bezier(0.16, 1, 0.3, 1)`), providing instant access to auxiliary tools, notifications, and emergency support.
            </p>
          </div>

          <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--ux4g-border)' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--ux4g-violet-950)', marginBottom: '8px' }}>
              Universal Motion Toggle Test
            </h4>
            <p style={{ fontSize: '0.825rem', color: 'var(--ux4g-text-secondary)', marginBottom: '14px' }}>
              When the Universal Motion Toggle is activated in the top accessibility header, this drawer and all cards immediately disable all sliding and lifting animations.
            </p>
            <UX4GButton variant="secondary" size="sm" onClick={closeOffcanvas}>
              Dismiss Drawer
            </UX4GButton>
          </div>
        </div>
      )}
    </UX4GOffcanvas>
  );
};
