import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export const UX4GInput = ({
  label,
  id,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  helperText,
  required = false,
  disabled = false,
  leadingIcon: LeadingIcon = null,
  allowShowPassword = false,
  className = '',
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const effectiveType = allowShowPassword ? (showPassword ? 'text' : 'password') : type;

  return (
    <div className={`ux4g-form-group ${className}`} style={{ marginBottom: '18px' }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            display: 'block',
            marginBottom: '6px',
            fontSize: '0.9rem',
            fontWeight: 600,
            color: 'var(--ux4g-text-primary)',
          }}
        >
          {label} {required && <span style={{ color: 'var(--ux4g-danger)', marginLeft: '2px' }}>*</span>}
        </label>
      )}

      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {LeadingIcon && (
          <div
            style={{
              position: 'absolute',
              left: '14px',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
              color: 'var(--ux4g-text-muted)',
            }}
          >
            <LeadingIcon size={18} />
          </div>
        )}

        <input
          id={inputId}
          type={effectiveType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className="ux4g-focus-glow"
          style={{
            width: '100%',
            padding: '10px 14px',
            paddingLeft: LeadingIcon ? '42px' : '14px',
            paddingRight: allowShowPassword ? '44px' : '14px',
            fontSize: '0.95rem',
            borderRadius: 'var(--radius-md)',
            border: `1.5px solid ${error ? 'var(--ux4g-danger)' : 'var(--ux4g-border)'}`,
            backgroundColor: disabled ? 'var(--ux4g-bg-subtle)' : 'var(--ux4g-surface)',
            color: 'var(--ux4g-text-primary)',
            transition: 'var(--transition-fast)',
          }}
          {...props}
        />

        {allowShowPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            style={{
              position: 'absolute',
              right: '12px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: 'var(--ux4g-text-muted)',
              padding: '4px',
            }}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>

      {error && (
        <p
          role="alert"
          style={{
            marginTop: '6px',
            fontSize: '0.825rem',
            color: 'var(--ux4g-danger)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          {error}
        </p>
      )}

      {!error && helperText && (
        <p
          style={{
            marginTop: '5px',
            fontSize: '0.8rem',
            color: 'var(--ux4g-text-muted)',
          }}
        >
          {helperText}
        </p>
      )}
    </div>
  );
};
