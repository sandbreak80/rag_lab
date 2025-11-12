import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { initializeOpenTelemetry, initializeWebVitals } from './instrumentation';

// Initialize OpenTelemetry BEFORE rendering the app
// Wrap in try-catch to prevent blocking app if OTel fails
try {
  initializeOpenTelemetry();
  initializeWebVitals();
} catch (error) {
  console.warn('⚠️ OpenTelemetry initialization failed (non-blocking):', error);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
