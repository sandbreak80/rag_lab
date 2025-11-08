"""
Cache Invalidation Subscriber

Subscribes to ingest events (doc_updated, alias_flip) and invalidates
cache entries for affected tenants.

Events:
- doc_updated: {tenant_id, doc_id, timestamp}
- alias_flip: {tenant_id, old_alias, new_alias, timestamp}
- bulk_ingest: {tenant_id, doc_count, timestamp}
"""

import redis
import json
import logging
from typing import Callable, Dict, Any
import threading

logger = logging.getLogger(__name__)


class CacheInvalidationSubscriber:
    """
    Subscribes to ingest events and invalidates cache.
    
    Uses Redis Pub/Sub for real-time invalidation.
    """
    
    def __init__(self, redis_client: redis.Redis, cache):
        self.redis = redis_client
        self.cache = cache
        self.pubsub = self.redis.pubsub()
        self.running = False
        self.thread = None
        
        # Subscribe to channels
        self.pubsub.subscribe('ingest.events')
        
        logger.info("Cache invalidation subscriber initialized")
    
    def start(self):
        """Start listening for events in background thread"""
        if self.running:
            logger.warning("Subscriber already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        logger.info("Cache invalidation subscriber started")
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.pubsub.close()
        logger.info("Cache invalidation subscriber stopped")
    
    def _listen(self):
        """Listen for events (runs in background thread)"""
        try:
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] != 'message':
                    continue
                
                try:
                    event = json.loads(message['data'])
                    self._handle_event(event)
                except Exception as e:
                    logger.error(f"Error handling event: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Subscriber error: {e}", exc_info=True)
    
    def _handle_event(self, event: Dict[str, Any]):
        """Handle individual event"""
        event_type = event.get('type')
        
        if event_type == 'doc_updated':
            self._handle_doc_updated(event)
        elif event_type == 'alias_flip':
            self._handle_alias_flip(event)
        elif event_type == 'bulk_ingest':
            self._handle_bulk_ingest(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def _handle_doc_updated(self, event: Dict[str, Any]):
        """Handle document update event"""
        tenant_id = event.get('tenant_id')
        doc_id = event.get('doc_id')
        
        if not tenant_id:
            logger.error("doc_updated event missing tenant_id")
            return
        
        # Invalidate all caches for this tenant
        # (conservative approach - could be more granular)
        self.cache.invalidate_tenant(tenant_id)
        
        logger.info(f"Invalidated cache for tenant={tenant_id} due to doc_updated: {doc_id}")
    
    def _handle_alias_flip(self, event: Dict[str, Any]):
        """Handle index alias flip event"""
        tenant_id = event.get('tenant_id')
        old_alias = event.get('old_alias')
        new_alias = event.get('new_alias')
        
        if not tenant_id:
            logger.error("alias_flip event missing tenant_id")
            return
        
        # Invalidate all caches (index changed)
        self.cache.invalidate_tenant(tenant_id)
        
        logger.info(
            f"Invalidated cache for tenant={tenant_id} due to alias_flip: "
            f"{old_alias} -> {new_alias}"
        )
    
    def _handle_bulk_ingest(self, event: Dict[str, Any]):
        """Handle bulk ingest event"""
        tenant_id = event.get('tenant_id')
        doc_count = event.get('doc_count', 0)
        
        if not tenant_id:
            logger.error("bulk_ingest event missing tenant_id")
            return
        
        # Invalidate all caches (many docs changed)
        self.cache.invalidate_tenant(tenant_id)
        
        logger.info(
            f"Invalidated cache for tenant={tenant_id} due to bulk_ingest: "
            f"{doc_count} docs"
        )


def publish_ingest_event(redis_client: redis.Redis, event: Dict[str, Any]):
    """Helper to publish ingest events"""
    redis_client.publish('ingest.events', json.dumps(event))
    logger.debug(f"Published event: {event['type']}")

