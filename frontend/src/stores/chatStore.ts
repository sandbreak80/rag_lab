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
  // CLEAR any old localStorage data (one-time cleanup)
  try {
    localStorage.removeItem('chat_messages');
    localStorage.removeItem('pending_request_ids');
    localStorage.removeItem('metadata_filters');
    console.log('🧹 Cleared old localStorage (Redis is now source of truth)');
  } catch (e) {
    // Ignore errors - localStorage might not be available
  }
  
  // NO localStorage - messages are in-memory only
  // Redis on backend is the source of truth
  // Polling retrieves responses when ready
  
  return {
    messages: [], // Start fresh - no localStorage
    isLoading: false,
    metadataFilters: {},
    pendingRequestIds: [], // Track in-memory only

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
        // NO localStorage - in-memory only
      }
    },

    removePendingRequest: (requestId: string) => {
      const current = get().pendingRequestIds;
      const updated = current.filter(id => id !== requestId);
      if (updated.length !== current.length) {
        set({ pendingRequestIds: updated });
        // NO localStorage - in-memory only
      }
    },

    getPendingRequests: () => {
      return get().pendingRequestIds;
    },
  };
});

