"""
MCP Server for Markdown RAG
Exposes tools for semantic search, RAG, and vault navigation
"""
import json
import sys
from typing import Any, Dict, List
import requests

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
from mcp.server.stdio import stdio_server

from search import VaultSearcher
import config


# Initialize server and searcher
app = Server("markdown-rag-mcp")
searcher = VaultSearcher()


def generate_with_ollama(prompt: str, context: str = "") -> str:
    """Generate text using Ollama"""
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.CHAT_MODEL,
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error generating response: {e}"


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="search_notes",
            description="Semantic search across markdown vault. Supports filtering by tags and folders.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 10)",
                        "default": 10
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (optional)"
                    },
                    "folder": {
                        "type": "string",
                        "description": "Filter by folder path (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_vault",
            description="Ask a question and get an AI-generated answer based on vault content (RAG).",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to ask"
                    },
                    "context_size": {
                        "type": "integer",
                        "description": "Amount of context to use (default 5 chunks)",
                        "default": 5
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="find_similar",
            description="Find notes similar to a given note based on content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the reference note"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of similar notes (default 10)",
                        "default": 10
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="find_linked",
            description="Find notes that link to or from a given note (wikilinks).",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the note file (e.g., 'my-note.md')"
                    }
                },
                "required": ["file_name"]
            }
        ),
        Tool(
            name="summarize_topic",
            description="Summarize all notes related to a specific topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to summarize"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: filter by tags"
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="get_vault_stats",
            description="Get statistics about the indexed vault.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "search_notes":
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        tags = arguments.get("tags", [])
        folder = arguments.get("folder")
        
        results = searcher.search(
            query=query,
            limit=limit,
            tags=tags if tags else None,
            folder=folder
        )
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No results found for '{query}'"
            )]
        
        # Format results
        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. **{result['metadata']['title']}**\n"
            output += f"   File: {result['metadata']['file_name']}\n"
            output += f"   Score: {result['score']:.3f}\n"
            if 'tags' in result['metadata']:
                output += f"   Tags: {', '.join(result['metadata']['tags'])}\n"
            output += f"\n   {result['content'][:300]}...\n\n"
            output += "---\n\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "ask_vault":
        question = arguments["question"]
        context_size = arguments.get("context_size", 5)
        
        # Generate context from vault
        context = searcher.generate_rag_context(question, max_length=context_size * 1000)
        
        if not context:
            return [TextContent(
                type="text",
                text="I couldn't find relevant information in the vault to answer this question."
            )]
        
        # Generate answer
        prompt = f"Based on the following notes from my vault, please answer this question: {question}\n\nPlease provide a clear, concise answer based only on the information provided."
        
        answer = generate_with_ollama(prompt, context)
        
        output = f"**Question:** {question}\n\n"
        output += f"**Answer:**\n{answer}\n\n"
        output += "---\n\n"
        output += f"*Based on {context.count('##')} note(s) from your vault*"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "find_similar":
        file_path = arguments["file_path"]
        limit = arguments.get("limit", 10)
        
        results = searcher.find_similar(file_path, limit=limit)
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No similar notes found for '{file_path}'"
            )]
        
        output = f"Notes similar to '{file_path}':\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. **{result['metadata']['title']}** (score: {result['score']:.3f})\n"
            output += f"   File: {result['metadata']['file_name']}\n"
            output += f"   {result['content'][:200]}...\n\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "find_linked":
        file_name = arguments["file_name"]
        
        links = searcher.find_linked(file_name)
        
        output = f"**Links for {file_name}:**\n\n"
        
        if links['links_to']:
            output += f"**Links to ({len(links['links_to'])}):**\n"
            for link in links['links_to']:
                output += f"  - [[{link}]]\n"
            output += "\n"
        else:
            output += "**Links to:** None\n\n"
        
        if links['linked_from']:
            output += f"**Linked from ({len(links['linked_from'])}):**\n"
            for link in links['linked_from']:
                output += f"  - {link}\n"
        else:
            output += "**Linked from:** None\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "summarize_topic":
        topic = arguments["topic"]
        tags = arguments.get("tags", [])
        
        # Search for relevant notes
        results = searcher.search(
            query=topic,
            limit=20,
            tags=tags if tags else None
        )
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No notes found for topic '{topic}'"
            )]
        
        # Build context from results
        context = "Here are notes about " + topic + ":\n\n"
        for result in results[:10]:  # Limit to top 10
            context += f"## {result['metadata']['title']}\n"
            context += f"{result['content']}\n\n"
        
        # Generate summary
        prompt = f"Please provide a comprehensive summary of the main ideas, concepts, and themes from these notes about {topic}. Organize the summary logically and highlight key points."
        
        summary = generate_with_ollama(prompt, context)
        
        output = f"**Summary of: {topic}**\n\n"
        output += summary + "\n\n"
        output += "---\n\n"
        output += f"*Based on {len(results)} note(s)*"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "get_vault_stats":
        if not searcher.collection:
            return [TextContent(
                type="text",
                text="Vault not indexed yet."
            )]
        
        # Get basic stats
        count = searcher.collection.count()
        
        # Get unique files
        all_data = searcher.collection.get(include=['metadatas'])
        unique_files = set()
        all_tags = set()
        
        if all_data['metadatas']:
            for metadata in all_data['metadatas']:
                unique_files.add(metadata.get('file_name', ''))
                if 'tags' in metadata:
                    try:
                        tags = json.loads(metadata['tags'])
                        all_tags.update(tags)
                    except:
                        pass
        
        output = "**Vault Statistics:**\n\n"
        output += f"- Vault path: `{config.VAULT_PATH}`\n"
        output += f"- Total chunks indexed: {count}\n"
        output += f"- Unique files: {len(unique_files)}\n"
        output += f"- Unique tags: {len(all_tags)}\n"
        output += f"- Embedding model: {config.EMBEDDING_MODEL}\n"
        output += f"- Chat model: {config.CHAT_MODEL}\n"
        
        if all_tags:
            output += f"\n**Popular tags:**\n"
            for tag in sorted(list(all_tags))[:20]:
                output += f"  - #{tag}\n"
        
        return [TextContent(type="text", text=output)]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



