"""
pdrac

A very basic PagerDuty REST API Client.

Serves as a convenience wrapper for the Requests package in that it handles some
of the most common tasks associated with accessing the PagerDuty REST API, and
leaves more advanced features to the end user to develop.

Features:

* Appropriate header-setting for making PagerDuty REST API calls
* TCP connection pooling & re-use for efficient API requests
* Iteration over index endpoints with automatic pagination
* Retrieval of individual objects exactly matching a query
"""

import logging
import time
from copy import deepcopy

import requests

_url = "https://api.pagerduty.com"
log = logging.getLogger(__name__)

class PDClientError(Exception): 
    """
    Error class for general API errors
    """

class APISession(requests.Session):
    """
    PagerDuty REST API session.

    Behaves as a requests.Session object, but with a few modifications:

    - When making requests, headers specified ad-hoc in calls to HTTP verb
      functions will not replace, but will be merged with, default headers.
    - The URL, if it doesn't include the schema/hostname, will be prepended with
      the API base URL.
    - It will only perform GET, POST, PUT and DELETE requests, and will raise
      PDClientError for any other HTTP verbs.
    """

    sleep_timer = 1.5 # Starting value in seconds of the rate limit cooldown
    parent = None # Proxy object for parent class

    def __init__(self, token, baseurl='https://api.pagerduty.com'):
        """
        Constructor that sets defaults for API requests for a given API token.

        :param token: REST API access token to use for HTTP requests
        """
        if not (type(token) is str and token):
            raise ValueError("API token must be a string.")
        self.parent = super(APISession, self)
        self.url = baseurl
        self.parent.__init__()
        self.headers.update({
            'Authorization': 'Token token='+token,
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def find(self, resource_name, query, attribute='name', params=None):
        """
        Finds an object of a given resource exactly matching a query.

        :param resource_name: The resource name to use as the type
        :param query: The value to use in the "query" parameter
        :param attribute: The property of results to compare against the query
            value when searching for an exact match; default is "name", but when
            searching for user by email (for example) it should be "email"
        :param params: Dictionary of optional additional parameters to use
        :return dict,None:
        """
        query_params = {}
        if params is not None:
            query_params.update(params)
        query_params.update({'query':query})
        # When determining uniqueness, web/the API doesn't care about case and
        # trailing/leading whitespace, hence:
        simplify = lambda s: s.lower().strip()
        search_term = simplify(query) 
        equiv = lambda s: simplify(s[attribute]) == search_term
        obj_iter = self.iter_all(resource_name, params=query_params)
        return next(iter(filter(equiv, obj_iter)), None)


    def get_obj(self, url, **kwargs):
        """
        Gracefully retrieve an object from the REST API.

        Returns a 2-tuple containing True or False depending on whether the API
        call succeeded, and a dictionary representing the response object (after
        JSON-decoding, if successful) and None otherwise, respectively.

        :param url: URL of the request
        :param kwargs: Keyword arguments to pass to requests.Session.get
        """
        response = self.get(url, **kwargs)
        try:
            return response.ok, response.json()
        except ValueError as e:
            # Just in case this ever happens:
            log.warn("Received invalid JSON in the response from the REST API: "
                "GET %s %d; keyword args to requests.Session.%s: %s / response "
                "text: %s", url, response.status_code, method.lower(),
                str(req_kw), response.text)
            return False, None

    def iter_all(self, path, params=None, item_hook=None, paginate=True):
        """
        Generator function that iterates over all results of an index endpoint,
        automatically paginating and yielding the results in each page.

        :param path: The index endpoint to use. This should not contain an
            interro / parameters (hard-coded into the URL); instead, the
            "params" keyword argument should be used to include them.
        :param params: Dictionary of additional parameters to include.
        :param progress: Print progress of retrieval
        :param count: Print verbose progress (show each object as retrieved)
        :param paginate: Ignore / don't page through more than the first 100
            results. Useful for non-standard index endpoints that don't fully
            support pagination yet.
        :param item_hook: Callable object to be called for each item in the
            result before yielding. Will be passed three positional arguments:
            (1) the object at the current step in iteration; (2) the number of
            the current result; (3) the total number of results. The third
            argument will be None if the paginate argument is false.
        """
        # Resource name:
        r_name = path.split('/')[-1]
        # Parameters to send:
        data = {}
        if paginate:
            # retrieve 100 at a time unless otherwise specified
            data.update({'limit': 100, 'total': 1}) 
        if params is not None:
            data.update(params)
        more = True
        offset = 0
        n = 0
        while more: # Paginate through all results
            if paginate:
                data['offset'] = offset
            success, results = self.get_obj(path, params=data)
            if not success or results is None:
                raise StopIteration
            if 'limit' in results:
                data['limit'] = response['limit']
            more = False
            total = None
            if paginate and 'more' in response:
                more = response['more']
            elif 'more' not in response and paginate:
                log.warn("Pagination is enabled for iteration, but index "
                    "endpoint %s has no \"more\" property in the response. Only"
                    "the first page of results will be included.", path)
            if paginate:
                offset += data['limit']
            for result in response[r_name]:
                n += 1 
                if count:
                    item_hook(result, n, response['total'])
                yield result

    def request(self, method, url, **kwargs):
        """
        Make a generic PagerDuty v2 REST API request.

        :param method: The request method to use
        :param url: The path/URL to request
        :param kwargs: Keyword arguments to pass to `requests.Session.request`
        :return requests.Response: 
        """
        _url = self.url
        sleep_timer = self.sleep_timer
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
        if 'headers' in kwargs:
            # Merge, but do not replace, headers specified.
            my_headers.update(kwargs['headers'])
        req_kw.update({'headers': my_headers})
        # Compose/normalize URL whether or not path is already a complete URL
        if url[:4] == 'http':
            my_url = url
        else:
            my_url = _url + "/" + url.lstrip('/')
        # Make the request (and repeat w/cooldown if the rate limit is reached):
        while True:
            # TODO: try/catch + cooldown logic for transient network issues
            response = self.parent.request(method, my_url, **kwargs)
            # Profiling using response.elapsed.total_seconds? (TODO)
            if response.status_code == 429:
                sleep_timer = sleep_timer * 2
                log.debug("Hit REST API rate limit (response status 429); "
                    "retrying in %g seconds", sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif response.status_code == 401:
                # Stop. Authentication failed. We shouldn't try doing any more,
                # because we'll run into problems later attempting to use the token.
                raise PDClientError("Received 401 Unauthorized response from "
                    "the API. The API token provided might not be valid.")
            else:
                return response

    @property
    def subdomain(self):
        """
        Subdomain of the account to which the current API token corresponds.

        If the token's access level excludes viewing any users, or if an error
        occurs, this will be None.
        """
        if not hasattr(self, _subdomain):
            try:
                url = next(self.iter_all(
                    'users', params={'limit':1}
                ))['html_url']
                self._subdomain = url.split('/')[2].split('.')[0]
            except StopIteration:
                self._subdomain = None
        return self._subdomain
 


#########################
### Utility Functions ### 
#########################

def object_type(resource_name):
    """
    Derives an object type from a resource name

    :param resource_name: Resource name, i.e. would be `users` for the URL
        `https://api.pagerduty.com/users`
    """
    if resource_name == 'escalation_policies':
        return 'escalation_policy'
    else:
        return resource_name.rstrip('s')

def resource_name(object_type):
    """
    Transforms an object type into a resource name

    :param object_type: The object type, i.e. `user` or `user_reference`
    """
    if object_type.endswith('_reference'):
        # Strip down to basic type if it's a reference
        object_type = object_type[:object_type.index('_reference')]
    if object_type == 'escalation_policy':
        return 'escalation_policies'
    else:
        return object_type+'s'


