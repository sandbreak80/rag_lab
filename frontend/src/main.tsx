import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Feature-flagged OTel initialization
const ENABLE_OTEL = import.meta.env.VITE_ENABLE_OTEL === 'true';

// Runtime error capture for debugging
window.addEventListener("error", (ev) => {
  console.error("[WINDOW_ERROR]", ev.message, ev.filename, ev.lineno, ev.colno);
});
window.addEventListener("unhandledrejection", (ev) => {
  console.error("[UNHANDLED_REJECTION]", ev.reason);
});

// Initialize OTel asynchronously if enabled
if (ENABLE_OTEL) {
  import("./instrumentation").then(({ initializeOpenTelemetry }) => {
    try {
      initializeOpenTelemetry();
      console.log("✅ OTel initialized");
    } catch (e) {
      console.warn("[OTEL_INIT_FAILED]", e);
    }
  }).catch(e => {
    console.warn("[OTEL_IMPORT_FAILED]", e);
  });
}

// Initialize Web Vitals (non-blocking)
import("./instrumentation").then(({ initializeWebVitals }) => {
  try {
    initializeWebVitals?.();
  } catch (e) {
    console.warn("[WEBVITALS_INIT_FAILED]", e);
  }
}).catch(() => {
  // Silently ignore if web vitals not available
});

// Normal React mount MUST always run
const root = document.getElementById("root");
if (root) {
  root.setAttribute("data-testid", "root-mounted");
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
} else {
  console.error("[MOUNT_FAILED] Root element not found");
}
