from django.core.cache import cache
from django.db import models
from django_redis import get_redis_connection
from .models import Property
import logging
import math

logger = logging.getLogger(__name__)

def get_redis_cache_metrics():
    """
    Retrieve and analyze Redis cache hit/miss metrics.
    
    Returns:
        dict: Cache metrics including hits, misses, hit ratio, and other stats
    """
    try:
        # Get Redis connection
        redis_conn = get_redis_connection("default")
        
        # Get Redis INFO command output
        info = redis_conn.info()
        
        # Extract cache statistics
        stats = info.get('stats', {})
        
        # Get keyspace hits and misses
        keyspace_hits = stats.get('keyspace_hits', 0)
        keyspace_misses = stats.get('keyspace_misses', 0)
        
        # Calculate total operations and hit ratio
        total_operations = keyspace_hits + keyspace_misses
        hit_ratio = keyspace_hits / total_operations if total_operations > 0 else 0
        
        # Get memory usage
        memory_stats = info.get('memory', {})
        used_memory = memory_stats.get('used_memory', 0)
        used_memory_human = memory_stats.get('used_memory_human', '0B')
        
        # Get key count for our cache pattern
        keys_count = 0
        try:
            # Count keys with our prefix
            pattern = "property_listings:*"
            keys_count = len(redis_conn.keys(pattern))
        except:
            pass
        
        # Get additional cache stats
        cache_stats = {
            'keyspace_hits': keyspace_hits,
            'keyspace_misses': keyspace_misses,
            'total_operations': total_operations,
            'hit_ratio': hit_ratio,
            'hit_ratio_percentage': round(hit_ratio * 100, 2),
            'miss_ratio': 1 - hit_ratio if total_operations > 0 else 0,
            'miss_ratio_percentage': round((1 - hit_ratio) * 100, 2) if total_operations > 0 else 0,
            'used_memory': used_memory,
            'used_memory_human': used_memory_human,
            'cached_keys_count': keys_count,
            'redis_version': info.get('redis_version', 'unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0),
            'uptime_in_days': info.get('uptime_in_days', 0),
        }
        
        # Log the metrics
        logger.info(
            f"📊 Redis Cache Metrics: "
            f"Hits: {keyspace_hits}, "
            f"Misses: {keyspace_misses}, "
            f"Hit Ratio: {cache_stats['hit_ratio_percentage']}%, "
            f"Cached Keys: {keys_count}"
        )
        
        return cache_stats
        
    except Exception as e:
        logger.error(f"❌ Error retrieving Redis cache metrics: {e}")
        return {
            'error': str(e),
            'keyspace_hits': 0,
            'keyspace_misses': 0,
            'total_operations': 0,
            'hit_ratio': 0,
            'hit_ratio_percentage': 0,
            'miss_ratio': 0,
            'miss_ratio_percentage': 0,
            'used_memory': 0,
            'used_memory_human': '0B',
            'cached_keys_count': 0,
            'redis_version': 'unknown',
            'connected_clients': 0,
            'uptime_in_seconds': 0,
            'uptime_in_days': 0,
        }

def get_cache_performance_analysis(metrics):
    """
    Analyze cache performance and provide recommendations.
    
    Args:
        metrics (dict): Cache metrics from get_redis_cache_metrics()
    
    Returns:
        dict: Performance analysis and recommendations
    """
    if not metrics or 'error' in metrics:
        return {'error': 'No metrics available'}
    
    hit_ratio = metrics.get('hit_ratio', 0)
    total_operations = metrics.get('total_operations', 0)
    cached_keys = metrics.get('cached_keys_count', 0)
    
    analysis = {
        'performance_level': '',
        'recommendations': [],
        'status': ''
    }
    
    # Performance level based on hit ratio
    if hit_ratio >= 0.9:
        analysis['performance_level'] = 'Excellent'
        analysis['status'] = 'success'
        analysis['recommendations'].append('Cache is performing very well. Consider increasing cache TTL for frequently accessed data.')
    elif hit_ratio >= 0.7:
        analysis['performance_level'] = 'Good'
        analysis['status'] = 'info'
        analysis['recommendations'].append('Cache performance is good. Monitor for any degradation.')
    elif hit_ratio >= 0.5:
        analysis['performance_level'] = 'Fair'
        analysis['status'] = 'warning'
        analysis['recommendations'].append('Consider optimizing cache keys or increasing TTL for better performance.')
    else:
        analysis['performance_level'] = 'Poor'
        analysis['status'] = 'error'
        analysis['recommendations'].append('Cache hit ratio is low. Review caching strategy and data access patterns.')
    
    # Additional recommendations based on other metrics
    if total_operations < 100:
        analysis['recommendations'].append('Low cache usage. Consider if more data should be cached.')
    
    if cached_keys == 0:
        analysis['recommendations'].append('No cached keys found. Verify cache is being used properly.')
    elif cached_keys > 1000:
        analysis['recommendations'].append('Large number of cached keys. Consider implementing cache key expiration policies.')
    
    return analysis

# Keep existing functions (get_all_properties, clear_properties_cache, etc.)
def get_all_properties():
    """
    Fetch all properties from cache if available, otherwise from database.
    Caches the queryset for 1 hour (3600 seconds).
    
    Returns:
        QuerySet: All Property objects
    """
    cache_key = 'all_properties'
    
    try:
        # Try to get properties from cache
        properties = cache.get(cache_key)
        
        if properties is None:
            # Cache miss - fetch from database
            logger.info("🔄 Cache miss: Fetching properties from database")
            properties = Property.objects.all().order_by('-created_at')
            
            # Store in cache for 1 hour (3600 seconds)
            cache.set(cache_key, properties, 3600)
            logger.info(f"✅ Cached {properties.count()} properties for 1 hour")
        else:
            logger.info("✅ Cache hit: Serving properties from Redis")
        
        return properties
        
    except Exception as e:
        logger.error(f"❌ Error in get_all_properties: {e}")
        # Fallback to database query
        return Property.objects.all().order_by('-created_at')

def clear_properties_cache():
    """
    Clear the cached properties from Redis
    """
    try:
        cache_key = 'all_properties'
        if cache.has_key(cache_key):
            cache.delete(cache_key)
            logger.info("🗑️ Properties cache cleared")
            return True
        else:
            logger.info("ℹ️ Properties cache was already empty")
            return True
    except Exception as e:
        logger.error(f"❌ Error clearing properties cache: {e}")
        return False

def get_cached_properties_count():
    """
    Get the number of properties from cache without fetching the entire queryset
    """
    try:
        cache_key = 'all_properties'
        properties = cache.get(cache_key)
        
        if properties is not None:
            return len(properties)
        return None
    except Exception as e:
        logger.error(f"❌ Error getting cached properties count: {e}")
        return None

def refresh_properties_cache():
    """
    Force refresh the properties cache
    """
    clear_properties_cache()
    return get_all_properties()

def is_properties_cached():
    """
    Check if properties are currently cached
    """
    try:
        cache_key = 'all_properties'
        return cache.has_key(cache_key)
    except Exception as e:
        logger.error(f"❌ Error checking cache status: {e}")
        return False

def get_all_properties():
    """
    Fetch all properties from cache if available, otherwise from database.
    Caches the queryset for 1 hour (3600 seconds).
    
    Returns:
        QuerySet: All Property objects
    """
    cache_key = 'all_properties'
    
    try:
        # Try to get properties from cache
        properties = cache.get(cache_key)
        
        if properties is None:
            # Cache miss - fetch from database
            logger.info("🔄 Cache miss: Fetching properties from database")
            properties = Property.objects.all().order_by('-created_at')
            
            # Store in cache for 1 hour (3600 seconds)
            cache.set(cache_key, properties, 3600)
            logger.info(f"✅ Cached {properties.count()} properties for 1 hour")
        else:
            logger.info("✅ Cache hit: Serving properties from Redis")
        
        return properties
        
    except Exception as e:
        logger.error(f"❌ Error in get_all_properties: {e}")
        # Fallback to database query
        return Property.objects.all().order_by('-created_at')

def clear_properties_cache():
    """
    Clear the cached properties from Redis
    """
    try:
        cache_key = 'all_properties'
        if cache.has_key(cache_key):
            cache.delete(cache_key)
            logger.info("🗑️ Properties cache cleared")
            return True
        else:
            logger.info("ℹ️ Properties cache was already empty")
            return True
    except Exception as e:
        logger.error(f"❌ Error clearing properties cache: {e}")
        return False

def get_cached_properties_count():
    """
    Get the number of properties from cache without fetching the entire queryset
    """
    try:
        cache_key = 'all_properties'
        properties = cache.get(cache_key)
        
        if properties is not None:
            return len(properties)
        return None
    except Exception as e:
        logger.error(f"❌ Error getting cached properties count: {e}")
        return None

def refresh_properties_cache():
    """
    Force refresh the properties cache
    """
    clear_properties_cache()
    return get_all_properties()

def is_properties_cached():
    """
    Check if properties are currently cached
    """
    try:
        cache_key = 'all_properties'
        return cache.has_key(cache_key)
    except Exception as e:
        logger.error(f"❌ Error checking cache status: {e}")
        return False