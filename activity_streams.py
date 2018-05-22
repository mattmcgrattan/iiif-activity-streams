import itertools
from datetime import timedelta

import arrow
import flask
import hashlib
import requests
import requests_cache
import simplejson as json
from flask import make_response, request, current_app, jsonify
from flask_cache import Cache
from functools import update_wrapper
from simplekv.fs import FilesystemStore
import dateparser
from collections import OrderedDict


import settings

# ====== Global/settings ==============================
#
#   A bit more baroque than required for a
#   minimal proof-of-concept service.
#

# Flask app.
app = flask.Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Set a bunch of defaults and initialise the local caching if used.

# expiry time for Flask pages cached in Redis or on Filesystem
if hasattr(settings, 'cache_timeout'):
    flask_cache_timeout = int(settings.cache_timeout)
else:
    flask_cache_timeout = None

# Cache requested IIIF resources locally.
if hasattr(settings, 'cache_requests'):
    cache_requests = settings.cache_requests
else:
    cache_requests = False

# Expiry time for IIIF/requests cached resources.
if hasattr(settings, 'cache_requests_timeout'):
    cache_requests_timeout = settings.cache_requests_timeout
else:
    cache_requests_timeout = 600  # default to 10 minutes.

# Dereference manifests and set startTime to the last-modified header value.
if hasattr(settings, 'check_last_modified'):
    check_last_modified = settings.check_last_modified
else:
    check_last_modified = False

# Use Redis for caching throughout.
if hasattr(settings, 'use_redis'):
    use_redis = settings.use_redis
else:
    use_redis = False

# Set the redis host, will default to localhost.
if hasattr(settings, 'redis_host'):
    redis_host = settings.redis_host
else:
    redis_host = 'localhost'


# expiry time for AS events stored/cached in Redis
if hasattr(settings, 'redis_ttl'):
    redis_ttl = settings.redis_ttl
else:
    redis_ttl = None

# Verbose print statements.
if hasattr(settings, 'verbose'):
    verbose = settings.verbose
else:
    verbose = False

# Set default page size.
if hasattr(settings, 'page_size'):
    pagesize = settings.page_size
else:
    pagesize = 25  # default to 25 items per page.

# Base address for the activity streams site.
# Useful for offline generation.
if hasattr(settings, 'service_base_address'):
    service_base_address = settings.service_base_address + 'as/'
else:
    service_base_address = None

# Generate @ids for the individual events.
# If True will persist the objects in Redis or on disk.
if hasattr(settings, 'event_ids'):
    event_ids = settings.event_ids
else:
    event_ids = False

# Use Redis for local caching.
if use_redis:
    """
    Simple key-value store using Redis for persisting events locally.
    The simplekv store will use settings.redis_ttl to expire items in Redis (if required).
    """
    from simplekv.memory.redisstore import RedisStore
    import redis

    store = RedisStore(redis.StrictRedis(host=redis_host, db=1))

    if flask_cache_timeout:
        cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_DB': 2,
                                   'CACHE_REDIS_HOST': redis_host,
                                   'CACHE_DEFAULT_TIMEOUT': flask_cache_timeout})
    else:
        cache = Cache(app, config={'CACHE_TYPE': 'null'})

    if cache_requests:
        """
        https://requests-cache.readthedocs.io/en/latest/
        
        Does not cache 40x results.
        """
        requests_cache.install_cache('iiif_cache', backend='redis', connection=redis.StrictRedis(host=redis_host, db=0),
                                     expire_after=cache_requests_timeout,
                                     allowable_codes=[200])
else:
    """ 
    Use sqlite for local requests caching.
    """
    store = FilesystemStore(settings.simplekv_path)

    if flask_cache_timeout:
        cache = Cache(app, config={'CACHE_TYPE': 'simple',  'CACHE_DEFAULT_TIMEOUT': flask_cache_timeout})
    else:
        cache = Cache(app, config={'CACHE_TYPE': 'null'})

    if cache_requests:
        """
        https://requests-cache.readthedocs.io/en/latest/
        
        Does not cache 40x results.
        
        Use sqlite if not using Redis. 
        """
        requests_cache.install_cache('iiif_cache', backend='sqlite', expire_after=cache_requests_timeout,
                                     allowable_codes=[200])


# ==============================================================


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
    Decorate the Flask response with CORS headers.

    :param origin:
    :param methods:
    :param headers:
    :param max_age:
    :param attach_to_all:
    :param automatic_options:
    :return:
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


def custom_error(message, status_code):
    """
    Return a custom error message as a simple Flask response

    :param message: message to include
    :param status_code: status code
    :return: json response
    """
    response = jsonify({'message': message})
    response.status_code = status_code
    return response


def get_json_resource(resource_uri):
    """
    Get a uri which returns JSON, return Python object.

    Returns None if the request status code is 4xx or 5xx.

    :param resource_uri: uri to request
    :return: Python dict/object from the request JSON.
    """
    r = requests.get(resource_uri)
    if r.status_code == requests.codes.ok:
        return r.json()
    else:
        return None


