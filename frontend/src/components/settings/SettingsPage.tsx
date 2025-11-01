import React from 'react';
import { SettingsPanel } from './SettingsPanel';

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">⚙️ Settings</h1>
        <p className="text-muted-foreground">
          Configure your RAG system to experiment with different features and parameters
        </p>
      </div>
      <SettingsPanel />
    </div>
  );
}
