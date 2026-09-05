import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, Flame, Clock, CheckCircle2, RefreshCw } from 'lucide-react';

export const UX4GBadge = ({ children, variant = 'primary', size = 'md', className = '', style = {}, ...props }) => {
  const getBadgeClass = () => {
    switch (variant) {
      case 'low':
      case 'success':
        return 'ux4g-badge-low';
      case 'medium':
      case 'warning':
        return 'ux4g-badge-medium';
      case 'high':
        return 'ux4g-badge-high';
      case 'critical':
      case 'danger':
        return 'ux4g-badge-critical';
      case 'primary':
      default:
        return 'ux4g-badge-primary';
    }
  };

  const paddingStyle = size === 'sm' ? { padding: '2px 8px', fontSize: '0.7rem' } : { padding: '4px 10px', fontSize: '0.75rem' };

  return (
    <span className={`ux4g-badge ${getBadgeClass()} ${className}`} style={{ ...paddingStyle, ...style }} {...props}>
      {children}
    </span>
  );
};

export const RiskBadge = ({ level = 'Low', showIcon = true, size = 'md' }) => {
  const normalized = String(level).toLowerCase();

  let badgeClass = 'ux4g-badge-low';
  let Icon = ShieldCheck;
  let label = 'Low Risk';

  if (normalized.includes('critical')) {
    badgeClass = 'ux4g-badge-critical';
    Icon = Flame;
    label = 'Critical Risk';
  } else if (normalized.includes('high')) {
    badgeClass = 'ux4g-badge-high';
    Icon = AlertCircle;
    label = 'High Risk';
  } else if (normalized.includes('medium') || normalized.includes('mod')) {
    badgeClass = 'ux4g-badge-medium';
    Icon = AlertTriangle;
    label = 'Medium Risk';
  }

  const paddingStyle = size === 'sm' ? { padding: '2px 8px', fontSize: '0.7rem' } : { padding: '4px 12px', fontSize: '0.78rem' };

  return (
    <span className={`ux4g-badge ${badgeClass}`} style={paddingStyle}>
      {showIcon && <Icon size={size === 'sm' ? 12 : 14} />}
      <span>{label}</span>
    </span>
  );
};

export const StatusBadge = ({ status = 'PENDING', size = 'md' }) => {
  const norm = String(status).toUpperCase();

  let bg = '#F1F5F9';
  let color = '#475569';
  let border = '#CBD5E1';
  let Icon = Clock;
  let text = status;

  switch (norm) {
    case 'PENDING':
      bg = 'var(--ux4g-warning-bg)';
      color = 'var(--ux4g-warning-text)';
      border = 'var(--ux4g-warning-border)';
      Icon = Clock;
      text = 'Pending';
      break;
    case 'ASSIGNED':
      bg = 'var(--ux4g-violet-50)';
      color = 'var(--ux4g-violet-700)';
      border = 'var(--ux4g-violet-200)';
      Icon = RefreshCw;
      text = 'Assigned';
      break;
    case 'ACKNOWLEDGED':
      bg = '#F0FDF4';
      color = '#15803D';
      border = '#BBF7D0';
      Icon = CheckCircle2;
      text = 'Acknowledged';
      break;
    case 'IN_PROGRESS':
    case 'IN PROGRESS':
      bg = '#EFF6FF';
      color = '#1D4ED8';
      border = '#BFDBFE';
      Icon = RefreshCw;
      text = 'In Progress';
      break;
    case 'COMPLETED':
      bg = 'var(--ux4g-success-bg)';
      color = 'var(--ux4g-success-text)';
      border = 'var(--ux4g-success-border)';
      Icon = CheckCircle2;
      text = 'Completed';
      break;
    case 'ESCALATED':
      bg = 'var(--ux4g-danger-bg)';
      color = 'var(--ux4g-danger-text)';
      border = 'var(--ux4g-danger-border)';
      Icon = AlertCircle;
      text = 'Escalated';
      break;
    default:
      break;
  }

  const paddingStyle = size === 'sm' ? { padding: '2px 8px', fontSize: '0.7rem' } : { padding: '4px 10px', fontSize: '0.75rem' };

  return (
    <span
      className="ux4g-badge"
      style={{
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        ...paddingStyle,
      }}
    >
      <Icon size={size === 'sm' ? 12 : 13} />
      <span>{text}</span>
    </span>
  );
};
