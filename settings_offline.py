
"""
if check_last_modified = True, will load manifests and check last-modified header, using this for the AS event.

Caution: Can massively slow performance down, as has to load each manifest, and generates many HTTP requests.

Requests can be cached using cache_requests, to improve performance during testing.

Unless you _know_ you have last-modified header dates you want to expose, set to False.
"""
check_last_modified = True  # See note above. If False, will use time of request for the StartTime.
collection = 'https://labs2.artstor.org/iiif/ssc/manifest.json'
verb = 'Update'  # Will default to 'Update' if not set.
page_size = 100
cache_requests = False  # Not optional. set to True to cache requests made to the source IIIF collection.
cache_requests_timeout = 86400  # Cache the IIIF collection and any manifest requests made for N seconds. 86400 = 1 day.
cache_timeout = 86400  # Cache Flask incoming requests for N seconds. None for no Flask caching, 86400 = 1 day.
simplekv_path = './data'  # Path to store local JSON objects for simplekv persistence of AS events on filesystem.
use_redis = False  # Not optional. Set to False to persist AS items/Flask cache to local filestore & requests to sqlite.
redis_ttl = 86400  # Set expiry on simplekv persistence of AS events, if using Redis. 86400 = 1 day.
verbose = True  # Print informative messages.
# actor = 'https://www.example.com/user/foo'  # optional
# instrument = 'https://www.example.com/workflow/'  # optional
service_base_address = 'http://activities.example.com/as/'  # optional, will use address hosted at.
output_file = 'output.json'
