
# Copyright (c) PagerDuty.
# See LICENSE for details.

import logging
import sys
import time
import warnings
from copy import deepcopy

import requests
from urllib3.connection import ConnectionError as Urllib3Error
from requests.exceptions import ConnectionError as RequestsError

if sys.version_info[0] == 3:
    string_types = str
else:
    string_types = basestring

__version__ = '3.1.1'


# These are API resource endpoints/methods for which multi-update is supported
valid_multi_update_paths = [
    ('incidents', '{index}'),
    ('incidents', '{id}', 'alerts', '{index}'),
    ('priorities', '{index}'),
]

#########################
### UTILITY FUNCTIONS ###
#########################

def auto_json(method):
    """
    Function decorator that makes methods return the full response JSON
    """
    def call(self, path, **kw):
        response = raise_on_error(method(self, path, **pass_kw))
        return try_decoding(response)
    return call

def last_4(secret):
    """Returns an abbreviation of the input"""
    return '*'+str(secret)[-4:]

def object_type(r_name):
    """
    Derives an object type (i.e. ``user``) from a resource name (i.e. ``users``)

    :param r_name:
        Resource name, i.e. would be ``users`` for the resource index URL
        ``https://api.pagerduty.com/users``
    :returns: The object type name; usually the ``type`` property of an instance
        of the given resource.
    :rtype: str
    """
    if r_name.endswith('ies'):
        # Because English
        return r_name[:-3]+'y'
    else:
        return r_name.rstrip('s')

def raise_on_error(r):
    """
    Raise an exception if a HTTP error response has error status.

    :param r: Response object corresponding to the response received.
    :type r: `requests.Response`_
    :returns: The response object, if its status was success
    :rtype: `requests.Response`_
    """
    if r.ok:
        return r
    else:
        raise PDClientError("%s %s: API responded with non-success status "
            "(%d)"%(
                r.request.method.upper(),
                r.request.url.replace('https://api.pagerduty.com', ''),
                r.status_code
            ), response=r
        )

def resource_envelope(method):
    """
    Convenience and consistency decorator for HTTP verb functions.

    This makes the request methods ``GET``, ``POST`` and ``PUT`` always return a
    dictionary object representing the resource at the envelope property (i.e.
    the ``{...}`` from ``{"escalation_policy":{...}}`` in a get/put request to
    an escalation policy)  rather than a `requests.Response`_ object.

    Methods using this decorator will raise a :class:`PDClientError` with its
    ``response`` property being being the `requests.Response`_ object in the
    case of any error, so that the implementer can access it by catching the
    exception, and thus design their own custom logic around different types of
    error responses.

    It allows creation of methods that can provide more succinct ways of making
    API calls. In particular, the methods using this decorator don't require
    checking for a success status, JSON-decoding the response body and then
    pulling the essential data out of the envelope (i.e. for ``GET
    /escalation_policies/{id}`` one would have to access the
    ``escalation_policy`` property of the object decoded from the response body,
    assuming nothing went wrong in the whole process).

    These methods are :attr:`APISession.rget`, :attr:`APISession.rpost` and
    :attr:`APISession.rput`.

    :param method: Method being decorated. Must take one positional argument
        after ``self`` that is the URL/path to the resource, and must return an
        object of class `requests.Response`_, and be named after the HTTP method
        but with "r" prepended.
    :returns: A callable object; the reformed method
    """
    global valid_multi_update_paths
    http_method = method.__name__.lstrip('r')
    def call(self, path, **kw):
        pass_kw = deepcopy(kw) # Make a copy for modification
        nodes = tokenize_url_path(path, baseurl=self.url)
        is_index = nodes[-1] == '{index}'
        resource = nodes[-2]
        multi_put = http_method == 'put' and nodes in valid_multi_update_paths
        envelope_name_single = object_type(resource) # Usually the "type"
        if is_index and http_method=='get' or multi_put:
            # Plural resource name, for index action (GET /<resource>), or for
            # multi-update (PUT /<resource>). In both cases, the response
            # (former) or request (latter) body is {<resource>:[<objects>]}
            envelope_name = resource
        else:
            # Individual resource create/read/update
            # Body = {<singular-resource-type>: {<object>}}
            envelope_name = envelope_name_single
        # Validate the abbreviated (or full) request payload, and automatically
        # fill the gap for the implementer if some assumptions hold true:
        if http_method in ('post', 'put') and 'json' in pass_kw and \
                envelope_name not in pass_kw['json']:
            pass_kw['json'] = {envelope_name: pass_kw['json']}

        r = raise_on_error(method(self, path, **pass_kw))
        # Now let's try to unpack...
        response_obj = try_decoding(r)
        # Get the encapsulated object
        if envelope_name not in response_obj:
            raise PDClientError("Cannot extract object; expected top-level "
                "property \"%s\", but could not find it in the response "
                "schema. Response body=%s"%(envelope_name, r.text[:99]),
                response=r)
            return None
        return response_obj[envelope_name]
    return call