def get_members(collection):
    """
    N.B. builds entire list of members in memory.

    :param collection: IIIF collection
    :return: num_members, members: number of members, list of members
    """
    members = []
    contents = ['members', 'manifests']
    if collection:
        for content in contents:
            if content in collection:
                [members.append(m) for m in collection[content]]
    else:
        return
    if members:
        num_members = len(members)
    else:
        return
    return num_members, members


def chunked_members(num_memb, memb, chunksize=10):
    """
    Yield manifests in lists of size chunksize.


    :param memb:list of members
    :param num_memb: length of list of members
    :param chunksize: size of chunk to yield, defaults to 10
    :return:
    """
    if memb and num_memb:
        for mem_index in range(0, num_memb, chunksize):
            yield memb[mem_index:min(mem_index + chunksize, num_memb)]
    else:
        return


def member_to_as_item(item, collection, url_base, end_time=str(arrow.utcnow()), check_modified=check_last_modified):
    """
    Convert manifest/member to an ActivityStreams event.

    Uses hash of the item @id to generate an id for the event, and persists to disk using simplekv.

    Example (from Rob Sanderson's gist):
    {
            "id": "http://data.getty.edu/iiif/discovery/event/196421",
            "type": "Update",
            "actor": "http://getty.edu/museum",
            "instrument": "http://github.com/thegetty/iiif_museum_transformer",
            "object": {
                "id": "https://data.getty.edu/iiif/museum/33092/manifest.json",
                "type": "Manifest",
                "label": "Example Museum Object",
                "within": "https://data.getty.edu/iiif/museum/collection/paintings.json"
            },
            "startTime": "2017-09-19T20:00:00Z",
            "endTime": "2017-09-19T20:01:00Z",
            "published": "2017-09-20T00:00:00Z"
        }
    :param collection: IIIF Collection
    :param item: Python object for the manifest/member item
    :param url_base: base to use when constructing the URI for the dereferenceable event
    :param end_time: time, defaults to utcnow()
    :param check_modified: if True, attempt to de-reference the manifest and check the last-modified date.
    :return: object for the ActivityStreams event
    """
    # hash the manifest URI to create a key for the 'event'.
    key = hashlib.md5(item['@id'].encode('ascii')).hexdigest()
    try:
        cached_obj = store.get(key)
    except KeyError:
        cached_obj = None
    if cached_obj:  # check for cached object, N.B. Redis uses ttl to expire after a time set in settings.py
        if verbose:
            print('========Cached=========')
            print(cached_obj)
        return json.loads(cached_obj)
    else:
        if check_modified:
            r = requests.get(item['@id'])
            if r.status_code == requests.codes.ok:
                h = r.headers
                if 'last-modified' in h:
                    last_m = arrow.get(dateparser.parse(h['last-modified']))
                    if last_m:
                        end_time = str(last_m)
        if item['@type'] == 'sc:Manifest':
            obj_type = 'Manifest'
        elif item['@type'] == 'sc:Collection':
            obj_type = 'Collection'
        else:
            obj_type = item['@type']
        obj = {'object': {'id': item['@id'], 'type': obj_type, 'label': item['label'],
                          'within': collection}, 'endTime': end_time}
        # Grab optional settings
        if hasattr(settings, 'verb'):
            obj['type'] = settings.verb
        else:
            obj['type'] = 'Update'
        if hasattr(settings, 'actor'):
            obj['actor'] = settings.actor
        if hasattr(settings, 'instrument'):
            obj['instrument'] = settings.instrument
        if verbose:
            print('=========NOT from Cache=======')
            print(json.dumps(obj, indent=4))
        if event_ids:
            obj['id'] = url_base.replace('/as/', '/activity/') + key
            if use_redis:
                store.put(key, json.dumps(obj).encode('ascii'), ttl_secs=redis_ttl)
            else:
                store.put(key, json.dumps(obj).encode('ascii'))
        return obj


def as_pages(numb_m, members, collection_id, base_id, size=10):
    """
    Generator function to yield items in pages of size size.

    :param collection_id: IIIF Collection @id
    :param numb_m: Number of members in the total item list
    :param members: List of member items
    :param base_id: the URI the site lives at
    :param size: page size
    :return: list of items
    """
    for chunk in chunked_members(num_memb=numb_m, memb=members, chunksize=size):
        yield {'items': [member_to_as_item(manifest,
                                           collection=collection_id,
                                           url_base=base_id) for manifest in chunk]}


