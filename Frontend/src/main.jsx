import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { AuthProvider } from './context/AuthContext.jsx';
import { ThemeAccessibilityProvider } from './context/ThemeAccessibilityContext.jsx';
import { ErrorBoundary } from './components/common/ErrorBoundary.jsx';

// Import UX4G Design System & Tokens
import './styles/ux4g-theme.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <ThemeAccessibilityProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ThemeAccessibilityProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);

