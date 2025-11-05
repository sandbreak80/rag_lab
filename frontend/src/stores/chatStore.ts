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

  // FIX: Detect if last message was a user question without a response (orphaned by page refresh)
  let initialMessages = savedMessages;
  if (savedMessages.length > 0) {
    const lastMessage = savedMessages[savedMessages.length - 1];

    // If last message is from user and was sent recently (< 2 minutes ago)
    const twoMinutesAgo = Date.now() - (2 * 60 * 1000);
    const messageTime = new Date(lastMessage.timestamp).getTime();

    if (lastMessage.role === 'user' && messageTime > twoMinutesAgo) {
      // Add a system message explaining what happened
      const systemMessage: ChatMessage = {
        id: `system-${Date.now()}`,
        role: 'assistant',
        content: '⚠️ **Request Interrupted**\n\nThe page was refreshed before the response completed. Please resend your question.',
        timestamp: new Date(),
      };
      initialMessages = [...savedMessages, systemMessage];
      // Save the updated messages
      setTimeout(() => saveToLocalStorage('chat_messages', initialMessages), 0);
    }
  }

  return {
    messages: initialMessages,
    isLoading: false,  // Always start with isLoading=false on page load

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
  };
});

