#!/usr/bin/env python3
"""
Simple Chatbot with Conversation History
Demonstrates multi-turn conversations with Ollama
"""

import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434"

class Chatbot:
    """Simple chatbot with conversation memory"""
    
    def __init__(self, model: str = "llama3.1:8b", system_prompt: str = None):
        self.model = model
        self.messages = []
        
        # Add system message if provided
        if system_prompt:
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })
    
    def chat(self, user_message: str) -> str:
        """Send a message and get a response"""
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Get response from Ollama
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": self.model,
                "messages": self.messages,
                "stream": False
            }
        )
        
        result = response.json()
        assistant_message = result['message']['content']
        
        # Add assistant response to history
        self.messages.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    def clear_history(self):
        """Clear conversation history (keep system message)"""
        system_messages = [m for m in self.messages if m['role'] == 'system']
        self.messages = system_messages
    
    def get_history(self) -> list:
        """Get conversation history"""
        return self.messages

def interactive_chat():
    """Run an interactive chat session"""
    print("🤖 Interactive Chatbot")
    print("=" * 60)
    print()
    
    # Choose model
    model = input("Choose model (default: llama3.1:8b): ").strip()
    if not model:
        model = "llama3.1:8b"
    
    # Optional system prompt
    print("\nEnter system prompt (or press Enter for default):")
    system_prompt = input("> ").strip()
    if not system_prompt:
        system_prompt = "You are a helpful, friendly AI assistant."
    
    # Initialize chatbot
    bot = Chatbot(model=model, system_prompt=system_prompt)
    
    print()
    print(f"✅ Chatbot initialized with {model}")
    print(f"💭 System prompt: {system_prompt}")
    print()
    print("Commands:")
    print("  /clear  - Clear conversation history")
    print("  /history - Show conversation history")
    print("  /quit   - Exit")
    print()
    print("=" * 60)
    print()
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input == "/quit":
                print("👋 Goodbye!")
                break
            
            elif user_input == "/clear":
                bot.clear_history()
                print("🗑️  Conversation history cleared")
                continue
            
            elif user_input == "/history":
                print("\n📜 Conversation History:")
                for msg in bot.get_history():
                    role = msg['role'].capitalize()
                    content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"  {role}: {content}")
                print()
                continue
            
            # Get response
            print("🤔 Thinking...", end="\r")
            response = bot.chat(user_input)
            print(f"Bot: {response}")
            print()
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_conversation():
    """Demo: Pre-scripted conversation"""
    print("🎬 Demo Conversation")
    print("=" * 60)
    print()
    
    # Create a coding assistant
    bot = Chatbot(
        model="llama3.2:3b",
        system_prompt="You are a helpful coding assistant. Keep responses concise and practical."
    )
    
    conversation = [
        "What is a REST API?",
        "Can you show me a simple Python example?",
        "How would I add error handling to that?",
        "Thanks! What about authentication?"
    ]
    
    for user_msg in conversation:
        print(f"👤 User: {user_msg}")
        response = bot.chat(user_msg)
        print(f"🤖 Bot: {response}")
        print()
        print("-" * 60)
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_conversation()
    else:
        interactive_chat()

