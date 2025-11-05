"""
Rate Limiter - Redis-based distributed rate limiting
Fast Track Phase 7 - Week 9 Day 4-5

Features:
- Sliding window algorithm
- Per-user and per-IP quotas
- Distributed (multi-instance safe)
- Configurable limits
- Retry-After headers
- Rate limit metrics
"""

import redis
import time
from typing import Optional, Tuple
from functools import wraps
from flask import request, jsonify
import os

class RateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize rate limiter

        Args:
            redis_url: Redis connection URL (default: redis://redis:6379/0)
        """
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')

        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        # Default rate limits (requests per minute)
        self.limits = {
            'authenticated': int(os.getenv('RATE_LIMIT_AUTH', 100)),      # 100 req/min for authenticated users
            'anonymous': int(os.getenv('RATE_LIMIT_ANON', 10)),           # 10 req/min for anonymous users
            'admin': int(os.getenv('RATE_LIMIT_ADMIN', 1000)),            # 1000 req/min for admins
        }

        # Window size in seconds
        self.window_size = 60  # 1 minute

        print(f"✅ Rate Limiter initialized (Auth: {self.limits['authenticated']}/min, "
              f"Anon: {self.limits['anonymous']}/min)")

    def _get_key(self, identifier: str, endpoint: str = None) -> str:
        """Generate Redis key for rate limiting"""
        if endpoint:
            return f"rate_limit:{identifier}:{endpoint}"
        return f"rate_limit:{identifier}"

    def _get_identifier(self) -> Tuple[str, str]:
        """
        Get identifier for current request

        Returns:
            (identifier, type) - type is 'user', 'ip', or 'admin'
        """
        # Try to get user from JWT token (if available)
        user_id = request.headers.get('X-User-ID')  # Set by auth middleware
        is_admin = request.headers.get('X-User-Admin') == 'true'

        if user_id:
            if is_admin:
                return f"user:{user_id}", 'admin'
            return f"user:{user_id}", 'user'

        # Fallback to IP address
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            # Get first IP if multiple (proxy chain)
            ip = ip.split(',')[0].strip()
        return f"ip:{ip}", 'ip'

    def check_rate_limit(self, identifier: str = None, limit_type: str = None) -> dict:
        """
        Check if request is within rate limit

        Args:
            identifier: Custom identifier (if None, auto-detect from request)
            limit_type: 'authenticated', 'anonymous', or 'admin'

        Returns:
            {
                'allowed': bool,
                'remaining': int,
                'reset_at': int (unix timestamp),
                'retry_after': int (seconds, only if not allowed)
            }
        """
        # Auto-detect identifier and type
        if identifier is None:
            identifier, detected_type = self._get_identifier()

            if limit_type is None:
                if detected_type == 'admin':
                    limit_type = 'admin'
                elif detected_type == 'user':
                    limit_type = 'authenticated'
                else:
                    limit_type = 'anonymous'
        else:
            if limit_type is None:
                limit_type = 'authenticated'

        # Get limit
        max_requests = self.limits.get(limit_type, self.limits['anonymous'])

        # Sliding window key
        key = self._get_key(identifier)
        current_time = int(time.time())
        window_start = current_time - self.window_size

        try:
            # Remove old entries outside the window
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            request_count = self.redis_client.zcard(key)

            # Check if limit exceeded
            if request_count >= max_requests:
                # Get oldest request time to calculate retry_after
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = int(oldest[0][1])
                    retry_after = max(1, oldest_time + self.window_size - current_time)
                else:
                    retry_after = self.window_size

                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_at': window_start + self.window_size,
                    'retry_after': retry_after,
                    'limit': max_requests,
                    'identifier': identifier
                }

            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})

            # Set expiry on key (cleanup)
            self.redis_client.expire(key, self.window_size + 10)

            # Calculate remaining
            remaining = max_requests - (request_count + 1)

            return {
                'allowed': True,
                'remaining': remaining,
                'reset_at': current_time + self.window_size,
                'limit': max_requests,
                'identifier': identifier
            }

        except redis.RedisError as e:
            # If Redis fails, allow request (fail open)
            print(f"⚠️ Redis error in rate limiter: {e}")
            return {
                'allowed': True,
                'remaining': max_requests,
                'reset_at': current_time + self.window_size,
                'limit': max_requests,
                'error': str(e)
            }

    def reset(self, identifier: str):
        """Reset rate limit for an identifier (admin use)"""
        key = self._get_key(identifier)
        self.redis_client.delete(key)

    def get_stats(self, identifier: str = None) -> dict:
        """Get rate limit statistics"""
        if identifier is None:
            identifier, _ = self._get_identifier()

        key = self._get_key(identifier)
        current_time = int(time.time())
        window_start = current_time - self.window_size

        try:
            # Clean old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Get count
            request_count = self.redis_client.zcard(key)

            return {
                'identifier': identifier,
                'requests_in_window': request_count,
                'window_size': self.window_size,
                'limits': self.limits
            }
        except redis.RedisError as e:
            return {
                'identifier': identifier,
                'error': str(e)
            }


def rate_limit(limit_type: str = None):
    """
    Decorator for Flask routes to apply rate limiting

    Usage:
        @app.route('/api/endpoint')
        @rate_limit('authenticated')
        def endpoint():
            return {'data': 'response'}

    Args:
        limit_type: 'authenticated', 'anonymous', or 'admin' (auto-detect if None)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter from app config
            limiter = getattr(decorated_function, '_rate_limiter', None)

            if limiter is None:
                # No rate limiter configured, allow request
                return f(*args, **kwargs)

            # Check rate limit
            result = limiter.check_rate_limit(limit_type=limit_type)

            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(result['limit']),
                'X-RateLimit-Remaining': str(result['remaining']),
                'X-RateLimit-Reset': str(result['reset_at'])
            }

            if not result['allowed']:
                # Rate limit exceeded
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Please try again in {result['retry_after']} seconds.",
                    'retry_after': result['retry_after'],
                    'limit': result['limit']
                })
                response.status_code = 429
                response.headers.update(response_headers)
                response.headers['Retry-After'] = str(result['retry_after'])

                return response

            # Execute the route
            response = f(*args, **kwargs)

            # Add rate limit headers to response
            if hasattr(response, 'headers'):
                response.headers.update(response_headers)

            return response

        return decorated_function
    return decorator


