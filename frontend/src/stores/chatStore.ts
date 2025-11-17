import { create } from 'zustand';
import { ChatMessage } from '../types/chat';
import { MetadataFilters } from '../types/config';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

interface ChatStore {
  messages: ChatMessage[];
  isLoading: boolean;
  metadataFilters: MetadataFilters;
  pendingRequestIds: string[]; // Track pending requests for polling

  // Actions
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
  setMetadataFilters: (filters: MetadataFilters) => void;
  addPendingRequest: (requestId: string) => void;
  removePendingRequest: (requestId: string) => void;
  getPendingRequests: () => string[];
}

export const useChatStore = create<ChatStore>((set, get) => {
  // CLEAR old localStorage chat data (one-time cleanup)
  try {
    localStorage.removeItem('chat_messages');
    localStorage.removeItem('metadata_filters');
    localStorage.removeItem('pending_request_ids');
  } catch (e) {
    // Ignore errors
  }
  
  // Load messages from sessionStorage (survives page refresh, cleared when tab closes)
  let savedMessages: ChatMessage[] = [];
  try {
    const saved = sessionStorage.getItem('chat_messages');
    if (saved) {
      savedMessages = JSON.parse(saved);
      // Filter out any error messages (no error messages should persist)
      savedMessages = savedMessages.filter((msg) => {
        if (msg.content && typeof msg.content === 'string') {
          const contentLower = msg.content.toLowerCase();
          const isErrorMessage = 
            contentLower.includes('request interrupted') ||
            contentLower.includes('request timed out') ||
            contentLower.includes('error occurred') ||
            contentLower.includes('❌') ||
            contentLower.includes('⏱️');
          return !isErrorMessage;
        }
        return true;
      });
      console.log(`🔄 Restored ${savedMessages.length} message(s) from sessionStorage`);
    }
  } catch (e) {
    console.warn('Failed to load messages from sessionStorage:', e);
  }
  
  // Load pending requests from sessionStorage
  let savedPendingRequests: string[] = [];
  try {
    const saved = sessionStorage.getItem('pending_request_ids');
    if (saved) {
      savedPendingRequests = JSON.parse(saved);
      console.log(`🔄 Restored ${savedPendingRequests.length} pending request(s) from sessionStorage`);
    }
  } catch (e) {
    console.warn('Failed to load pending requests from sessionStorage:', e);
  }
  
  // Use sessionStorage for messages and pending requests
  // Persists during session, cleared when tab closes
  // Redis on backend is the source of truth
  
  return {
    messages: savedMessages, // Restore from sessionStorage
    isLoading: false,
    metadataFilters: {},
    pendingRequestIds: savedPendingRequests,

    addMessage: (message) => {
      const messages = [...get().messages, message];
      set({ messages });
      // Save to sessionStorage (persists during session)
      try {
        sessionStorage.setItem('chat_messages', JSON.stringify(messages));
      } catch (e) {
        console.warn('Failed to save messages to sessionStorage:', e);
      }
    },

    setLoading: (isLoading) => {
      set({ isLoading });
      // Don't persist isLoading state - always reset to false on page refresh
      // This prevents stuck "Thinking..." state after refresh
    },

    clearMessages: () => {
      set({ messages: [], pendingRequestIds: [] });
      // Clear sessionStorage
      try {
        sessionStorage.removeItem('chat_messages');
        sessionStorage.removeItem('pending_request_ids');
      } catch (e) {
        console.warn('Failed to clear sessionStorage:', e);
      }
    },

    setMetadataFilters: (metadataFilters) => {
      set({ metadataFilters });
      // NO localStorage - in-memory only
    },

    addPendingRequest: (requestId: string) => {
      const current = get().pendingRequestIds;
      if (!current.includes(requestId)) {
        const updated = [...current, requestId];
        set({ pendingRequestIds: updated });
        // Save to sessionStorage so polling works after page refresh
        try {
          sessionStorage.setItem('pending_request_ids', JSON.stringify(updated));
        } catch (e) {
          console.warn('Failed to save pending requests to sessionStorage:', e);
        }
      }
    },

    removePendingRequest: (requestId: string) => {
      const current = get().pendingRequestIds;
      const updated = current.filter(id => id !== requestId);
      if (updated.length !== current.length) {
        set({ pendingRequestIds: updated });
        // Update sessionStorage
        try {
          sessionStorage.setItem('pending_request_ids', JSON.stringify(updated));
        } catch (e) {
          console.warn('Failed to update pending requests in sessionStorage:', e);
        }
      }
    },

    getPendingRequests: () => {
      return get().pendingRequestIds;
    },
  };
});

