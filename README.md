# ida-activity-streams
Stream manifest and collection create, update, delete events as an ActivityStreams feed.

This is a proof of concept illustration. Please read LICENSE for standard MIT license conditions.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Configuration

Update `settings.py` for local/virtualenv usage.

Update `docker_settings.py` for docker usage.

### Main Config

_collection_    The IIIF Collection to base the stream on

_check_last_modified_  Set to True to dereference every manifest and check for last-modified heders to set the startTime

_use_redis_     Use Redis for local caching. Docker usage assumes Redis, but local/virtualenv can use alternative caching methods if set to False.

_event_ids_     Set to True to store local versions of the individual events, and serve up with dereferenceable IDs.

Other settings alter cache timeouts, and whether to cache requests to the IIIF services.

Docker settings will:

Bring up Redis

Use Redis for local caching of IIIF requests, and for activity streams results.

if _check_last_modified_ is set to True, the first time a stream is loaded, it may be slow, but it should be fast thereafter.

Set _redis_ttl_, _cache_requests_timeout_ and _cache_timeout_ to suitably long values for your service.

## Run using Docker with docker-compose


Will build Redis and Flask/uWSGI apps and link them.

`git clone https://github.com/mattmcgrattan/iiif-activity-streams.git`

`cd iiif-activity-streams/`

`docker-compose up --build -d`

Default will expose the application port on 8000.

Test by going to `'http://localhost:8000/as/'`

N.B. Run with `docker-compose up --build`

To run it not daemonized, so you can see what's happening.


## Run in a virtualenv

Has been tested with Python 2.7, Python 3.6, and PyPy.

`git clone https://github.com/mattmcgrattan/iiif-activity-streams.git`

`cd iiif-activity-streams/`

`virtualenv -p Python3 .`

`source bin/activate`

`pip install -r requirements.txt`

`python activity_streams.py`

to serve on localhost:5000 using Flask in debug mode.

