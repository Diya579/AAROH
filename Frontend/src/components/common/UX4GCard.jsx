import React from 'react';

export const UX4GCard = ({
  children,
  elevation = 1, // 1 | 2 | 3 | 4
  liftOnHover = true,
  hoverElevation = 2,
  padding = '28px',
  borderRadius = '12px',
  className = '',
  style = {},
  onClick,
  ...props
}) => {
  const getElevationShadow = (level) => {
    switch (level) {
      case 2:
        return 'var(--elevation-2)';
      case 3:
        return 'var(--elevation-3)';
      case 4:
        return 'var(--elevation-4)';
      case 1:
      default:
        return 'var(--elevation-1)';
    }
  };

  const [isHovered, setIsHovered] = React.useState(false);

  const cardStyle = {
    backgroundColor: 'var(--ux4g-surface)',
    borderRadius: '6px',
    padding: padding,
    border: '2px solid #3A2312',
    boxShadow: isHovered && liftOnHover ? getElevationShadow(hoverElevation) : getElevationShadow(elevation),
    transform: isHovered && liftOnHover ? 'translate(-2px, -2px)' : 'none',
    borderColor: '#3A2312',
    transition: 'all 0.15s ease',
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  };

  return (
    <div
      className={`ux4g-card ${className}`}
      style={cardStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};