def resource_name(obj_type):
    """
    Transforms an object type into a resource name

    :param obj_type:
        The object type, i.e. ``user`` or ``user_reference``
    :returns: The name of the resource, i.e. the last part of the URL for the
        resource's index URL
    :rtype: str
    """
    if obj_type.endswith('_reference'):
        # Strip down to basic type if it's a reference
        obj_type = obj_type[:obj_type.index('_reference')]
    if obj_type.endswith('y'):
        # Because English
        return obj_type[:-1]+'ies'
    else:
        return obj_type+'s'

def tokenize_url_path(url, baseurl='https://api.pagerduty.com'):
    """
    Classifies a URL according to some global patterns in the API.

    If the URL is to access a specific individual resource by ID, the node type
    will be identified as ``{id}``, whereas if it is an index, it will be
    identified as ``{index}``.

    For instance, ``https://api.pagerduty.com/users`` would be classified as
    ``("users", "{index}")``, and ``https://api.pagerduty.com/users/PABC123``
    would be classified as ``("users", "{id}")``

    :param url:
        The URL (or path) to be classified; the function should accept either
    :param baseurl:
        API base URL
    :type method: str
    :type url: str
    :type baseurl: str
    :rtype: tuple 
    """
    urlnparams = url.split('#')[0].split('?') # Ignore all #'s / params
    url_nodes = urlnparams[0].lstrip('/').split('/')
    path_index = 0
    invalid_url = ValueError('Invalid API resource URL: '+url[:99])
    # Validate URL or path:
    if url.startswith(baseurl):
        # Full URL: path starts after the third forward slash
        path_index = 3
    elif url.startswith('http') and url_nodes[0].endswith(':'):
        # Full URL but not within the REST API
        raise invalid_url
    if len(url_nodes) - path_index < 1:
        # Incomplete URL (API web root is not a valid resource)
        raise invalid_url
    # Path nodes generally start after the hostname, at path_index
    path_nodes = tuple(url_nodes[path_index:])
    if '' in path_nodes:
        # Empty node due to two consecutive unescaped forward slashes (or
        # trailing slash in the case of it being just the base URL plus slash)
        raise invalid_url
    # Tokenize / classify the URL now:
    tokenized_nodes = [path_nodes[0]]
    if len(path_nodes) >= 3:
        # It's an endpoint like one of the following 
        # /{resource}/{id}/{sub-resource}
        # We're interested in {resource} and {sub_resource}.
        # More deeply-nested endpoints not known to exist.
        tokenized_nodes.extend(('{id}', path_nodes[2]))
    # If the number of path nodes is even: it's an individual resource URL, and
    # the resource name will be the second to last path node. Otherwise, it is
    # a resource index, and the resource name will be the last pathnode.
    # However, if the request was GET, and made to an index endpoint, the
    # envelope property should simply be the resource name.
    #
    # This is a ubiquitous pattern throughout the PagerDuty REST API: path
    # nodes alternate between identifiers and resource names.
    final_node_type = '{id}'
    if len(path_nodes)%2 == 1:
        final_node_type = '{index}'
    tokenized_nodes.append(final_node_type)
    return tuple(tokenized_nodes)

