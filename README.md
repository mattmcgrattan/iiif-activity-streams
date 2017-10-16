# IIIF Activity Streams

Turn a IIIF top level collection into a paged Activity Stream. Please read the `settings.py` and `docker_settings.py` files for more information on setting up.

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

__collection__    The IIIF Collection to base the stream on

__check_last_modified__  Set to True to dereference every manifest and check for last-modified heders to set the startTime

__use_redis__     Use Redis for local caching. Docker usage assumes Redis, but local/virtualenv can/will use alternative caching methods if set to False.

__event_ids__     Set to True to store local versions of the individual events, and serve up with dereferenceable IDs.

Other settings alter cache timeouts, and whether to cache requests to the IIIF services.

Docker settings will:

* Bring up Redis

* Use Redis for local caching of IIIF requests, and for activity streams results.

If __check_last_modified__ is set to _True_, the first time a stream is loaded, it may be slow, but it should be fast thereafter.

Set __redis_ttl__, __cache_requests_timeout__ and __cache_timeout__ to suitably long values for your service.

## Run using Docker with docker-compose

Running with Docker is a quick and easy way to test locally. 

Change the value for __collection__ in `docker_settings.py` and go.

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

