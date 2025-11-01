import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './components/layout/AppLayout';
import { ChatPage } from './components/chat/ChatPage';
import { DocumentsPage } from './components/documents/DocumentsPage';
import { SettingsPage } from './components/settings/SettingsPage';
import { MetricsPage } from './components/metrics/MetricsPage';
import { LabGuidePage } from './components/lab/LabGuidePage';
import { QAPage } from './components/qa/QAPage';
import { FeedbackPage } from './components/feedback/FeedbackPage';

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<ChatPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="metrics" element={<MetricsPage />} />
            <Route path="lab" element={<LabGuidePage />} />
            <Route path="qa" element={<QAPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
