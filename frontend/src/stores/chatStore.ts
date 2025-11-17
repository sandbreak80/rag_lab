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
  // Load initial messages from localStorage
  const savedMessages = loadFromLocalStorage<ChatMessage[]>('chat_messages', []);
  const savedFilters = loadFromLocalStorage<MetadataFilters>('metadata_filters', {});
  const savedPendingRequests = loadFromLocalStorage<string[]>('pending_request_ids', []);

  // Use saved messages directly - polling will handle responses
  const filteredMessages = savedMessages;

  // Clean up pending requests that already have responses
  const messagesWithRequestIds = new Set(
    filteredMessages
      .filter(msg => msg.metadata?.request_id)
      .map(msg => msg.metadata!.request_id!)
  );
  const activePendingRequests = savedPendingRequests.filter(
    reqId => !messagesWithRequestIds.has(reqId)
  );
  if (activePendingRequests.length !== savedPendingRequests.length) {
    saveToLocalStorage('pending_request_ids', activePendingRequests);
  }

  return {
    messages: filteredMessages, // Use filtered messages (polling will add responses)
    isLoading: false,  // Always start with isLoading=false on page load
    metadataFilters: savedFilters,
    pendingRequestIds: activePendingRequests, // Track pending requests for polling

    addMessage: (message) => {
      const messages = [...get().messages, message];
      set({ messages });
      saveToLocalStorage('chat_messages', messages);
    },

    setLoading: (isLoading) => {
      set({ isLoading });
      // Don't persist isLoading state - always reset to false on page refresh
      // This prevents stuck "Thinking..." state after refresh
    },

    clearMessages: () => {
      set({ messages: [] });
      saveToLocalStorage('chat_messages', []);
    },

    setMetadataFilters: (metadataFilters) => {
      set({ metadataFilters });
      saveToLocalStorage('metadata_filters', metadataFilters);
    },

    addPendingRequest: (requestId: string) => {
      const current = get().pendingRequestIds;
      if (!current.includes(requestId)) {
        const updated = [...current, requestId];
        set({ pendingRequestIds: updated });
        saveToLocalStorage('pending_request_ids', updated);
      }
    },

    removePendingRequest: (requestId: string) => {
      const current = get().pendingRequestIds;
      const updated = current.filter(id => id !== requestId);
      if (updated.length !== current.length) {
        set({ pendingRequestIds: updated });
        saveToLocalStorage('pending_request_ids', updated);
      }
    },

    getPendingRequests: () => {
      return get().pendingRequestIds;
    },
  };
});

