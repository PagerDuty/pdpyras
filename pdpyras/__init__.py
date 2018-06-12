"""
===========================================
pdpyras: PagerDuty Python REST API Sessions
===========================================

A lightweight, practical REST API client for the PagerDuty REST API.

This library supplies a class ``APISession`` extending the class
``requests.Session`` from the Requests_ library. This has the means to handle
the most common tasks associated with accessing the PagerDuty REST API in a
succinct manner.

Its intention is to be a practical and efficient abstraction of PagerDuty REST
API access with minimal differences on top of the underlying HTTP library. This
makes it ideal to use as the foundation of anything from a feature-rich REST API
client library to a quick-and-dirty API script.

Higher-level features, i.e. model classes for handling the particulars of any
given resource type, are left to the end user to develop as they see fit.

Features
--------
- HTTP connection persistence for more efficient API requests
- Automatic cooldown/reattempt for rate limiting and transient network issues
- Inclusion of required headers for PagerDuty REST API requests
- Iteration over `resource index`_ endpoints with automatic pagination
- Retrieval of individual objects matching a query
- API request profiling
- It gets the job done without getting in the way.

Usage
-----

**Example 1:** get a user:

::
  import pdpyras
  api_token = 'your-token-here'
  session = pdpyras.APISession(api_token)
  response = session.get('/users/PABC123')
  if response.ok:
    user = response.json()['user']

**Example 2:** iterate over all users and print their ID, email and name:

::
  import pdpyras
  api_token = 'your-token-here'
  session = pdpyras.APISession(api_token)
  for user in session.iter_all('/users'):
    print(user['id'], user['email'], user['name'])

Resources
---------
.. _pagination: https://v2.developer.pagerduty.com/docs/pagination
.. _Requests: http://docs.python-requests.org/en/master/
.. _`resource index`: https://v2.developer.pagerduty.com/docs/endpoints#resources-index
"""

import logging
import time

from copy import deepcopy
from urllib3.connection import ConnectionError

import requests

__version__ = '1.0a'

_url = "https://api.pagerduty.com"