def ceildiv(a, b):
    """
    Ceiling division, used rounding up page size numbers
    :param a: numerator
    :param b: denominator
    :return: integer
    """
    return -(-a // b)


def as_paged(number_of_members, member_list, collection, id_base, page_size):
    """
    Generator function to return ActivityStreams pages with first, previous, next, last, etc.

    :param number_of_members: total number of items
    :param member_list: list of member items
    :param collection: IIIF Collection @id
    :param id_base: te URI the site lives at
    :param page_size: page size
    :return: ActivityStreams page objects, size of results
    """
    count = 1
    # number of pages in the final result set
    result_size = ceildiv(number_of_members, page_size)
    print('Paged result size', result_size)
    for as_page in as_pages(numb_m=number_of_members,
                            members=member_list, collection_id=collection, base_id=id_base, size=page_size):
        first = False
        last = False
        if count == 1:
            first = True
        elif count == result_size:
            last = True
        results_page = OrderedDict()
        results_page['@context'] = [
                            "http://iiif.io/api/presentation/2/context.json",
                            "https://www.w3.org/ns/activitystreams"
                            ]
        results_page['@id'] = id_base + str(count)
        results_page['type'] = 'OrderedCollectionPage'
        results_page['partOf'] = {'id': id_base, 'type': 'OrderedCollection'}
        if not first:
            results_page['prev'] = {'id': id_base + str(count - 1), 'type': 'OrderedCollectionPage'}
        if not last:
            results_page['next'] = {'id': id_base + str(count + 1), 'type': 'OrderedCollectionPage'}
            # results_page['last'] = {'id': id_base + str(result_size), 'type': 'OrderedCollectionPage'}
        results_page['orderedItems'] = as_page['items']
        yield results_page, result_size
        count += 1


def streamer(number_of_members, member_list, top_uri, service_uri, size_of_page=25):
    """
    Wrapper around as_paged

    :param number_of_members: number of members in the total list
    :param member_list: list of item objects
    :param top_uri: IIIF Collection @id
    :param service_uri: URI the page lives at
    :param size_of_page: page size
    :return: ActivityStreams pages
    """
    for as_p, no_results in as_paged(number_of_members=number_of_members,
                                     member_list=member_list, id_base=service_uri,
                                     page_size=size_of_page, collection=top_uri):
        yield (as_p)


def page_slicer(activity_streams_pages, position):
    """
    Return a specific page within the activity stream using itertools islice.

    :param activity_streams_pages: generator of activity streams pages
    :param position: position in the list of pages
    :return: ActivityStreams page object
    """
    try:
        page = next(itertools.islice(activity_streams_pages, position - 1, position))
        return page
    except StopIteration:
        return


def gen_top(service_uri, no_pages, num_mem, label=None):
    """
    Generate the top level collection page.

    :param service_uri: base uri for the AS paged site.
    :param no_pages:
    :param num_mem:
    :param label:
    :return: dict
    """
    top = OrderedDict()
    top['@context'] = [
                "http://iiif.io/api/presentation/2/context.json",
                "https://www.w3.org/ns/activitystreams"
            ]
    top['id'] = service_uri
    top['type'] = 'OrderedCollection'
    if label:
        top['label'] = label
    top['total'] = num_mem
    top['first'] = {'id': service_uri + str(1), 'type': 'OrderedCollectionPage'}
    top['last'] = {'id': service_uri + str(no_pages), 'type': 'OrderedCollectionPage'}
    return top


@app.route('/activity/<path:identifier>', methods=['GET'])
@crossdomain(origin='*')  # add CORS
@cache.cached()  # Flask caching.
def activity(identifier):
    """
    Return individual dereferenceable activity streams event.

    Pulls the json from simplekv store.

    :param identifier: MD5 hash of the manifest/member @id
    :return: Flask json
    """
    if identifier:
        try:
            return jsonify(json.loads(store.get(identifier)))
        except KeyError:
            return custom_error('Activity not found', 404)
    else:
        return custom_error('Activity not found', 404)


@app.route('/as/', defaults={'identifier': '0'})
@app.route('/as/<path:identifier>', methods=['GET'])
@crossdomain(origin='*')  # add CORS
@cache.cached()  # Flask caching.
def stream(identifier):
    """
    Activity Streams pages Flask app.
    :param identifier: page number (or no page for the first page)
    :return: Activity Streams page as Flask json
    """
    if identifier:
        page_number = int(identifier)
    else:
        page_number = 0
    if not service_base_address:
        service_address = request.url_root + 'as/'
    else:
        service_address = service_base_address
    # noinspection PyBroadException
    try:
        collection_uri = settings.collection
        print(collection_uri)
        number_of_members, member_list = get_members(get_json_resource(resource_uri=collection_uri))
        if page_number == 0:
            return jsonify(gen_top(service_uri=service_address, no_pages=ceildiv(number_of_members, pagesize),
                                   num_mem=number_of_members, label='Top level collection: ' + collection_uri))
        activity_streams_pages = streamer(number_of_members=number_of_members, member_list=member_list,
                                          top_uri=collection_uri, service_uri=service_address,
                                          size_of_page=pagesize)
        p = page_slicer(activity_streams_pages=activity_streams_pages, position=page_number)
        if p:
            return jsonify(p)
        else:
            return custom_error('That results page does not exist', 404)
    except IndexError:
        return custom_error('That results page does not exist', 404)
    except Exception as e:
        print(e)
        return custom_error('An unexpected error occurred', 500)


if __name__ == "__main__":
    app.run(threaded=True, debug=True, port=5000, host='0.0.0.0')
