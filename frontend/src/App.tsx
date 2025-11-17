import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './components/layout/AppLayout';
import { ChatPage } from './components/chat/ChatPage';
import { DocumentsPage } from './components/documents/DocumentsPage';
import { SettingsPage } from './components/settings/SettingsPage';
import { MetricsPage } from './components/metrics/MetricsPage';
import { MonitoringPage } from './components/monitoring/MonitoringPage';
import { LabGuidePage } from './components/lab/LabGuidePage';
import { LearningHubPage } from './components/learning/LearningHubPage';
import { FeedbackPage } from './components/feedback/FeedbackPage';
import { PromptLoggingPage } from './components/logging/PromptLoggingPage';
import { ResearchAgentPage } from './components/research/ResearchAgentPage';
import { PromptsPage } from './pages/PromptsPage';
import { ABTestingPage } from './pages/ABTestingPage';
import { GPUMonitoringPage } from './pages/GPUMonitoringPage';
import { VersionFooter } from './components/layout/VersionFooter';
import { ToastProvider } from './components/ui/toast';
import { AuthProvider } from './contexts/AuthContext';
import { LoginPage } from './components/auth/LoginPage';
import { RegisterPage } from './components/auth/RegisterPage';
import { UserProfile } from './components/auth/UserProfile';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          {/* Hidden indicator that RUM is initialized */}
          <div data-testid="rum-ready" style={{ display: 'none' }} aria-hidden="true" />
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Routes */}
              <Route path="/profile" element={
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              } />

              {/* App Routes (Chat accessible to guests, others optional) */}
              <Route path="/" element={<AppLayout />}>
                <Route index element={<ChatPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="research" element={<ResearchAgentPage />} />
                <Route path="prompts" element={<PromptsPage />} />
                <Route path="ab-testing" element={<ABTestingPage />} />
                <Route path="gpu" element={<GPUMonitoringPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="metrics" element={<MetricsPage />} />
                <Route path="monitoring" element={<MonitoringPage />} />
                <Route path="logging" element={<PromptLoggingPage />} />
                <Route path="lab" element={<LabGuidePage />} />
                <Route path="learning" element={<LearningHubPage />} />
                <Route path="feedback" element={<FeedbackPage />} />
              </Route>
            </Routes>
            <VersionFooter />
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
