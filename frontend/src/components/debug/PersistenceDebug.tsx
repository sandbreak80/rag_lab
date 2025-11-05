/**
 * Persistence Debug Component
 *
 * Shows localStorage contents and state to help debug persistence issues
 */

import React, { useState, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { useConfigStore } from '../../stores/configStore';

export function PersistenceDebug() {
  const [localStorageData, setLocalStorageData] = useState<Record<string, any>>({});
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const currentPreset = useConfigStore((state) => state.currentPreset);

  useEffect(() => {
    // Read all relevant localStorage keys
    const data: Record<string, any> = {};

    try {
      const chatMessages = localStorage.getItem('chat_messages');
      data.chat_messages = chatMessages ? JSON.parse(chatMessages) : null;
    } catch (e) {
      data.chat_messages = 'ERROR: ' + e;
    }

    try {
      const draft = localStorage.getItem('chat_draft_message');
      data.chat_draft_message = draft || '(empty)';
    } catch (e) {
      data.chat_draft_message = 'ERROR: ' + e;
    }

    try {
      const config = localStorage.getItem('rag_config');
      data.rag_config = config ? JSON.parse(config) : null;
    } catch (e) {
      data.rag_config = 'ERROR: ' + e;
    }

    setLocalStorageData(data);
  }, [messages, currentPreset]); // Re-check when state changes

  return (
    <div className="fixed bottom-4 right-4 max-w-md p-4 bg-card border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto text-xs">
      <div className="font-bold text-sm mb-2">🔍 Persistence Debug</div>

      <div className="space-y-3">
        {/* Chat Messages */}
        <div>
          <div className="font-semibold text-primary">Chat Messages:</div>
          <div className="pl-2">
            <div>• Store: {messages.length} messages</div>
            <div>• localStorage: {Array.isArray(localStorageData.chat_messages) ? localStorageData.chat_messages.length : 0} messages</div>
            <div>• isLoading: {isLoading ? '🔄 YES' : '✅ NO'}</div>
          </div>
        </div>

        {/* Draft Message */}
        <div>
          <div className="font-semibold text-primary">Draft Message:</div>
          <div className="pl-2">
            <div>• localStorage: {localStorageData.chat_draft_message === '(empty)' ? '(empty)' : `"${localStorageData.chat_draft_message}"`}</div>
          </div>
        </div>

        {/* Current Preset */}
        <div>
          <div className="font-semibold text-primary">Current Preset:</div>
          <div className="pl-2">
            <div>• Store: {currentPreset || '(none)'}</div>
            <div>• localStorage: {localStorageData.rag_config?.currentPreset || '(none)'}</div>
          </div>
        </div>

        {/* localStorage Health */}
        <div>
          <div className="font-semibold text-primary">localStorage Health:</div>
          <div className="pl-2">
            <div>• Available: {typeof localStorage !== 'undefined' ? '✅ YES' : '❌ NO'}</div>
            <div>• Keys: {Object.keys(localStorage).length}</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="pt-2 border-t border-border space-y-1">
          <button
            onClick={() => {
              console.log('💾 localStorage contents:', {
                chat_messages: localStorageData.chat_messages,
                chat_draft_message: localStorageData.chat_draft_message,
                rag_config: localStorageData.rag_config,
              });
            }}
            className="w-full px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Log to Console
          </button>

          <button
            onClick={() => {
              if (confirm('Clear all localStorage? This will reset everything.')) {
                localStorage.clear();
                window.location.reload();
              }
            }}
            className="w-full px-2 py-1 text-xs bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
          >
            Clear All & Reload
          </button>
        </div>
      </div>
    </div>
  );
}