def try_decoding(r):
    """
    JSON-decode a response body and raise :class:`PDClientError` if it fails.

    :param r:
        `requests.Response`_ object
    """
    try:
        return r.json()
    except ValueError as e:
        raise PDClientError("API responded with invalid JSON: "+r.text[:99],
            response=r)

###############
### CLASSES ###
###############

class PDSession(requests.Session):
    """
    Base class for making HTTP requests to PagerDuty APIs.

    Instances of this class are essentially the same as `requests.Session`_
    objects, but with a few modifications:

    - The client will reattempt the request with configurable, auto-increasing
      cooldown/retry intervals if encountering a network error or rate limit
    - When making requests, headers specified ad-hoc in calls to HTTP verb
      functions will not replace, but will be merged with, default headers.
    - The request URL, if it doesn't already start with the REST API base URL,
      will be prepended with the default REST API base URL.
    - It will only perform requests with methods as given in the
      :attr:`permitted_methods` list, and will raise :class:`PDClientError` for
      any other HTTP methods.
    """

    log = None
    """A ``logging.Logger`` object for printing messages."""

    max_http_attempts = 10
    """
    The number of times that the client will retry after error statuses, for any
    that are defined greater than zero in :attr:`retry`.
    """

    max_network_attempts = 3
    """
    The number of times that connecting to the API will be attempted before
    treating the failure as non-transient; a :class:`PDClientError` exception
    will be raised if this happens.
    """

    parent = None
    """The ``super`` object (`requests.Session`_)"""

    permitted_methods = ()

    raise_if_http_error = True
    """
    Raise an exception upon receiving an error response from the server.

    This affects iteration (in the REST API) as well as the generic request
    method itself.

    In the general case: if set to True, then upon receiving a non-transient
    HTTP error (from too many retries), an exception will be raised. Otherwise,
    the response object will be returned.

    In iteration: if set to true, an exception will be raised in
    :attr:`iter_all` if a HTTP error is encountered. This is the default
    behavior in versions >= 2.1.0.  If False, the behavior is to halt iteration
    upon receiving a HTTP error.
    """

    retry = None
    """
    A dict defining the retry behavior for each HTTP response status code.

    Each key in this dictionary represents a HTTP response code. The behavior is
    specified by the value at each key as follows:

    * ``-1`` to retry infinitely
    * ``0`` to return the `requests.Response`_ object and exit (which is the
      default behavior) 
    * ``n``, where ``n > 0``, to retry ``n`` times (or up
      to :attr:`max_http_attempts` total for all statuses, whichever is
      encountered first), and raise a :class:`PDClientError` after that many
      attempts. For each successive attempt, the wait time will increase by a
      factor of :attr:`sleep_timer_base`.

    The default behavior is to retry infinitely on a 429, and return the
    response in any other case (assuming a HTTP response was received from the
    server).
    """

    sleep_timer = 1.5
    """
    Default initial cooldown time factor for rate limiting and network errors.

    Each time that the request makes a followup request, there will be a delay
    in seconds equal to this number times :attr:`sleep_timer_base` to the power
    of how many attempts have already been made so far.
    """

    sleep_timer_base = 2
    """
    After each retry, the time to sleep before reattempting the API connection
    and request will increase by a factor of this amount.
    """

    url = ""

    def __init__(self, api_key, name=None):
        """
        Basic constructor for API sessions.

        :param api_key:
            The API credential to use.
        :param name:
            Identifying label for the session to use in log messages
        """
        self.parent = super(PDSession, self)
        self.parent.__init__()
        self.api_key = api_key
        if isinstance(name, string_types) and name:
            my_name = name
        else:
            my_name = self.trunc_key
        self.log = logging.getLogger('pdpyras.%s(%s)'%(
            self.__class__.__name__, my_name))
        self.retry = {}

    @property
    def api_key(self):
        """
        API Key property getter.

        Returns the _api_key attribute's value.
        """
        return self._api_key

    @api_key.setter
    def api_key(self, api_key):
        self.set_api_key(api_key)

    def postprocess(self, response):
        """
        Perform supplemental actions immediately after receiving a response.
        """
        pass

    def prepare_headers(self, method):
        """
        Append special additional per-request headers.

        :param method:
            The HTTP method, in upper case.
        """
        return self.headers

    def request(self, method, url, **kwargs):
        """
        Make a generic PagerDuty API request.

        :param method:
            The request method to use. Case-insensitive. May be one of get, put,
            post or delete.
        :param url:
            The path/URL to request. If it does not start with the base URL, the
            base URL will be prepended.
        :param \*\*kwargs:
            Additional keyword arguments to pass to `requests.Session.request
            <http://docs.python-requests.org/en/master/api/#requests.Session.request>`_
        :type method: str
        :type url: str
        :returns: the HTTP response object
        :rtype: `requests.Response`_
        """
        sleep_timer = self.sleep_timer
        network_attempts = 0
        http_attempts = {}
        method = method.strip().upper()
        if method not in self.permitted_methods:
            raise PDClientError(
                "Method %s not supported by this API. Permitted methods: %s"%(
                    method, ', '.join(self.permitted_methods)))
        req_kw = deepcopy(kwargs)
        my_headers = self.prepare_headers(method)
        # Merge, but do not replace, any headers specified in keyword arguments:
        if 'headers' in kwargs:
            my_headers.update(kwargs['headers'])
        req_kw.update({'headers': my_headers, 'stream': False})
        # Compose/normalize URL whether or not path is already a complete URL
        if url.startswith(self.url) or not self.url:
            my_url = url
        else:
            my_url = self.url + "/" + url.lstrip('/')
        # Make the request (and repeat w/cooldown if the rate limit is reached):
        while True:
            try:
                response = self.parent.request(method, my_url, **req_kw)
                self.postprocess(response)
            except (Urllib3Error, RequestsError) as e:
                network_attempts += 1
                if network_attempts > self.max_network_attempts:
                    raise PDClientError("Non-transient network error; exceeded "
                        "maximum number of attempts (%d) to connect to the "
                        "API"%self.max_network_attempts)
                sleep_timer *= self.sleep_timer_base
                self.log.debug("Connection error: %s; retrying in %g seconds.",
                    e, sleep_timer)
                time.sleep(sleep_timer)
                continue
            status = response.status_code
            retry_logic = self.retry.get(status, 0)
            if not response.ok and retry_logic != 0:
                # Take special action as defined by the retry logic
                if retry_logic != -1:
                    # Retry a specific number of times (-1 implies infinite)
                    if http_attempts.get(status, 0)>=retry_logic or \
                            sum(http_attempts.values())>self.max_http_attempts:
                        self.log.error("Non-transient HTTP error: exceeded " \
                            "maximum number of attempts (%d) to make a " \
                            "successful request. Currently encountering "
                            "status %d.", self.retry[status], status)
                        return response
                    http_attempts[status] = 1 + http_attempts.get(status, 0)
                sleep_timer *= self.sleep_timer_base
                self.log.debug("HTTP error (%d); retrying in %g seconds.",
                    status, sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif response.status_code == 429:
                sleep_timer *= self.sleep_timer_base
                self.log.debug("Hit API rate limit (response status 429); "
                    "retrying in %g seconds", sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif response.status_code == 401:
                # Stop. Authentication failed. We shouldn't try doing any more,
                # because we'll run into problems later anyway.
                raise PDClientError(
                    "Received 401 Unauthorized response from the API. The "
                    "access key (%s) might not be valid."%self.trunc_key,
                    response=response)
            else:
                # All went according to plan.
                return response

    def set_api_key(self, api_key):
        """
        Set the API key/token.

        Child classes should implement this method to do special things like
        setting default headers.

        The getter will return the value of self._api_key, so any setters should
        set this property.
        """
        self._api_key =  api_key

    @property
    def trunc_key(self):
        """Truncated key for secure display/identification purposes."""
        return last_4(self.api_key)

    @property
    def user_agent(self):
        """Unique user-agent header for making requests"""
        return 'pdpyras/%s python-requests/%s Python/%d.%d'%(
            __version__,
            requests.__version__,
            sys.version_info.major,
            sys.version_info.minor
        )

class EventsAPISession(PDSession):

    """
    Session class for submitting events to the PagerDuty v2 Events API.

    Provides methods for submitting events to the Events API.

    Inherits from :class:`PDSession`.
    """

    permitted_methods = ('POST',)

    url = "https://events.pagerduty.com"

    def acknowledge(self, dedup_key):
        """
        Acknowledge an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to set to the acknowledged state.
        """
        return self.send_event('acknowledge', dedup_key=dedup_key)

    def prepare_headers(self, method):
        """Add user agent and content type headers for Events API requests."""
        headers = deepcopy(self.headers)
        headers.update({
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
        })
        return headers

    def resolve(self, dedup_key):
        """
        Resolve an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to resolve.
        """
        return self.send_event('resolve', dedup_key=dedup_key)

    def send_event(self, action, dedup_key=None, **properties):
        """
        Send an event to the v2 Events API.

        See: https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2

        :param action:
            The action to perform through the Events API: trigger, acknowledge
            or resolve.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param \*\*properties:
            Additional properties to set, i.e. if ``action`` is ``trigger``
            this would include ``payload``
        :type action: str
        :type dedup_key: str
        :returns:
            The deduplication key of the incident, if any.
        """
        actions = ('trigger', 'acknowledge', 'resolve')
        if action not in actions:
            raise ValueError("Event action must be one of: "+', '.join(actions))
        event = {'event_action':action}
        event.update(properties)
        if isinstance(dedup_key, string_types):
            event['dedup_key'] = dedup_key
        elif not action == 'trigger':
            raise ValueError("The dedup_key property is required for"
                "event_action=%s events, and it must be a string."%action)
        response = self.post('/v2/enqueue', json=event)
        raise_on_error(response)
        response_body = try_decoding(response)
        if not 'dedup_key' in response_body:
            raise PDClientError("Malformed response body; does not contain "
                "deduplication key.", response=response)
        return response_body['dedup_key']

    def trigger(self, summary, source, dedup_key=None, severity='critical',
            payload=None, custom_details=None, images=None, links=None):
        """
        Trigger an incident

        :param summary:
            Summary / brief description of what is wrong.
        :param source:
            A human-readable name identifying the system that is affected.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param severity:
            Alert severity. Sets the ``payload.severity`` property.
        :param payload:
            Set the payload directly. Can be used in conjunction with other
            parameters that also set payload properties; these properties will
            be merged into the default payload, and any properties in this
            parameter will take precedence except with regard to
            ``custom_details``.
        :param custom_details:
            The ``payload.custom_details`` property of the payload. Will
            override the property set in the ``payload`` parameter if given.
        :param images:
            Set the ``images`` property of the event.
        :param links:
            Set the ``links`` property of the event.
        :type action: str
        :type summary: str
        :type dedup_key: str
        :type severity: str
        :type payload: dict
        :type custom_details: dict
        :type images: list
        :type links: list
        :rtype: str
        :type summary: str
        :type source: str
        :type dedup_key: str
        :type severity: str
        :type payload: dict
        :type custom_details: dict
        :type images: list
        :type links: list
        """
        for local in ('payload', 'custom_details'):
            local_var = locals()[local]
            if not (local_var is None or type(local_var) is dict):
                raise ValueError(local+" must be a dict")
        event = {'payload': {'summary':summary, 'source':source,
            'severity':severity}}
        if type(payload) is dict:
            event['payload'] = payload
        if type(custom_details) is dict:
            details = event.setdefault('payload', {}).get('custom_details', {})
            details.update(custom_details)
            event['payload']['custom_details'] = details
        if images:
            event['images'] = images
        if links:
            event['links'] = links
        return self.send_event('trigger', dedup_key=dedup_key, **event)

    def set_api_key(self, api_key):
        """
        Sets the routing key in the ``X-Routing-Key`` header.

        :param api_key:
            The routing key to use for this session.
        :type api_key: str
        """
        self._api_key = api_key
        self.headers.update({
            'X-Routing-Key': api_key,
        })

class APISession(PDSession):
    """
    Reusable PagerDuty REST API session objects for making API requests.

    Includes some convenience functions as well, i.e. :attr:`rget`, :attr:`find`
    and :attr:`iter_all`, to eliminate some repetitive tasks associated with
    making API calls.

    Inherits from :class:`PDSession`.

    :param api_key:
        REST API access token to use for HTTP requests
    :param name:
        Optional name identifier for logging. If unspecified or ``None``, it
        will be the last four characters of the REST API token.
    :param default_from:
        Email address of a valid PagerDuty user to use in API requests by
        default as the ``From`` header (see: `HTTP Request Headers`_)
    :type token: str
    :type name: str or None
    :type default_from: str or None

    :members:
    """

    api_call_counts = None 
    """A dict object recording the number of API calls per endpoint"""

    api_time = None
    """A dict object recording the total time of API calls to each endpoint"""

    default_from = None
    """The default value to use as the ``From`` request header"""

    default_page_size = 100
    """
    This will be the default number of results requested in each page when
    iterating/querying an index (the ``limit`` parameter). See: `pagination`_.
    """

    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = 'https://api.pagerduty.com'
    """Base URL of the REST API"""

    def __init__(self, api_key, name=None, default_from=None):
        if not (isinstance(api_key, string_types) and api_key):
            raise ValueError("API token must be a non-empty string.")
        self.api_call_counts = {}
        self.api_time = {}
        super(APISession, self).__init__(api_key, name)
        self.default_from = default_from
        self.headers.update({
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def dict_all(self, path, **kw):
        """
        Returns a dictionary of all objects from a given index endpoint.

        With the exception of ``by``, all keyword arguments passed to this
        method are also passed to :attr:`iter_all`; see the documentation on
        that method for further details.

        :param path:
            The index endpoint URL to use.
        :param by:
            The attribute of each object to use for the key values of the
            dictionary. This is ``id`` by default. Please note, there is no
            uniqueness validation, so if you use an attribute that is not
            distinct for the data set, this function will omit some data in the
            results.
        :param params:
            Additional URL parameters to include.
        :param paginate:
            If True, use `pagination`_ to get through all available results. If
            False, ignore / don't page through more than the first 100 results.
            Useful for special index endpoints that don't fully support
            pagination yet, i.e. "nested" endpoints like
            ``/users/{id}/contact_methods`` and ``/services/{id}/integrations``
        """
        by = kw.pop('by', 'id')
        iterator = self.iter_all(path, **kw)
        return {obj[by]:obj for obj in iterator}


    def find(self, resource, query, attribute='name', params=None):
        """
        Finds an object of a given resource exactly matching a query.

        Will query a given `resource index`_ endpoint using the ``query``
        parameter supported by most indexes.

        Returns a dict if a result is found. The structure will be that of an
        entry in the index endpoint schema's array of results. Otherwise, it
        will return `None` if no result is found or an error is encountered.

        :param resource:
            The name of the resource endpoint to query, i.e.
            ``escalation_policies``
        :param query:
            The string to query for in the the index.
        :param attribute:
            The property of each result to compare against the query value when
            searching for an exact match. By default it is ``name``, but when
            searching for user by email (for example) it can be set to ``email``
        :param params:
            Optional additional parameters to use when querying.
        :type resource: str
        :type query: str
        :type attribute: str
        :type params: dict or None
        :rtype: dict
        """
        query_params = {}
        if params is not None:
            query_params.update(params)
        query_params.update({'query':query})
        # When determining uniqueness, web/the API doesn't care about case.
        simplify = lambda s: s.lower()
        search_term = simplify(query) 
        equiv = lambda s: simplify(s[attribute]) == search_term
        obj_iter = self.iter_all(resource, params=query_params)
        return next(iter(filter(equiv, obj_iter)), None)

    def iter_all(self, path, params=None, paginate=True, item_hook=None,
            total=False):
        """
        Iterator for the contents of an index endpoint or query.

        Automatically paginates and yields the results in each page, until all
        matching results have been yielded or a HTTP error response is received.

        Each yielded value is a dict object representing a result returned from
        the index. For example, if requesting the ``/users`` endpoint, each
        yielded value will be an entry of the ``users`` array property in the
        response; see: `List Users
        <https://v2.developer.pagerduty.com/v2/page/api-reference#!/Users/get_users>`_

        :param path:
            The index endpoint URL to use.
        :param params:
            Additional URL parameters to include.
        :param paginate:
            If True, use `pagination`_ to get through all available results. If
            False, ignore / don't page through more than the first 100 results.
            Useful for special index endpoints that don't fully support
            pagination yet, i.e. "nested" endpoints like (as of this writing):
            ``/users/{id}/contact_methods`` and ``/services/{id}/integrations``
        :param item_hook:
            Callable object that will be invoked for each iteration, i.e. for
            printing progress. It will be called with three parameters: a dict
            representing a given result in the iteration, the number of the
            item, and the total number of items in the series.
        :param total:
            If True, the ``total`` parameter will be included in API calls, and
            the value for the third parameter to the item hook will be the total
            count of records that match the query. Leaving this as False confers
            a small performance advantage, as the API in this case does not have
            to compute the total count of results in the query.
        :type path: str
        :type params: dict or None
        :type paginate: bool
        :type total: bool
        :yields: Results from the index endpoint.
        :rtype: dict
        """
        # Validate that it's an index URL being requested:
        path_nodes = tokenize_url_path(path, baseurl=self.url)
        if not path_nodes[-1] == '{index}':
            raise ValueError("Invalid index url/path: "+path[:99])
        # Determine the resource name:
        r_name = path_nodes[-2]
        # Parameters to send:
        data = {}
        if paginate:
            # Retrieve 100 at a time unless otherwise specified:
            data['limit'] = self.default_page_size
        if total:
            data['total'] = 1
        if params is not None:
            # Override defaults with values given:
            data.update(params)

        more = True
        offset = 0
        n = 0
        while more: # Paginate through all results
            if paginate:
                data['offset'] = offset
            r = self.get(path, params=data.copy())
            if not r.ok:
                if self.raise_if_http_error:
                    raise PDClientError("Encountered HTTP error status (%d) "
                        "response while iterating through index endpoint %s."%(
                            r.status_code, path), response=r)
                self.log.debug("Stopping iteration on endpoint \"%s\"; API "
                    "responded with non-success status %d", path, r.status_code)
                break
            try:
                response = r.json()
            except ValueError: 
                self.log.debug("Stopping iteration on endpoint %s; API "
                    "responded with invalid JSON.", path)
                break
            if 'limit' in response:
                data['limit'] = response['limit']
            more = False
            total_count = None
            if paginate:
                if 'more' in response:
                    more = response['more']
                else:
                    self.log.debug("Pagination is enabled in iteration, but the" 
                        " index endpoint %s responded with no \"more\" property"
                        " in the response. Only the first page of results, "
                        "however many can be gotten, will be included.", path)
                if 'total' in response:
                    total_count = response['total']
                else: 
                    self.log.debug("Pagination and the \"total\" parameter "
                        "are enabled in iteration, but the index endpoint %s "
                        "responded with no \"total\" property in the response. "
                        "Cannot display a total count of this resource without "
                        "first retrieving all records.", path)
                offset += data['limit']
            for result in response[r_name]:
                n += 1 
                # Call a callable object for each item, i.e. to print progress:
                if hasattr(item_hook, '__call__'):
                    item_hook(result, n, total_count)
                yield result

    @auto_json
    def jget(self, path, **kw):
        """
        Performs a GET request, returning the JSON-decoded body as a dictionary

        :raises PDClientError: In the event of HTTP error 
        """
        return self.get(path, **kw)

    @auto_json
    def jpost(self, path, **kw):
        """
        Performs a POST request, returning the JSON-decoded body as a dictionary

        :raises PDClientError: In the event of HTTP error 
        """
        return self.post(path, **kw)

    @auto_json
    def jput(self, path, **kw):
        """
        Performs a PUT request, returning the JSON-decoded body as a dictionary

        :rauses PDClientError: In the event of HTTP errror
        """
        return self.put(path, **kw)

    def list_all(self, path, **kw):
        """
        Returns a list of all objects from a given index endpoint.

        All keyword arguments passed to this function are also passed directly
        to :attr:`iter_all`; see the documentation on that method for details.

        :param path:
            The index endpoint URL to use.
        """
        return list(self.iter_all(path, **kw))

    def postprocess(self, response, suffix=None):
        """
        Records performance information about the API call.

        This method is called automatically by :func:`request` for all requests,
        and can be extended in child classes.

        :param method:
            Method of the request
        :param response: 
            Response object
        :param suffix: 
            Optional suffix to append to the key
        :type method: str
        :type response: `requests.Response`_
        :type suffix: str or None
        """
        key = self.profiler_key(response.request.method, response.url,
            suffix=suffix)
        self.api_call_counts.setdefault(key, 0)
        self.api_time.setdefault(key, 0.0)
        self.api_call_counts[key] += 1
        self.api_time[key] += response.elapsed.total_seconds()

    def prepare_headers(self, method):
        headers = deepcopy(self.headers)
        headers['User-Agent'] = self.user_agent
        if self.default_from is not None:
            headers['From'] = self.default_from
        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/json'
        return headers

    def profiler_key(self, method, path, suffix=None):
        """
        Generates a fixed-format key to classify a request, i.e. for profiling.

        Returns a string that will have all instances of IDs replaced with
        ``{id}``, and will begin with the method in lower case followed by a
        colon, i.e. ``get:escalation_policies/{id}``

        :param method:
            The request method
        :param path:
            The path/URI to classify
        :param suffix:
            Optional suffix to append to the key
        :type method: str
        :type path: str
        :type suffix: str
        :rtype: str
        """
        my_suffix = "" if suffix is None else "#"+suffix 
        path_str = '/'.join(tokenize_url_path(path, baseurl=self.url))
        return '%s:%s'%(method.lower(), path_str)+my_suffix

    def rdelete(self, path, **kw):
        raise_on_error(self.delete(path, **kw))

    @resource_envelope
    def rget(self, path, **kw):
        """
        Retrieve a resource and return the encapsulated object in the response
        """
        return self.get(path, **kw)

    @resource_envelope
    def rpost(self, path, **kw):
        """
        Create a resource.

        Returns the dictionary object representation if creating it was
        successful.

        :param path: The path/URL to which to send the POST request.
        :param \*\*kw: Keyword arguments to pass to ``requests.Session.post``
        :returns: Dictionary representation of the created object
        :rtype: 
        """
        return self.post(path, **kw)

    @resource_envelope
    def rput(self, path, **kw):
        """
        Update an individual resource, returning the encapsulated object.

        :param path: The path/URL to which to send the PUT request.
        :param \*\*kw: Keyword arguments to pass to ``requests.Session.put``
        """
        return self.put(path, **kw)

    def set_api_key(self, api_key):
        self._api_key = api_key
        self._subdomain = None
        self.headers.update({
            'Authorization': 'Token token='+api_key,
        })

    @property
    def subdomain(self):
        """
        Subdomain of the PagerDuty account of the API access token.

        :type: str or None
        """
        if not hasattr(self, '_subdomain') or self._subdomain is None:
            try:
                url = self.rget('users', params={'limit':1})[0]['html_url']
                self._subdomain = url.split('/')[2].split('.')[0]
            except PDClientError as e:
                self.log.error("Failed to obtain subdomain; encountered error.")
                self._subdomain = None
                raise e
        return self._subdomain

    @property
    def total_call_count(self):
        """The total number of API calls made by this instance."""
        return sum(self.api_call_counts.values())

    @property
    def total_call_time(self):
        """The total time spent making API calls."""
        return sum(self.api_time.values())

    @property
    def trunc_token(self):
        """Truncated token for secure display/identification purposes."""
        return last_4(self.token)

class PDClientError(Exception): 
    """
    General API errors base class.
    """

    response = None
    """
    The HTTP response object, if a response was successfully received.

    In the case of network errors, this property will be None.
    """

    def __init__(self, message, response=None):
        self.msg = message
        self.response = response
        super(PDClientError, self).__init__(message)
