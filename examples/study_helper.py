#!/usr/bin/env python3
"""
Flexible Study Helper - works with ANY folder in your vault
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from search import VaultSearcher
import config


def search_folder_content(searcher, query: str, folder_filter: str, limit: int = 5):
    """Search within a specific folder"""
    results = searcher.search(query, limit=50)
    
    # Filter to specified folder
    folder_results = []
    for r in results:
        file_path = r['metadata'].get('file_path', '')
        folder_path = r['metadata'].get('folder', '')
        
        # Check if in target folder (case-insensitive, partial match)
        if folder_filter.lower() in file_path.lower() or \
           folder_filter.lower() in folder_path.lower():
            folder_results.append(r)
            if len(folder_results) >= limit:
                break
    
    return folder_results


def ask_question(searcher, question: str, folder_filter: str = None):
    """
    Ask a question, optionally filtered to a specific folder
    
    Args:
        searcher: VaultSearcher instance
        question: Study question
        folder_filter: Optional folder name/path (e.g., "Green Belt", "Blue Belt", "Projects")
    """
    if folder_filter:
        print(f"\n❓ Question: {question}")
        print(f"📁 Searching in: {folder_filter}")
    else:
        print(f"\n❓ Question: {question}")
        print("📁 Searching: All notes")
    
    # Search with optional folder filter
    if folder_filter:
        results = search_folder_content(searcher, question, folder_filter, limit=5)
    else:
        results = searcher.search(question, limit=5)
    
    if not results:
        print(f"❌ No relevant content found!")
        if folder_filter:
            print(f"   Try without folder filter or check folder name: '{folder_filter}'")
        return None
    
    print(f"✅ Found {len(results)} relevant documents\n")
    
    # Build context
    context_text = f"# Study Materials{' from ' + folder_filter if folder_filter else ''}\n\n"
    sources = []
    
    for i, result in enumerate(results, 1):
        context_text += f"## Source {i}: {result['metadata']['title']}\n"
        context_text += f"Relevance: {result['score']:.3f}\n\n"
        context_text += f"{result['content']}\n\n"
        context_text += "---\n\n"
        
        sources.append({
            "title": result['metadata']['title'],
            "file": result['metadata']['file_name'],
            "folder": result['metadata'].get('folder', 'N/A'),
            "score": result['score']
        })
    
    # Create prompt
    folder_context = f" about {folder_filter}" if folder_filter else ""
    prompt = f"""Based on these study materials{folder_context}, answer this question:

Question: {question}

{context_text}

Instructions:
- Provide clear, concise explanations suitable for studying
- Cite which sources you used (by source number)
- If multiple sources cover the topic, synthesize the information

Answer:"""
    
    print("🤖 Generating answer with Ollama (llama3.2:3b)...")
    
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 400
                }
            },
            timeout=90
        )
        response.raise_for_status()
        answer = response.json()['response']
        
        print("\n" + "="*60)
        print("💡 ANSWER:")
        print("="*60)
        print(answer)
        
        print("\n" + "="*60)
        print("📚 SOURCES:")
        print("="*60)
        for i, src in enumerate(sources, 1):
            print(f"{i}. {src['title']}")
            print(f"   File: {src['file']}")
            print(f"   Folder: {src['folder']}")
            print(f"   Relevance: {src['score']:.3f}")
        
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def list_available_folders(searcher):
    """Show all folders in the vault"""
    all_data = searcher.collection.get()
    
    # Collect unique folders
    folders = {}
    for metadata in all_data['metadatas']:
        file_path = metadata.get('file_path', '')
        
        # Extract folder from path
        if '/' in file_path:
            folder = '/'.join(file_path.split('/')[:-1])
            if folder:
                folders[folder] = folders.get(folder, 0) + 1
    
    # Sort by chunk count
    sorted_folders = sorted(folders.items(), key=lambda x: x[1], reverse=True)
    
    print("\n" + "="*60)
    print("📁 AVAILABLE FOLDERS IN YOUR VAULT")
    print("="*60)
    print(f"Total: {len(sorted_folders)} folders, {searcher.collection.count()} chunks\n")
    
    for folder, count in sorted_folders[:20]:  # Top 20
        percentage = count / searcher.collection.count() * 100
        print(f"  {count:4d} chunks ({percentage:5.1f}%) - {folder}")
    
    if len(sorted_folders) > 20:
        remaining = len(sorted_folders) - 20
        print(f"\n  ... and {remaining} more folders")


def study_session():
    """Interactive study session with folder selection"""
    print("="*60)
    print("🎓 FLEXIBLE STUDY HELPER")
    print("="*60)
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found!")
        return
    
    print(f"\n📚 Vault indexed: {searcher.collection.count()} chunks")
    
    # Show available folders
    list_available_folders(searcher)
    
    print("\n" + "="*60)
    print("Commands:")
    print("  - Type a question to search all notes")
    print("  - Type 'folder:Green Belt <question>' to search specific folder")
    print("  - Type 'folder:' to see available folders")
    print("  - Type 'quit' to exit")
    print("="*60)
    
    current_folder = None
    
    while True:
        try:
            if current_folder:
                prompt_text = f"\n📝 [{current_folder}] Your question: "
            else:
                prompt_text = "\n📝 Your question: "
            
            user_input = input(prompt_text).strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Happy studying!")
                break
            
            # Check for folder command
            if user_input.startswith('folder:'):
                parts = user_input[7:].strip()
                
                if not parts:
                    # Show folders
                    list_available_folders(searcher)
                    current_folder = None
                    continue
                
                # Check if it's setting a folder or asking a question
                if ' ' in parts:
                    # Format: folder:Green Belt <question>
                    folder_name, question = parts.split(' ', 1)
                    ask_question(searcher, question.strip(), folder_name.strip())
                else:
                    # Just setting active folder
                    current_folder = parts
                    print(f"📁 Now searching in: {current_folder}")
                    print("   (Type questions or 'folder:' to clear)")
            else:
                # Regular question
                ask_question(searcher, user_input, current_folder)
            
        except KeyboardInterrupt:
            print("\n\n👋 Happy studying!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command-line mode
        searcher = VaultSearcher()
        
        # Parse arguments
        args = sys.argv[1:]
        folder_filter = None
        
        # Check for --folder flag
        if '--folder' in args:
            idx = args.index('--folder')
            if idx + 1 < len(args):
                folder_filter = args[idx + 1]
                args = args[:idx] + args[idx+2:]
        
        # Check for folder: prefix
        if args and args[0].startswith('folder:'):
            parts = ' '.join(args).split('folder:', 1)[1]
            if ' ' in parts:
                folder_filter, question = parts.split(' ', 1)
                args = [question]
        
        question = ' '.join(args)
        
        if question:
            ask_question(searcher, question, folder_filter)
        else:
            # No question, show folders
            list_available_folders(searcher)
    else:
        # Interactive mode
        study_session()


if __name__ == "__main__":
    main()

