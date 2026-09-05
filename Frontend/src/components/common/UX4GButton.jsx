import React from 'react';

export const UX4GButton = ({
  children,
  variant = 'primary', // 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size = 'md', // 'sm' | 'md' | 'lg'
  isLoading = false,
  disabled = false,
  icon: Icon = null,
  iconPosition = 'left',
  onClick,
  type = 'button',
  className = '',
  ariaLabel,
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'secondary':
        return {
          backgroundColor: 'var(--ux4g-violet-50)',
          color: 'var(--ux4g-violet-700)',
          border: '1px solid var(--ux4g-violet-200)',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--ux4g-violet-700)',
          border: '1.5px solid var(--ux4g-violet-700)',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: 'var(--ux4g-text-secondary)',
          border: '1px solid transparent',
        };
      case 'danger':
        return {
          backgroundColor: 'var(--ux4g-danger)',
          color: '#FFFFFF',
          border: '1px solid var(--ux4g-danger)',
        };
      case 'primary':
      default:
        return {
          backgroundColor: 'var(--ux4g-violet-700)',
          color: '#FFFFFF',
          border: '1px solid var(--ux4g-violet-700)',
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          padding: '6px 14px',
          fontSize: '0.85rem',
          borderRadius: 'var(--radius-sm)',
        };
      case 'lg':
        return {
          padding: '12px 28px',
          fontSize: '1.05rem',
          borderRadius: 'var(--radius-md)',
        };
      case 'md':
      default:
        return {
          padding: '9px 20px',
          fontSize: '0.925rem',
          borderRadius: 'var(--radius-md)',
        };
    }
  };

  const baseStyle = {
    ...getVariantStyles(),
    ...getSizeStyles(),
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontWeight: 600,
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.65 : 1,
    transition: 'var(--transition-fast)',
    boxShadow: variant === 'primary' ? '0 2px 4px rgba(75, 35, 184, 0.15)' : 'none',
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      aria-label={ariaLabel}
      className={`ux4g-focus-glow ${className}`}
      style={baseStyle}
      {...props}
    >
      {isLoading && (
        <span
          style={{
            width: '16px',
            height: '16px',
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            display: 'inline-block',
            animation: 'spin 0.75s linear infinite',
          }}
          aria-hidden="true"
        />
      )}
      {!isLoading && Icon && iconPosition === 'left' && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
      <span>{children}</span>
      {!isLoading && Icon && iconPosition === 'right' && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} />}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
};
