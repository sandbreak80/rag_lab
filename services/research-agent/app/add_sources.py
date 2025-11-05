#!/usr/bin/env python3
"""
Add new RSS/blog sources to research agent database
Run this once to initialize new sources
"""
import sys
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/app')

from database import Database

# Initialize database
db = Database('/data/research_agent.db')

# New sources to add
NEW_SOURCES = [
    {
        'name': 'TechCrunch AI',
        'type': 'techcrunch',
        'url': 'https://techcrunch.com/category/artificial-intelligence/',
        'enabled': True,
        'config': None
    },
    {
        'name': 'VentureBeat AI',
        'type': 'venturebeat',
        'url': 'https://venturebeat.com/category/ai/',
        'enabled': True,
        'config': None
    },
    {
        'name': 'The Verge AI',
        'type': 'theverge',
        'url': 'https://www.theverge.com/ai-artificial-intelligence',
        'enabled': True,
        'config': None
    },
    {
        'name': 'OpenAI Blog',
        'type': 'openai_blog',
        'url': 'https://openai.com/blog/',
        'enabled': True,
        'config': None
    }
]

print("🤖 Adding new sources to research agent...")
print()

for source in NEW_SOURCES:
    try:
        # Check if source already exists
        existing = db.get_all_sources()
        exists = any(s['name'] == source['name'] for s in existing)
        
        if exists:
            print(f"⏭️  {source['name']} - Already exists, skipping")
        else:
            source_id = db.create_source(
                name=source['name'],
                source_type=source['type'],
                url=source['url'],
                enabled=source['enabled'],
                config=source['config']
            )
            print(f"✅ {source['name']} - Added (ID: {source_id})")
    except Exception as e:
        print(f"❌ {source['name']} - Error: {e}")

print()
print("✅ Source initialization complete!")
print()
print("📊 Current sources:")
all_sources = db.get_all_sources()
for s in all_sources:
    status = "✅" if s['enabled'] else "⏸️ "
    print(f"  {status} #{s['id']}: {s['name']} ({s['type']})")

