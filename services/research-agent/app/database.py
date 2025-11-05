"""
Database models and management for Research Agent
Tracks sources, fetch history, and discovered items
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', '/data/research_agent.db')

class Database:
    """Database manager for research agent"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                last_fetched TIMESTAMP,
                total_items_fetched INTEGER DEFAULT 0,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Fetch history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fetch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER REFERENCES sources(id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                items_discovered INTEGER DEFAULT 0,
                items_ingested INTEGER DEFAULT 0,
                items_failed INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                error_message TEXT,
                duration_seconds REAL
            )
        ''')

        # Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER REFERENCES sources(id),
                external_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                authors TEXT,
                abstract TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ingested_at TIMESTAMP,
                status TEXT DEFAULT 'discovered',
                content_hash TEXT,
                metadata TEXT,
                error_message TEXT
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_discovered ON items(discovered_at DESC)')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    # ============================================================================
    # SOURCES
    # ============================================================================

    def create_source(self, name: str, source_type: str, url: str, config: Dict = None, enabled: bool = True) -> int:
        """Create a new source"""
        conn = self.get_connection()
        cursor = conn.cursor()

        config_json = json.dumps(config) if config else None

        cursor.execute('''
            INSERT INTO sources (name, type, url, enabled, config)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, source_type, url, enabled, config_json))

        source_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Created source: {name} (ID: {source_id})")
        return source_id

    def get_source(self, source_id: int) -> Optional[Dict]:
        """Get source by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sources WHERE id = ?', (source_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_source_by_name(self, name: str) -> Optional[Dict]:
        """Get source by name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sources WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_sources(self, enabled_only: bool = False) -> List[Dict]:
        """Get all sources"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if enabled_only:
            cursor.execute('SELECT * FROM sources WHERE enabled = TRUE ORDER BY name')
        else:
            cursor.execute('SELECT * FROM sources ORDER BY name')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_source(self, source_id: int, **kwargs):
        """Update source fields"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key == 'config' and isinstance(value, dict):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(source_id)

        query = f"UPDATE sources SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        logger.info(f"Updated source ID {source_id}")

    def delete_source(self, source_id: int):
        """Delete a source and its history"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM items WHERE source_id = ?', (source_id,))
        cursor.execute('DELETE FROM fetch_history WHERE source_id = ?', (source_id,))
        cursor.execute('DELETE FROM sources WHERE id = ?', (source_id,))

        conn.commit()
        conn.close()

        logger.info(f"Deleted source ID {source_id}")

    # ============================================================================
    # FETCH HISTORY
    # ============================================================================

    def create_fetch_record(self, source_id: int, items_discovered: int, items_ingested: int,
                           items_failed: int, status: str, duration_seconds: float,
                           error_message: str = None) -> int:
        """Create a fetch history record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO fetch_history
            (source_id, items_discovered, items_ingested, items_failed, status, duration_seconds, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (source_id, items_discovered, items_ingested, items_failed, status, duration_seconds, error_message))

        record_id = cursor.lastrowid

        # Update source last_fetched and total count
        cursor.execute('''
            UPDATE sources
            SET last_fetched = CURRENT_TIMESTAMP,
                total_items_fetched = total_items_fetched + ?
            WHERE id = ?
        ''', (items_ingested, source_id))

        conn.commit()
        conn.close()

        return record_id

    def get_fetch_history(self, source_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get fetch history, optionally filtered by source"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if source_id:
            cursor.execute('''
                SELECT fh.*, s.name as source_name
                FROM fetch_history fh
                JOIN sources s ON fh.source_id = s.id
                WHERE fh.source_id = ?
                ORDER BY fh.timestamp DESC
                LIMIT ?
            ''', (source_id, limit))
        else:
            cursor.execute('''
                SELECT fh.*, s.name as source_name
                FROM fetch_history fh
                JOIN sources s ON fh.source_id = s.id
                ORDER BY fh.timestamp DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ============================================================================
    # ITEMS
    # ============================================================================

    def create_item(self, source_id: int, external_id: str, title: str, url: str,
                   authors: str = None, abstract: str = None, metadata: Dict = None) -> Optional[int]:
        """Create a new item"""
        conn = self.get_connection()
        cursor = conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        try:
            cursor.execute('''
                INSERT INTO items (source_id, external_id, title, url, authors, abstract, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (source_id, external_id, title, url, authors, abstract, metadata_json))

            item_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return item_id
        except sqlite3.IntegrityError:
            # Item already exists (duplicate external_id)
            conn.close()
            return None

    def find_item_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Find item by external_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM items WHERE external_id = ?', (external_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_items(self, source_id: Optional[int] = None, status: Optional[str] = None,
                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get items with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM items WHERE 1=1'
        params = []

        if source_id:
            query += ' AND source_id = ?'
            params.append(source_id)

        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY discovered_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_item_status(self, item_id: int, status: str, error_message: str = None):
        """Update item status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if status == 'ingested':
            cursor.execute('''
                UPDATE items
                SET status = ?, ingested_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            ''', (status, error_message, item_id))
        else:
            cursor.execute('''
                UPDATE items
                SET status = ?, error_message = ?
                WHERE id = ?
            ''', (status, error_message, item_id))

        conn.commit()
        conn.close()

    # ============================================================================
    # STATS
    # ============================================================================

    def get_stats(self) -> Dict:
        """Get overall statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total items by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM items
            GROUP BY status
        ''')
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        # Items in last 24h
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM items
            WHERE discovered_at >= datetime('now', '-1 day')
        ''')
        items_last_24h = cursor.fetchone()['count']

        # Active sources
        cursor.execute('SELECT COUNT(*) as count FROM sources WHERE enabled = TRUE')
        active_sources = cursor.fetchone()['count']

        # Last fetch
        cursor.execute('''
            SELECT MAX(timestamp) as last_fetch
            FROM fetch_history
        ''')
        last_fetch = cursor.fetchone()['last_fetch']

        # Success rate
        cursor.execute('''
            SELECT
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                COUNT(*) as total_count
            FROM fetch_history
            WHERE timestamp >= datetime('now', '-7 days')
        ''')
        fetch_stats = cursor.fetchone()
        success_rate = 0
        if fetch_stats['total_count'] > 0:
            success_rate = (fetch_stats['success_count'] / fetch_stats['total_count']) * 100

        conn.close()

        return {
            'total_items': sum(status_counts.values()),
            'items_discovered': status_counts.get('discovered', 0),
            'items_ingested': status_counts.get('ingested', 0),
            'items_failed': status_counts.get('failed', 0),
            'items_last_24h': items_last_24h,
            'active_sources': active_sources,
            'last_fetch': last_fetch,
            'success_rate': round(success_rate, 1)
        }

# Global database instance
db = Database()

