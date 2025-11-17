import { create } from 'zustand';
import { ChatMessage } from '../types/chat';
import { MetadataFilters } from '../types/config';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

interface ChatStore {
  messages: ChatMessage[];
  isLoading: boolean;
  metadataFilters: MetadataFilters;

  // Actions
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
  setMetadataFilters: (filters: MetadataFilters) => void;
}

export const useChatStore = create<ChatStore>((set, get) => {
  // Load initial messages from localStorage
  const savedMessages = loadFromLocalStorage<ChatMessage[]>('chat_messages', []);
  const savedFilters = loadFromLocalStorage<MetadataFilters>('metadata_filters', {});

  // Check for orphaned requests (user message without response) - will be handled by polling
  // No longer showing "Request Interrupted" message - will poll for response instead

  return {
    messages: savedMessages, // Use savedMessages directly (polling will add responses)
    isLoading: false,  // Always start with isLoading=false on page load
    metadataFilters: savedFilters,

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
  };
});

