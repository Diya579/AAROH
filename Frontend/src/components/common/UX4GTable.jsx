import React from 'react';

export const UX4GTable = ({
  columns = [],
  data = [],
  keyField = 'id',
  onRowClick = null,
  emptyMessage = 'No data available in this table',
  className = '',
}) => {
  return (
    <div
      style={{
        width: '100%',
        overflowX: 'auto',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--ux4g-border)',
        backgroundColor: 'var(--ux4g-surface)',
        boxShadow: 'var(--elevation-1)',
      }}
      className={className}
    >
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          textAlign: 'left',
          fontSize: '0.9rem',
        }}
      >
        <thead>
          <tr style={{ backgroundColor: 'var(--ux4g-bg-subtle)', borderBottom: '1.5px solid var(--ux4g-border)' }}>
            {columns.map((col, idx) => (
              <th
                key={col.key || idx}
                scope="col"
                style={{
                  padding: '14px 18px',
                  fontWeight: 600,
                  color: 'var(--ux4g-violet-950)',
                  fontSize: '0.825rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  width: col.width || 'auto',
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                style={{
                  padding: '32px 18px',
                  textAlign: 'center',
                  color: 'var(--ux4g-text-muted)',
                  fontSize: '0.9rem',
                }}
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIdx) => (
              <tr
                key={row[keyField] || rowIdx}
                onClick={() => onRowClick && onRowClick(row)}
                style={{
                  borderBottom: '1px solid var(--ux4g-border-subtle)',
                  cursor: onRowClick ? 'pointer' : 'default',
                  transition: 'background-color 0.15s ease',
                  backgroundColor: rowIdx % 2 === 0 ? 'var(--ux4g-surface)' : 'rgba(248, 249, 254, 0.6)',
                }}
                onMouseEnter={(e) => {
                  if (onRowClick) e.currentTarget.style.backgroundColor = 'var(--ux4g-violet-50)';
                }}
                onMouseLeave={(e) => {
                  if (onRowClick) {
                    e.currentTarget.style.backgroundColor =
                      rowIdx % 2 === 0 ? 'var(--ux4g-surface)' : 'rgba(248, 249, 254, 0.6)';
                  }
                }}
              >
                {columns.map((col, colIdx) => (
                  <td
                    key={col.key || colIdx}
                    style={{
                      padding: '14px 18px',
                      color: 'var(--ux4g-text-primary)',
                      verticalAlign: 'middle',
                    }}
                  >
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
