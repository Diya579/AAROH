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
  style = {},
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'secondary':
        return {
          backgroundColor: 'var(--ux4g-violet-100)',
          color: 'var(--ux4g-violet-950)',
          border: '2px solid #3A2312',
        };
      case 'outline':
        return {
          backgroundColor: 'var(--ux4g-surface)',
          color: 'var(--ux4g-violet-950)',
          border: '2px solid #3A2312',
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
          color: '#FAF4EB',
          border: '2px solid #3A2312',
        };
      case 'primary':
      default:
        return {
          backgroundColor: 'var(--ux4g-violet-700)',
          color: '#FAF4EB',
          border: '2px solid #2B1508',
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          padding: '6px 14px',
          fontSize: '0.84rem',
          borderRadius: '6px',
        };
      case 'lg':
        return {
          padding: '12px 26px',
          fontSize: '0.98rem',
          borderRadius: '8px',
        };
      case 'md':
      default:
        return {
          padding: '9px 20px',
          fontSize: '0.9rem',
          borderRadius: '6px',
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
    fontWeight: 700,
    fontFamily: '"Space Mono", "Courier Prime", monospace',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.65 : 1,
    transition: 'all 0.15s ease',
    boxShadow: variant !== 'ghost' ? '3px 3px 0px #3A2312' : 'none',
    ...style,
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
            width: '15px',
            height: '15px',
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            display: 'inline-block',
            animation: 'spin 0.75s linear infinite',
          }}
          aria-hidden="true"
        />
      )}
      {!isLoading && Icon && iconPosition === 'left' && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
      <span>{children}</span>
      {!isLoading && Icon && iconPosition === 'right' && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </button>
  );
};