# Flask extension integration
class FlaskRateLimiter:
    """
    Flask extension for rate limiting

    Usage:
        app = Flask(__name__)
        limiter = FlaskRateLimiter(app)
    """

    def __init__(self, app=None, redis_url=None):
        self.limiter = None
        if app is not None:
            self.init_app(app, redis_url)

    def init_app(self, app, redis_url=None):
        """Initialize Flask app with rate limiter"""
        self.limiter = RateLimiter(redis_url)
        app.config['RATE_LIMITER'] = self.limiter

        # Store limiter reference for decorator
        rate_limit._rate_limiter = self.limiter

        # Add before_request handler to set user info in headers
        @app.before_request
        def add_user_info():
            """Extract user info from JWT and add to headers for rate limiter"""
            try:
                from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
                from flask import g

                # Try to verify JWT (optional)
                try:
                    verify_jwt_in_request(optional=True)
                    identity = get_jwt_identity()

                    if identity:
                        # Add user info to request headers for rate limiter
                        request.environ['HTTP_X_USER_ID'] = str(identity.get('user_id', ''))
                        request.environ['HTTP_X_USER_ADMIN'] = str(identity.get('is_admin', False)).lower()

                        # Store in g for easy access
                        g.user_id = identity.get('user_id')
                        g.is_admin = identity.get('is_admin', False)
                except:
                    pass
            except ImportError:
                # JWT not available, skip
                pass

    def check(self, identifier: str = None, limit_type: str = None) -> dict:
        """Check rate limit"""
        if self.limiter:
            return self.limiter.check_rate_limit(identifier, limit_type)
        return {'allowed': True, 'remaining': 999, 'reset_at': 0}


# Example usage
if __name__ == "__main__":
    print("🧪 Testing Rate Limiter")
    print("=" * 60)

    # Initialize
    limiter = RateLimiter('redis://localhost:6379/0')

    # Test rate limiting
    test_user = "test_user_123"

    print(f"\nTesting rate limit for: {test_user}")
    print(f"Limit: {limiter.limits['authenticated']} requests/minute")

    # Simulate requests
    for i in range(12):
        result = limiter.check_rate_limit(test_user, 'authenticated')

        if result['allowed']:
            print(f"✅ Request {i+1}: Allowed (Remaining: {result['remaining']})")
        else:
            print(f"❌ Request {i+1}: BLOCKED (Retry after {result['retry_after']}s)")

    # Get stats
    stats = limiter.get_stats(test_user)
    print(f"\n📊 Stats: {stats}")

    # Reset
    limiter.reset(test_user)
    print(f"\n🔄 Reset rate limit for {test_user}")

    print("\n✅ Rate Limiter test complete!")

