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
          backgroundColor: '#F1F5F9',
          color: '#1E3A8A',
          border: '1px solid #CBD5E1',
        };
      case 'outline':
        return {
          backgroundColor: '#FFFFFF',
          color: '#1E3A8A',
          border: '1px solid #CBD5E1',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: '#475569',
          border: '1px solid transparent',
        };
      case 'danger':
        return {
          backgroundColor: '#DC2626',
          color: '#FFFFFF',
          border: '1px solid #DC2626',
        };
      case 'primary':
      default:
        return {
          backgroundColor: '#1E3A8A',
          color: '#FFFFFF',
          border: '1px solid #1E3A8A',
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
    fontWeight: 600,
    letterSpacing: '-0.01em',
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.65 : 1,
    transition: 'all 0.15s ease',
    boxShadow: variant === 'primary' ? '0 1px 2px rgba(15, 23, 42, 0.08)' : 'none',
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
