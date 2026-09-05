import React from 'react';
import { PhoneCall, AlertTriangle, Sparkles } from 'lucide-react';
import { useThemeAccessibility } from '../../context/ThemeAccessibilityContext';
import { UX4GOffcanvas } from './UX4GOffcanvas';
import { UX4GButton } from './UX4GButton';

export const GlobalOffcanvasDrawer = () => {
  const { offcanvasOpen, offcanvasContent, closeOffcanvas } = useThemeAccessibility();

  if (!offcanvasContent) return null;

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

      {/* Notifications Drawer View */}
      {offcanvasContent.type === 'notifications' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--ux4g-violet-50)', border: '1px solid var(--ux4g-violet-200)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-violet-950)' }}>New Check-In Received</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>10m ago</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>
              Beneficiary Meera Sharma completed a 90s voice check-in via South Delhi channel.
            </p>
          </div>

          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--ux4g-danger-bg)', border: '1px solid var(--ux4g-danger-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-danger-text)' }}>SLA Urgency Alert</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-danger-text)' }}>45m ago</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>
              Case #8402 high-distress flag requires nodal officer review within 2 hours.
            </p>
          </div>

          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', backgroundColor: '#FFFFFF', border: '1px solid var(--ux4g-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <strong style={{ fontSize: '0.88rem', color: 'var(--ux4g-text-primary)' }}>System Audit Recorded</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--ux4g-text-muted)' }}>2h ago</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--ux4g-text-secondary)' }}>
              DPDP 2023 verification stamp confirmed by Central Infrastructure.
            </p>
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