class PDClientError(Exception): 
    """
    General API client errors 
    """

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

    Attributes
    ----------
    api_call_counts : dict
    default_page_size : int
        Default value for the ``limit`` parameter; see Pagination_
    log : logging.Logger
        Logger object for printing messages
    max_attempts : int
        Number of times that connecting to the API will be attempted before
        allowing the exception from the underlying HTTP library to bubble up 
    parent : requests.Session
        The ``super`` object
    sleep_timer : float
        Default initial cooldown time factor for API rate limiting and transient
        network errors. Each time that the request makes a followup request,
        there will be a delay in seconds equal to this number times
        ``sleep_timer_base`` to the power of how many attempts have already been
        made so far.
    sleep_timer_base : float
        After each retry, the time to sleep before reattempting the API
        connection and request will increase by a factor of this amount.
    subdomain : str
        The subdomain of the account corresponding to the API token in use with
        this session.
    token : str
        The API access token.
    total_call_counts : int
        Total number of API calls made by the current session object.
    total_call_time : float
        Total time spent making API requests.
    url : str
        Base URL of the API. Can be adjusted for functional tests with a
        different host.
    """

    api_call_counts = None
    api_time = None
    default_page_size = 100
    log = None
    max_attempts = 5
    parent = None
    sleep_timer = 1.5
    sleep_timer_base = 2
    url = 'https://api.pagerduty.com'

    def __init__(self, token, name=None):
        """
        Constructor that sets defaults for API requests for a given API token.

        token : str
            REST API access token to use for HTTP requests
        name : `str`
            Optional name identifier for logging. If unspecified, it will be the
            last four characters of the REST API token.
        """
        if not (type(token) is str and token):
            raise ValueError("API token must be a non-empty string.")
        self.api_call_counts = {}
        self.api_time = {}
        self.parent = super(APISession, self)
        self.parent.__init__()
        self.token = token
        if type(name) is str and name:
            my_name = name
        else:
            my_name = token[:-4]
        self.log = logging.getLogger('pdpyras.APISession(%s)'%my_name)
        self.headers.update({
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def find(self, resource_name, query, attribute='name', params=None):
        """
        Finds an object of a given resource exactly matching a query.

        Will query a given `resource index`_ endpoint using the ``query``
        parameter supported by most indexes.

        Parameters
        ----------
        resource_name : str
            The name of the resource to query, i.e. 
        query : str
            The value to use in the query_ parameter
        str : attribute
            The property of results to compare against the query value when
            searching for an exact match; default is ``name``, but when
            searching for user by email (for example) it can be ``email``
        params : dict
            Dictionary of optional additional parameters to use when querying

        Returns
        -------
        dict
            If a result is found, it will be the entry in the list object of
            results from the resource's `index endpoint
        None
            If no result is found
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

    def iter_all(self, path, params=None, paginate=True, item_hook=None):
        """
        Generator function for iteration over all results from an index endpoint

        Automatically paginates and yields the results in each page, until all
        results have been yielded or an error occurs.

        Parameters
        ----------
        path : str
            The index endpoint/URL to use. 
        params : dict
            Additional URL parameters to include.
        paginate : bool
            If True, employ pagination to get through all available results.  If
            False, ignore / don't page through more than the first 100 results.
            Useful for special index endpoints that don't fully support
            pagination yet, i.e. "nested" endpoints like
            `/users/{id}/contact_methods` and `/services/{id}/integrations`
        item_hook : obj
            Callable that will be invoked for each iteration, ie. for printing
            progress.

        Yields
        ------
        dict
            Each result object returned from the index. For example, if
            requesting the ``/users`` endpoint, each yielded value will be an
            entry of the ``users`` array property in the response; see:
            `List Users<https://v2.developer.pagerduty.com/v2/page/api-reference#!/Users/get_users>`_
        """
        # Resource name:
        r_name = path.split('?')[0].split('/')[-1]
        # Parameters to send:
        data = {}
        if paginate:
            # retrieve 100 at a time unless otherwise specified
            data.update({'limit': self.default_page_size, 'total': 1}) 
        if params is not None:
            data.update(params)
        more = True
        offset = 0
        n = 0
        while more: # Paginate through all results
            if paginate:
                data['offset'] = offset
            r = self.get(path, params=data.copy())
            if not r.ok:
                self.log.debug("Stopping iteration on endpoint %s; API "
                    "responded with non-success status %d", path,
                    r.response_code)
                raise StopIteration
            try:
                response = r.json()
            except ValueError: 
                self.log.debug("Stopping iteration on endpoint %s; API "
                    "responded with invalid JSON.", path)
                raise StopIteration
            if 'limit' in response:
                data['limit'] = response['limit']
            more = False
            total = None
            if paginate:
                if 'more' in response:
                    more = response['more']
                else:
                    self.log.debug("Pagination is enabled in iteration, but the" 
                        " index endpoint %s responded with no \"more\" property"
                        " in the response. Only the first page of results, "
                        "however many can be gotten, will be included.", path)
                if 'total' in response:
                    total = response['total']
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
                    item_hook(result, n, total)
                yield result

    def profile(self, method, response, suffix=None):
        """
        Records performance information about the API call

        Parameters
        ----------
        method : str
            Method of the request
        response : requests.Response
            Response object
        suffix : str
            Optional suffix to append to the key
        """
        key = self.profiler_key(method, response.url.split('?')[0], suffix)
        self.api_call_counts.setdefault(key, 0)
        self.api_time.setdefault(key, 0.0)
        self.api_call_counts[key] += 1
        self.api_time[key] += response.elapsed.total_seconds()

    def profiler_key(self, method, path, suffix=None):
        """
        Generates a fixed-format "key" to classify a request URL for profiling 

        Parameters
        ----------
        path : str
            The path/URI to classify
        method : str
            The reqeust method
        suffix : str
            Optional suffix to append to the key

        Returns
        -------
        str
            The profiler key. This will have all instances of IDs replaced with
            ``{id}``, and will begin with the method in lower case followed by a
            colon.
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

        Parameters
        ----------
        method : str
            The request method to use. Case-insensitive. May be one of get, put,
            post or delete.
        url : str
            The path/URL to request. If it does not start with the PagerDuty
            REST API's base URL, the base URL will be prepended.
        **kwargs
            Additional keyword arguments to pass to ``requests.Session.request``

        Returns
        -------
        requests.Response
            The response object
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
        if method in ('POST', 'PUT'):
            my_headers.update({'Content-Type': 'application/json'})
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
            except ConnectionError as e:
                attempts += 1
                if attempts > self.max_attempts:
                    raise PDClientError("Non-transient network error; exceeded "
                        "maximum number of attempts (%d) to connect to the REST"
                        " API.", self.max_attempts)
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
        Subdomain of the PagerDuty account of the API access token (getter)

        If the token's access level excludes viewing any users, or if an error
        occurs, this will be None.

        Returns
        -------
        str
        """
        if not hasattr(self, '_subdomain'):
            try:
                url = next(self.iter_all(
                    'users', params={'limit':1}
                ))['html_url']
                self._subdomain = url.split('/')[2].split('.')[0]
            except StopIteration:
                self._subdomain = None
        return self._subdomain

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token
        self.headers.update({
            'Authorization': 'Token token='+token,
        })

    @property
    def total_call_counts(self):
        """
        Total count of API calls (getter)

        Returns
        -------
        int
        """
        return sum(self.api_call_counts.values())

    @property
    def total_call_time(self):
        """
        Total time spent making API calls (getter)

        Returns
        -------
        float
        """
        return sum(self.api_call_counts.values())

#########################
### Utility Functions ### 
#########################

def object_type(resource_name):
    """
    Derives an object type from a resource name

    Parameters
    ----------
    resource_name : str
        Resource name, i.e. would be ``users`` for the URL
        ``https://api.pagerduty.com/users``

    Returns
    -------
    str
    """
    if resource_name == 'escalation_policies':
        return 'escalation_policy'
    else:
        return resource_name.rstrip('s')

def resource_name(object_type):
    """
    Transforms an object type into a resource name

    Parameters
    ----------
    object_type : str
        The object type, i.e. `user` or `user_reference`

    Returns
    -------
    str
    """
    if object_type.endswith('_reference'):
        # Strip down to basic type if it's a reference
        object_type = object_type[:object_type.index('_reference')]
    if object_type == 'escalation_policy':
        return 'escalation_policies'
    else:
        return object_type+'s'


