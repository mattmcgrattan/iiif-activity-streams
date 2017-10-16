import settings_offline
from simplekv.fs import FilesystemStore
import requests_cache


# ====== Global/settings ==============================

# If True, will dereference manifests and attempt to set startTime to the last-modified header value.
# This can be extremely slow with large collections.
try:
    check_last_modified = settings_offline.check_last_modified
except AttributeError:
    check_last_modified = False

# expiry time for AS events stored/cached in Redis
try:
    redis_ttl = settings_offline.redis_ttl
except AttributeError:
    redis_ttl = None

if settings_offline.use_redis:
    """
    Simple key-value store using Redis for persisting events locally.

    http://simplekv.readthedocs.io/en/latest/

    Can be configured to use JSON on the filesystem. See below. 

    Flask cache also using Redis. Expiry after settings.cache_timeout.

    The simplekv store will use settings.redis_ttl to expire items in Redis (if required).
    """
    from simplekv.memory.redisstore import RedisStore
    import redis

    store = RedisStore(redis.StrictRedis(db=1))
    if settings_offline.cache_requests:
        """
        If set, will cache requests to remote servers (using Redis)

        Useful during testing. Will expire requests after settings.cache_requests_timeout.

        https://requests-cache.readthedocs.io/en/latest/
        """
        requests_cache.install_cache('iiif_cache', backend='redis',
                                     expire_after=settings_offline.cache_requests_timeout,
                                     allowable_codes=[200, 404])
else:
    """ 
    Simple key-value store using JSON on the filesystem.

    Plus Flask Cache using local filesystem.
    """
    store = FilesystemStore(settings_offline.simplekv_path)
    if settings_offline.cache_requests:
        """
        If set, will cache requests to remote servers.

        Useful during testing. Use sqlite backend if not using Redis.    
        """
        requests_cache.install_cache('iiif_cache', backend='sqlite',
                                     expire_after=settings_offline.cache_requests_timeout,
                                     allowable_codes=[200, 404])
# ====================================