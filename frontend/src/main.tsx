import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { initializeOpenTelemetry, initializeWebVitals } from './instrumentation';

// Initialize OpenTelemetry BEFORE rendering the app
// This ensures all fetch/XHR calls and user interactions are instrumented
initializeOpenTelemetry();
initializeWebVitals();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
