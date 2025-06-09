import time
from prometheus_client import Counter, Histogram, Gauge
from django.conf import settings

# Request metrics
REQUEST_COUNT = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Database metrics
DB_QUERY_COUNT = Counter(
    'django_db_queries_total',
    'Total database queries',
    ['view']
)

DB_QUERY_LATENCY = Histogram(
    'django_db_query_duration_seconds',
    'Database query latency',
    ['view']
)

# Cache metrics
CACHE_HITS = Counter(
    'django_cache_hits_total',
    'Total cache hits',
    ['cache_name']
)

CACHE_MISSES = Counter(
    'django_cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

# Active users
ACTIVE_USERS = Gauge(
    'django_active_users',
    'Number of active users'
)

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Record request metrics
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path
        ).observe(duration)
        
        return response

class DatabaseMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.db import connection
        
        # Get initial query count
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate metrics
        final_queries = len(connection.queries)
        query_count = final_queries - initial_queries
        duration = time.time() - start_time
        
        # Record metrics
        DB_QUERY_COUNT.labels(view=request.resolver_match.view_name).inc(query_count)
        DB_QUERY_LATENCY.labels(view=request.resolver_match.view_name).observe(duration)
        
        return response

class CacheMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.core.cache import cache
        
        # Get initial cache stats
        initial_hits = getattr(cache, '_cache_hits', 0)
        initial_misses = getattr(cache, '_cache_misses', 0)
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate metrics
        final_hits = getattr(cache, '_cache_hits', 0)
        final_misses = getattr(cache, '_cache_misses', 0)
        
        # Record metrics
        CACHE_HITS.labels(cache_name='default').inc(final_hits - initial_hits)
        CACHE_MISSES.labels(cache_name='default').inc(final_misses - initial_misses)
        
        return response 