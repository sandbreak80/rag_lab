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
    console.log('🧹 Cleared old localStorage chat data');
  } catch (e) {
    // Ignore errors
  }
  
  // Load pending requests from sessionStorage (survives page refresh)
  // sessionStorage is cleared when tab closes, perfect for this use case
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
  
  // Messages are in-memory only (cleared on refresh)
  // Pending requests persist in sessionStorage (polling retrieves responses)
  // Redis on backend is the source of truth
  
  return {
    messages: [], // Start fresh - no localStorage
    isLoading: false,
    metadataFilters: {},
    pendingRequestIds: savedPendingRequests, // Restore from sessionStorage

    addMessage: (message) => {
      const messages = [...get().messages, message];
      set({ messages });
      // NO localStorage - messages are in-memory only
    },

    setLoading: (isLoading) => {
      set({ isLoading });
      // Don't persist isLoading state - always reset to false on page refresh
      // This prevents stuck "Thinking..." state after refresh
    },

    clearMessages: () => {
      set({ messages: [], pendingRequestIds: [] });
      // NO localStorage - just clear in-memory state
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

