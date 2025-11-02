import { create } from 'zustand';
import { ChatMessage } from '../types/chat';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

interface ChatStore {
  messages: ChatMessage[];
  isLoading: boolean;

  // Actions
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => {
  // Load initial messages from localStorage
  const savedMessages = loadFromLocalStorage<ChatMessage[]>('chat_messages', []);

  return {
    messages: savedMessages,
    isLoading: false,

    addMessage: (message) => {
      const messages = [...get().messages, message];
      set({ messages });
      saveToLocalStorage('chat_messages', messages);
    },

    setLoading: (isLoading) => {
      set({ isLoading });
    },

    clearMessages: () => {
      set({ messages: [] });
      saveToLocalStorage('chat_messages', []);
    },
  };
});

