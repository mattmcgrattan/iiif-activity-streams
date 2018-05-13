# if check_last_modified = True
#
# will load manifests and check last-modified header, using this for the AS event.
#
# Caution: Can massively slow performance down, as this has to request each manifest,
# and generates many HTTP requests.
#
# Requests can be cached using cache_requests, to improve performance during testing.
#
# Unless you _know_ you have last-modified header dates you want to expose, set to False.

check_last_modified = False

# Collection to provide a stream for

collection = 'https://manifests.dlcs-ida.org/top'

# Will default to 'Update' if not set.
verb = 'Update'

# Size of pages to return
page_size = 100

# Cache Flask incoming requests for N seconds. Comment out for no Flask caching, 86400s = 1 day.
cache_timeout = 60

# Set to True to cache requests made to the source IIIF collection, false to make each request each time.
cache_requests = True
cache_requests_timeout = 86400  # Cache HTTP requests made for N seconds. 86400 = 1 day.

# Path to store local JSON objects for simplekv persistence of AS events on filesystem.
simplekv_path = './data'

# Cache results AND requets using Redis.
# Set to False to persist AS items/Flask cache to local filestore & cached requests to sqlite
use_redis = True

# set to 'redis' for Docker use.
redis_host = 'redis'

# Set expiry on persistence of AS events, if using Redis.
redis_ttl = 86400  # 86400 = 1 day

# Print informative messages.
verbose = True

# optional
# actor = 'https://www.example.com/user/foo'

# optional
# instrument = 'https://www.example.com/workflow/'

# optional, will use address hosted at.
# service_base_address = 'http://www.example.com/'

# if True, generate dereferenceable ids for events and cache/persist the JSON content.
event_ids = True
