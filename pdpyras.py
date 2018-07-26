
# Copyright (c) PagerDuty.
# See LICENSE for details.

import logging
import time

from copy import deepcopy

import requests
from urllib3.connection import ConnectionError as Urllib3Error
from requests.exceptions import ConnectionError as RequestsError

__version__ = '1.0.0'

class APISession(requests.Session):
    """
    PagerDuty REST API session

    A ``requests.Session`` object, but with a few modifications:

    - The client will reattempt the request if a network error is encountered
    - When making requests, headers specified ad-hoc in calls to HTTP verb
      functions will not replace, but will be merged with, default headers.
    - The reqeust URL, if it doesn't already start with the REST API base URL,
      will be prepended with the default REST API base URL.
    - It will only perform GET, POST, PUT and DELETE requests, and will raise
      PDClientError for any other HTTP verbs.

    :param token: REST API access token to use for HTTP requests
    :param name: Optional name identifier for logging. If unspecified or
        ``None``, it will be the last four characters of the REST API token.
    :param default_from: Email address of a valid PagerDuty user to use in
        API requests by default as the ``From`` header (see: `HTTP Request
        Headers`_)
    :type token: str
    :type name: str or None
    :type default_from: str or None

    :members:
    """

    api_call_counts = None 
    """A dict object recording Number of API calls per endpoint"""

    api_time = None
    """A dict object recording the total time of API calls to each endpoint"""

    default_from = None
    """The default value to use as the ``From`` request header"""

    default_page_size = 100
    """
    This will be the default number of results requested in each page when
    iterating/querying an index (the ``limit`` parameter). See: `pagination`_.
    """

    log = None
    """A ``logging.Logger`` object for printing messages."""

    max_attempts = 3
    """
    The number of times that connecting to the API will be attempted before
    treating the failure as non-transient; a :class:`PDClientError` exception
    will be raised if this happens.
    """

    parent = None
    """The ``super`` object (`requests.Session`_)"""

    sleep_timer = 1.5
    """
    Default initial cooldown time factor for API rate limiting and transient
    network errors. Each time that the request makes a followup request, there
    will be a delay in seconds equal to this number times ``sleep_timer_base``
    to the power of how many attempts have already been made so far.
    """

    sleep_timer_base = 2
    """
    After each retry, the time to sleep before reattempting the API connection
    and request will increase by a factor of this amount.
    """

    url = 'https://api.pagerduty.com'
    """Base URL of the REST API"""

    def __init__(self, token, name=None, default_from=None):
        if not (type(token) is str and token):
            raise ValueError("API token must be a non-empty string.")
        self.api_call_counts = {}
        self.api_time = {}
        self.parent = super(APISession, self)
        self.parent.__init__()
        self.token = token
        self.default_from = default_from
        if type(name) is str and name:
            my_name = name
        else:
            my_name = "*"+token[-4:]
        self.log = logging.getLogger('pdpyras.APISession(%s)'%my_name)
        self.headers.update({
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def find(self, resource_name, query, attribute='name', params=None):
        """
        Finds an object of a given resource exactly matching a query.

        Will query a given `resource index`_ endpoint using the ``query``
        parameter supported by most indexes.

        Returns a dict if a result is found. The structure will be that of an
        entry in the index endpoint schema's array of results. Otherwise, it
        will return `None` if no result is found or an error is encountered.

        :param resource_name:
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
        :type resource_name: str
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
        obj_iter = self.iter_all(resource_name, params=query_params)
        return next(iter(filter(equiv, obj_iter)), None)

    def iter_all(self, path, params=None, paginate=True, item_hook=None,
            total=False):
        """
        Iterator for the contents of an index endpoint

        Automatically paginates and yields the results in each page, until all
        matching results have been yielded.

        Each yielded value is a dict object representing a result returned from
        the index. For example, if requesting the ``/users`` endpoint, each
        yielded value will be an entry of the ``users`` array property in the
        response; see: `List Users
        <https://v2.developer.pagerduty.com/v2/page/api-reference#!/Users/get_users>`_

        :param path:
            The index endpoint/URL to use. 
        :param params:
            Additional URL parameters to include.
        :param paginate:
            If True, use `pagination`_ to get through all available results. If
            False, ignore / don't page through more than the first 100 results.
            Useful for special index endpoints that don't fully support
            pagination yet, i.e. "nested" endpoints like
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
        :rtype: dict
        """
        # Resource name:
        r_name = path.split('?')[0].split('/')[-1]
        # Parameters to send:
        data = {}
        if paginate:
            # retrieve 100 at a time unless otherwise specified
            data['limit'] = self.default_page_size
        if total:
            data['total'] = 1
        if params is not None:
            # Override defaults with values given
            data.update(params)
        more = True
        offset = 0
        n = 0
        while more: # Paginate through all results
            if paginate:
                data['offset'] = offset
            r = self.get(path, params=data.copy())
            if not r.ok:
                self.log.warn("Stopping iteration on endpoint \"%s\"; API "
                    "responded with non-success status %d", path, r.status_code)
                break
            try:
                response = r.json()
            except ValueError: 
                self.log.warn("Stopping iteration on endpoint %s; API "
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

    def profile(self, method, response, suffix=None):
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
        key = self.profiler_key(method, response.url.split('?')[0], suffix)
        self.api_call_counts.setdefault(key, 0)
        self.api_time.setdefault(key, 0.0)
        self.api_call_counts[key] += 1
        self.api_time[key] += response.elapsed.total_seconds()

    def profiler_key(self, method, path, suffix=None):
        """
        Generates a fixed-format "key" to classify a request URL for profiling.

        Returns a string that will have all instances of IDs replaced with
        ``{id}``, and will begin with the method in lower case followed by a
        colon, i.e. ``get:escalation_policies/{id}``

        :param path: str
            The path/URI to classify
        :param method:
            The reqeust method
        :param suffix:
            Optional suffix to append to the key
        :type param: str
        :type method: str
        :type suffix: str
        :rtype: str
        """
        path_nodes = path.replace(self.url, '').lstrip('/').split('/')
        my_suffix = "" if suffix is None else "#"+suffix 
        node_type = '{id}'
        sub_node_type = '{index}'
        if len(path_nodes) < 3:
            # Basic / root level resource, i.e. list, create, view, update
            if len(path_nodes) == 1:
                node_type = '{index}'
            resource = path_nodes[0].split('?')[0]
            key = '%s:%s/%s%s'%(method.lower(), resource, node_type, my_suffix)
        else:
            # It's an endpoint like one of the following 
            # /{resource}/{id}/{sub-resource}
            # We're interested in {resource} and {sub_resource}.
            # More deeply-nested endpoints are not yet known to exist.
            sub_resource = path_nodes[2].split('?')[0]
            if len(path_nodes) == 4:
                sub_node_type = '{id}'
            key = '%s:%s/%s/%s/%s%s'%(method.lower(), path_nodes[0], node_type,
                sub_resource, sub_node_type, my_suffix)
        return key


    def request(self, method, url, **kwargs):
        """
        Make a generic PagerDuty v2 REST API request. 
        
        Returns a `requests.Response`_ object.

        :param method:
            The request method to use. Case-insensitive. May be one of get, put,
            post or delete.
        :param url:
            The path/URL to request. If it does not start with the PagerDuty
            REST API's base URL, the base URL will be prepended.
        :param \*\*kwargs:
            Additional keyword arguments to pass to `requests.Session.request
            <http://docs.python-requests.org/en/master/api/#requests.Session.request>`_
        :type method: str
        :type url: str
        :rtype: `requests.Response`_
        """
        sleep_timer = self.sleep_timer
        attempts = 0
        method = method.upper()
        if method not in ('GET', 'POST', 'PUT', 'DELETE'):
            raise PDClientError(
                "Method %s not supported by PagerDuty REST API."%method
            )
        # Prepare headers
        req_kw = deepcopy(kwargs)
        my_headers = self.headers.copy()
        if self.default_from is not None:
            my_headers['From'] = self.default_from
        if method in ('POST', 'PUT'):
            my_headers['Content-Type'] = 'application/json'
        # Merge, but do not replace, any headers specified in keyword arguments:
        if 'headers' in kwargs:
            my_headers.update(kwargs['headers'])
        req_kw.update({'headers': my_headers, 'stream': False})
        # Compose/normalize URL whether or not path is already a complete URL
        if url.startswith('https://api.pagerduty.com'):
            my_url = url
        else:
            my_url = self.url + "/" + url.lstrip('/')
        # Make the request (and repeat w/cooldown if the rate limit is reached):
        while True:
            try:
                response = self.parent.request(method, my_url, **req_kw)
                self.profile(method.lower(), response)
            except (Urllib3Error, RequestsError) as e:
                attempts += 1
                if attempts > self.max_attempts:
                    raise PDClientError("Non-transient network error; exceeded "
                        "maximum number of attempts (%d) to connect to the REST"
                        " API."%self.max_attempts)
                sleep_timer *= self.sleep_timer_base
                self.log.debug("Connection error: %s; retrying in %g seconds.",
                    e, sleep_timer)
                time.sleep(sleep_timer)
                continue
            if response.status_code == 429:
                sleep_timer *= self.sleep_timer_base
                self.log.debug("Hit REST API rate limit (response status 429); "
                    "retrying in %g seconds", sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif response.status_code == 401:
                # Stop. Authentication failed. We shouldn't try doing any more,
                # because we'll run into problems later attempting to use the token.
                raise PDClientError("Received 401 Unauthorized response from "
                    "the REST API. The access key might not be valid.")
            else:
                return response

    @property
    def subdomain(self):
        """
        Subdomain of the PagerDuty account of the API access token.

        If the token's access level excludes viewing any users, or if an error
        occurs when retrieving, this will be False.

        :type: str or bool
        """
        if not hasattr(self, '_subdomain') or self._subdomain is None:
            try:
                url = next(self.iter_all(
                    'users', params={'limit':1}
                ))['html_url']
                self._subdomain = url.split('/')[2].split('.')[0]
            except (StopIteration, IndexError):
                self._subdomain = False
        return self._subdomain

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token
        self._subdomain = None
        self.headers.update({
            'Authorization': 'Token token='+token,
        })

    @property
    def total_call_count(self):
        return sum(self.api_call_counts.values())

    @property
    def total_call_time(self):
        return sum(self.api_time.values())

class PDClientError(Exception): 
    """
    General API client errors class.
    """
