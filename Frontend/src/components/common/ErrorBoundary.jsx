import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('AAROH Application Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          backgroundColor: '#F9FAFB',
          color: '#111827',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <div style={{
            maxWidth: '560px',
            width: '100%',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '2px solid #EF4444',
            padding: '24px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.08)',
            textAlign: 'center'
          }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#1E3A8A', marginBottom: '8px' }}>
              Portal Display Notice
            </h2>
            <p style={{ color: '#4B5563', marginBottom: '16px', fontSize: '0.95rem' }}>
              An error occurred during page rendering.
            </p>
            {this.state.error && (
              <pre style={{
                textAlign: 'left',
                backgroundColor: '#F3F4F6',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '0.8rem',
                color: '#DC2626',
                overflowX: 'auto',
                marginBottom: '16px'
              }}>
                {this.state.error.toString()}
              </pre>
            )}
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.href = '/';
              }}
              style={{
                backgroundColor: '#1E3A8A',
                color: '#ffffff',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '6px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Return to Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
