
# Copyright (c) PagerDuty.
# See LICENSE for details.

# Standard libraries
import logging
import sys
import time
from copy import deepcopy
from datetime import datetime
from random import random
from typing import Iterator, Union
from warnings import warn

# Upstream components on which this client is based:
from requests import Response, Session
from requests import __version__ as REQUESTS_VERSION

# HTTP client exceptions:
from urllib3.exceptions import HTTPError, PoolError
from requests.exceptions import RequestException

__version__ = '5.3.0'

#######################
### CLIENT DEFAULTS ###
#######################
ITERATION_LIMIT = 1e4
"""
The maximum position of a result in classic pagination.

The offset plus limit parameter may not exceed this number. This is enforced
server-side and is not something the client may override. Rather, this value is
used to short-circuit pagination in order to avoid a HTTP 400 error.

See: `Pagination
<https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU4-pagination>`_.
"""

TIMEOUT = 60
"""
The default timeout in seconds for any given HTTP request.

Modifying this value will not affect any preexisting API session instances.
Rather, it will only affect new instances. It is recommended to use
:attr:`PDSession.timeout` to configure the timeout for a given session.
"""

TEXT_LEN_LIMIT = 100
"""
The longest permissible length of API content to include in error messages.
"""

# List of canonical API paths
#
# Supporting a new API for entity wrapping will require adding its patterns to
# this list. If it doesn't follow standard naming conventions, it will also
# require one or more new entries in ENTITY_WRAPPER_CONFIG.
#
# To generate new definitions for CANONICAL_PATHS and
# CURSOR_BASED_PAGINATION_PATHS based on the API documentation's source code,
# use scripts/get_path_list/get_path_list.py

CANONICAL_PATHS = [
    '/{entity_type}/{id}/change_tags',
    '/{entity_type}/{id}/tags',
    '/abilities',
    '/abilities/{id}',
    '/addons',
    '/addons/{id}',
    '/analytics/metrics/incidents/all',
    '/analytics/metrics/incidents/services',
    '/analytics/metrics/incidents/teams',
    '/analytics/raw/incidents',
    '/analytics/raw/incidents/{id}',
    '/analytics/raw/incidents/{id}/responses',
    '/audit/records',
    '/automation_actions/actions',
    '/automation_actions/actions/{id}',
    '/automation_actions/actions/{id}/invocations',
    '/automation_actions/actions/{id}/services',
    '/automation_actions/actions/{id}/services/{service_id}',
    '/automation_actions/actions/{id}/teams',
    '/automation_actions/actions/{id}/teams/{team_id}',
    '/automation_actions/invocations',
    '/automation_actions/invocations/{id}',
    '/automation_actions/runners',
    '/automation_actions/runners/{id}',
    '/automation_actions/runners/{id}/teams',
    '/automation_actions/runners/{id}/teams/{team_id}',
    '/business_services',
    '/business_services/{id}',
    '/business_services/{id}/account_subscription',
    '/business_services/{id}/subscribers',
    '/business_services/{id}/supporting_services/impacts',
    '/business_services/{id}/unsubscribe',
    '/business_services/impactors',
    '/business_services/impacts',
    '/business_services/priority_thresholds',
    '/change_events',
    '/change_events/{id}',
    '/customfields/fields',
    '/customfields/fields/{field_id}',
    '/customfields/fields/{field_id}/field_options',
    '/customfields/fields/{field_id}/field_options/{field_option_id}',
    '/customfields/fields/{field_id}/schemas',
    '/customfields/schema_assignments',
    '/customfields/schema_assignments/{id}',
    '/customfields/schemas',
    '/customfields/schemas/{schema_id}',
    '/customfields/schemas/{schema_id}/field_configurations',
    '/customfields/schemas/{schema_id}/field_configurations/{field_configuration_id}',
    '/escalation_policies',
    '/escalation_policies/{id}',
    '/escalation_policies/{id}/audit/records',
    '/event_orchestrations',
    '/event_orchestrations/{id}',
    '/event_orchestrations/{id}/router',
    '/event_orchestrations/{id}/unrouted',
    '/event_orchestrations/services/{id}',
    '/event_orchestrations/services/{id}/active',
    '/extension_schemas',
    '/extension_schemas/{id}',
    '/extensions',
    '/extensions/{id}',
    '/extensions/{id}/enable',
    '/incident_workflows',
    '/incident_workflows/{id}',
    '/incident_workflows/{id}/instances',
    '/incident_workflows/actions',
    '/incident_workflows/actions/{id}',
    '/incident_workflows/triggers',
    '/incident_workflows/triggers/{id}',
    '/incident_workflows/triggers/{id}/services',
    '/incident_workflows/triggers/{trigger_id}/services/{service_id}',
    '/incidents',
    '/incidents/{id}',
    '/incidents/{id}/alerts',
    '/incidents/{id}/alerts/{alert_id}',
    '/incidents/{id}/business_services/{business_service_id}/impacts',
    '/incidents/{id}/business_services/impacts',
    '/incidents/{id}/field_values',
    '/incidents/{id}/field_values/schema',
    '/incidents/{id}/log_entries',
    '/incidents/{id}/merge',
    '/incidents/{id}/notes',
    '/incidents/{id}/outlier_incident',
    '/incidents/{id}/past_incidents',
    '/incidents/{id}/related_change_events',
    '/incidents/{id}/related_incidents',
    '/incidents/{id}/responder_requests',
    '/incidents/{id}/snooze',
    '/incidents/{id}/status_updates',
    '/incidents/{id}/status_updates/subscribers',
    '/incidents/{id}/status_updates/unsubscribe',
    '/incidents/count',
    '/license_allocations',
    '/licenses',
    '/log_entries',
    '/log_entries/{id}',
    '/log_entries/{id}/channel',
    '/maintenance_windows',
    '/maintenance_windows/{id}',
    '/notifications',
    '/oncalls',
    '/paused_incident_reports/alerts',
    '/paused_incident_reports/counts',
    '/priorities',
    '/response_plays',
    '/response_plays/{id}',
    '/response_plays/{response_play_id}/run',
    '/rulesets',
    '/rulesets/{id}',
    '/rulesets/{id}/rules',
    '/rulesets/{id}/rules/{rule_id}',
    '/schedules',
    '/schedules/{id}',
    '/schedules/{id}/audit/records',
    '/schedules/{id}/overrides',
    '/schedules/{id}/overrides/{override_id}',
    '/schedules/{id}/users',
    '/schedules/preview',
    '/service_dependencies/associate',
    '/service_dependencies/business_services/{id}',
    '/service_dependencies/disassociate',
    '/service_dependencies/technical_services/{id}',
    '/services',
    '/services/{id}',
    '/services/{id}/audit/records',
    '/services/{id}/change_events',
    '/services/{id}/integrations',
    '/services/{id}/integrations/{integration_id}',
    '/services/{id}/rules',
    '/services/{id}/rules/{rule_id}',
    '/status_dashboards',
    '/status_dashboards/{id}',
    '/status_dashboards/{id}/service_impacts',
    '/status_dashboards/url_slugs/{url_slug}',
    '/status_dashboards/url_slugs/{url_slug}/service_impacts',
    '/tags',
    '/tags/{id}',
    '/tags/{id}/users',
    '/tags/{id}/teams',
    '/tags/{id}/escalation_policies',
    '/teams',
    '/teams/{id}',
    '/teams/{id}/audit/records',
    '/teams/{id}/escalation_policies/{escalation_policy_id}',
    '/teams/{id}/members',
    '/teams/{id}/notification_subscriptions',
    '/teams/{id}/notification_subscriptions/unsubscribe',
    '/teams/{id}/users/{user_id}',
    '/templates',
    '/templates/{id}',
    '/templates/{id}/render',
    '/users',
    '/users/{id}',
    '/users/{id}/audit/records',
    '/users/{id}/contact_methods',
    '/users/{id}/contact_methods/{contact_method_id}',
    '/users/{id}/license',
    '/users/{id}/notification_rules',
    '/users/{id}/notification_rules/{notification_rule_id}',
    '/users/{id}/notification_subscriptions',
    '/users/{id}/notification_subscriptions/unsubscribe',
    '/users/{id}/oncall_handoff_notification_rules',
    '/users/{id}/oncall_handoff_notification_rules/{oncall_handoff_notification_rule_id}',
    '/users/{id}/sessions',
    '/users/{id}/sessions/{type}/{session_id}',
    '/users/{id}/status_update_notification_rules',
    '/users/{id}/status_update_notification_rules/{status_update_notification_rule_id}',
    '/users/me',
    '/vendors',
    '/vendors/{id}',
    '/webhook_subscriptions',
    '/webhook_subscriptions/{id}',
    '/webhook_subscriptions/{id}/enable',
    '/webhook_subscriptions/{id}/ping',
]
"""
Explicit list of supported canonical REST API v2 paths

:meta hide-value:
"""

CURSOR_BASED_PAGINATION_PATHS = [
    '/audit/records',
    '/automation_actions/actions',
    '/automation_actions/runners',
    '/escalation_policies/{id}/audit/records',
    '/incident_workflows/actions',
    '/incident_workflows/triggers',
    '/schedules/{id}/audit/records',
    '/services/{id}/audit/records',
    '/teams/{id}/audit/records',
    '/users/{id}/audit/records',
]
"""
Explicit list of paths that support cursor-based pagination

:meta hide-value:
"""

ENTITY_WRAPPER_CONFIG = {
    # Analytics
    '* /analytics/metrics/incidents/all': None,
    '* /analytics/metrics/incidents/services': None,
    '* /analytics/metrics/incidents/teams': None,
    '* /analytics/raw/incidents': None,
    '* /analytics/raw/incidents/{id}': None,
    '* /analytics/raw/incidents/{id}/responses': None,

    # Automation Actions
    'POST /automation_actions/actions/{id}/invocations': (None,'invocation'),

    # Paused Incident Reports
    'GET /paused_incident_reports/alerts': 'paused_incident_reporting_counts',
    'GET /paused_incident_reports/counts': 'paused_incident_reporting_counts',

    # Business Services
    '* /business_services/{id}/account_subscription': None,
    'POST /business_services/{id}/subscribers': ('subscribers', 'subscriptions'),
    'POST /business_services/{id}/unsubscribe': ('subscribers', None),
    '* /business_services/priority_thresholds': None,
    'GET /business_services/impacts': 'services',
    'GET /business_services/{id}/supporting_services/impacts': 'services',

    # Change Events
    'POST /change_events': None, # why not just use ChangeEventsAPISession?
    'GET /incidents/{id}/related_change_events': 'change_events',

    # Event Orchestrations
    '* /event_orchestrations': 'orchestrations',
    '* /event_orchestrations/{id}': 'orchestration',
    '* /event_orchestrations/{id}/router': 'orchestration_path',
    '* /event_orchestrations/{id}/unrouted': 'orchestration_path',
    '* /event_orchestrations/services/{id}': 'orchestration_path',
    '* /event_orchestrations/services/{id}/active': None,

    # Extensions
    'POST /extensions/{id}/enable': (None, 'extension'),

    # Incidents
    'PUT /incidents': 'incidents', # Multi-update
    'PUT /incidents/{id}/merge': ('source_incidents', 'incident'),
    'POST /incidents/{id}/responder_requests': (None, 'responder_request'),
    'POST /incidents/{id}/snooze': (None, 'incident'),
    'POST /incidents/{id}/status_updates': (None, 'status_update'),
    'POST /incidents/{id}/status_updates/subscribers': ('subscribers', 'subscriptions'),
    'POST /incidents/{id}/status_updates/unsubscribe': ('subscribers', None),
    'GET /incidents/{id}/business_services/impacts': 'services',
    'PUT /incidents/{id}/business_services/{business_service_id}/impacts': None,

    # Incident Workflows
    'POST /incident_workflows/{id}/instances': 'incident_workflow_instance',
    'POST /incident_workflows/triggers/{id}/services': ('service', 'trigger'),

    # Response Plays
    'POST /response_plays/{response_play_id}/run': None, # (deprecated)

    # Schedules
    'POST /schedules/{id}/overrides': ('overrides', None),

    # Service Dependencies
    'POST /service_dependencies/associate': 'relationships',

    # Webhooks
    'POST /webhook_subscriptions/{id}/enable': (None, 'webhook_subscription'),
    'POST /webhook_subscriptions/{id}/ping': None,

    # Status Dashboards
    'GET /status_dashboards/{id}/service_impacts': 'services',
    'GET /status_dashboards/url_slugs/{url_slug}': 'status_dashboard',
    'GET /status_dashboards/url_slugs/{url_slug}/service_impacts': 'services',

    # Tags
    'POST /{entity_type}/{id}/change_tags': None,

    # Teams
    'PUT /teams/{id}/escalation_policies/{escalation_policy_id}': None,
    'POST /teams/{id}/notification_subscriptions': ('subscribables', 'subscriptions'),
    'POST /teams/{id}/notification_subscriptions/unsubscribe': ('subscribables', None),
    'PUT /teams/{id}/users/{user_id}': None,
    'GET /teams/{id}/notification_subscriptions': 'subscriptions',

    # Templates
    'POST /templates/{id}/render': None,

    # Users
    '* /users/{id}/notification_subscriptions': ('subscribables', 'subscriptions'),
    'POST /users/{id}/notification_subscriptions/unsubscribe': ('subscribables', None),
    'GET /users/{id}/sessions': 'user_sessions',
    'GET /users/{id}/sessions/{type}/{session_id}': 'user_session',
    'GET /users/me': 'user',
} #: :meta hide-value:
"""
Wrapped entities antipattern handling configuration.

When trying to determine the entity wrapper name, this dictionary is first
checked for keys that apply to a given request method and canonical API path
based on a matching logic. If no keys are found that match, it is assumed that
the API endpoint follows classic entity wrapping conventions, and the wrapper
name can be inferred based on those conventions (see
:attr:`infer_entity_wrapper`). Any new API that does not follow these
conventions should therefore be given an entry in this dictionary in order to
properly support it for entity wrapping.

Each of the keys should be a capitalized HTTP method (or ``*`` to match any
method), followed by a space, followed by a canonical path i.e. as returned by
:attr:`canonical_path` and included in :attr:`CANONICAL_PATHS`. Each value
is either a tuple with request and response body wrappers (if they differ), a
string (if they are the same for both cases) or ``None`` (if wrapping is
disabled and the data is to be marshaled or unmarshaled as-is). Values in tuples
can also be None to denote that either the request or response is unwrapped.

An endpoint, under the design logic of this client, is said to have entity
wrapping if the body (request or response) has only one property containing
the content requested or transmitted, apart from properties used for
pagination. If there are any secondary content-bearing properties (other than
those used for pagination), entity wrapping should be disabled to avoid
discarding those properties from responses or preventing the use of those
properties in request bodies.

:meta hide-value:
"""


####################
### URL HANDLING ###
####################

def canonical_path(base_url: str, url: str) -> str:
    """
    The canonical path from the API documentation corresponding to a URL

    This is used to identify and classify URLs according to which particular API
    within REST API v2 it belongs to.

    Explicitly supported canonical paths are defined in the list
    :attr:`CANONICAL_PATHS` and are the path part of any given API's URL. The
    path for a given API is what is shown at the top of its reference page, i.e.
    ``/users/{id}/contact_methods`` for retrieving a user's contact methods
    (GET) or creating a new one (POST).

    :param base_url: The base URL of the API
    :param url: A non-normalized URL (a path or full URL)
    :returns:
        The canonical REST API v2 path corresponding to a URL.
    """
    full_url = normalize_url(base_url, url)
    # Starting with / after hostname before the query string:
    url_path = full_url.replace(base_url.rstrip('/'), '').split('?')[0]
    # Root node (blank) counts so we include it:
    n_nodes = url_path.count('/')
    # First winnow the list down to paths with the same number of nodes:
    patterns = list(filter(
        lambda p: p.count('/') == n_nodes,
        CANONICAL_PATHS
    ))
    # Match against each node, skipping index zero because the root node always
    # matches, and using the adjusted index "j":
    for i, node in enumerate(url_path.split('/')[1:]):
        j = i+1
        patterns = list(filter(
            lambda p: p.split('/')[j] == node or is_path_param(p.split('/')[j]),
            patterns
        ))
        # Don't break early if len(patterns) == 1, but require an exact match...

    if len(patterns) == 0:
        raise URLError(f"URL {url} does not match any canonical API path " \
            'supported by this client.')
    elif len(patterns) > 1:
        # If there's multiple matches but one matches exactly, return that.
        if url_path in patterns:
            return url_path

        # ...otherwise this is ambiguous.
        raise Exception(f"Ambiguous URL {url} matches more than one " \
            "canonical path pattern: "+', '.join(patterns)+'; this is likely ' \
            'a bug.')
    else:
        return patterns[0]

def endpoint_matches(endpoint_pattern: str, method: str, path: str) -> bool:
    """
    Whether an endpoint (method and canonical path) matches a given pattern

    This is the filtering logic  used for finding the appropriate entry in
    :attr:`ENTITY_WRAPPER_CONFIG` to use for a given method and API path.

    :param endpoint_pattern:
        The endpoint pattern in the form ``METHOD PATH`` where ``METHOD`` is the
        HTTP method in uppercase or ``*`` to match all methods, and ``PATH`` is
        a canonical API path.
    :param method:
        The HTTP method.
    :param path:
        The canonical API path (i.e. as returned by :func:`canonical_path`)
    :returns:
        True or False based on whether the pattern matches the endpoint
    """
    return (
        endpoint_pattern.startswith(method.upper()) \
            or endpoint_pattern.startswith('*')
    ) and endpoint_pattern.endswith(f" {path}")

def is_path_param(path_node: str) -> bool:
    """
    Whether a part of a canonical path represents a variable parameter

    :param path_node: The node (value between slashes) in the path
    :returns:
        True if the node is an arbitrary variable, False if it is a fixed value
    """
    return path_node.startswith('{') and path_node.endswith('}')

def normalize_url(base_url: str, url: str) -> str:
    """
    Normalize a URL to a complete API URL.

    The ``url`` argument may be a path relative to the base URL or a full URL.

    :param url: The URL to normalize
    :param baseurl:
        The base API URL, excluding any trailing slash, i.e.
        "https://api.pagerduty.com"
    :returns: The full API endpoint URL
    """
    if url.startswith(base_url):
        return url
    elif not (url.startswith('http://') or url.startswith('https://')):
        return base_url.rstrip('/') + "/" + url.lstrip('/')
    else:
        raise URLError(
            f"URL {url} does not start with the API base URL {base_url}"
        )

#######################
### ENTITY WRAPPING ###
#######################

def entity_wrappers(method: str, path: str) -> tuple:
    """
    Obtains entity wrapping information for a given endpoint (path and method)

    :param method: The HTTP method
    :param path: A canonical API path i.e. as returned by ``canonical_path``
    :returns:
        A 2-tuple. The first element is the wrapper name that should be used for
        the request body, and the second is the wrapper name to be used for the
        response body. For either elements, if ``None`` is returned, that
        signals to disable wrapping and pass the user-supplied request body or
        API response body object unmodified.
    """
    m = method.upper()
    endpoint = "%s %s"%(m, path)
    match = list(filter(
        lambda k: endpoint_matches(k, m, path),
        ENTITY_WRAPPER_CONFIG.keys()
    ))

    if len(match) == 1:
        # Look up entity wrapping info from the global dictionary and validate:
        wrapper = ENTITY_WRAPPER_CONFIG[match[0]]
        invalid_config_error = 'Invalid entity wrapping configuration for ' \
                    f"{endpoint}: {wrapper}; this is most likely a bug."
        if wrapper is not None and type(wrapper) not in (tuple, str):
            raise Exception(invalid_config_error)
        elif wrapper is None or type(wrapper) is str:
            # Both request and response have the same wrapping at this endpoint.
            return (wrapper, wrapper)
        elif type(wrapper) is tuple and len(wrapper) == 2:
            # Endpoint uses different wrapping for request and response bodies.
            #
            # Both elements must be either str or None. The first element is the
            # request body wrapper and the second is the response body wrapper.
            # If a value is None, that indicates that the request or response
            # value should be encoded and decoded as-is without modifications.
            if False in [w is None or type(w) is str for w in wrapper]:
                raise Exception(invalid_config_error)
            return wrapper
    elif len(match) == 0:
        # Nothing in entity wrapper config matches. In this case it is assumed
        # that the endpoint follows classic API patterns and the wrapper name
        # can be inferred from the URL and request method:
        wrapper = infer_entity_wrapper(method, path)
        return (wrapper, wrapper)
    else:
        matches_str = ', '.join(match)
        raise Exception(f"{endpoint} matches more than one pattern:" + \
            f"{matches_str}; this is most likely a bug in pdpyras.")

def infer_entity_wrapper(method: str, path: str) -> str:
    """
    Infer the entity wrapper name from the endpoint using orthodox patterns.

    This is based on patterns that are broadly applicable but not universal in
    the v2 REST API, where the wrapper name is predictable from the path and
    method. This is the default logic applied to determine the wrapper name
    based on the path if there is no explicit entity wrapping defined for the
    given path in :attr:`ENTITY_WRAPPER_CONFIG`.

    :param method: The HTTP method
    :param path: A canonical API path i.e. as returned by ``canonical_path``
    """
    m = method.upper()
    path_nodes = path.split('/')
    if is_path_param(path_nodes[-1]):
        # Singular if it's an individual resource's URL for read/update/delete
        # (named similarly to the second to last node, as the last is its ID and
        # the second to last denotes the API resource collection it is part of):
        return singular_name(path_nodes[-2])
    elif m == 'POST':
        # Singular if creating a new resource by POSTing to the index containing
        # similar resources (named simiarly to the last path node):
        return singular_name(path_nodes[-1])
    else:
        # Plural if listing via GET to the index endpoint, or doing a multi-put:
        return path_nodes[-1]

def unwrap(response: Response, wrapper) -> Union[dict, list]:
    """
    Unwraps a wrapped entity.

    :param response: The response object
    :param wrapper: The entity wrapper
    :type wrapper: str or None
    :returns:
        The value associated with the wrapper key in the JSON-decoded body of
        the response, which is expected to be a dictionary (map).
    """
    body = try_decoding(response)
    endpoint = "%s %s"%(response.request.method.upper(), response.request.url)
    if wrapper is not None:
        # There is a wrapped entity to unpack:
        bod_type = type(body)
        error_msg = f"Expected response body from {endpoint} after JSON-" \
            f"decoding to be a dictionary with a key \"{wrapper}\", but "
        if bod_type is dict:
            if wrapper in body:
                return body[wrapper]
            else:
                keys = truncate_text(', '.join(body.keys()))
                raise PDServerError(
                    error_msg + f"its keys are: {keys}",
                    response
                )
        else:
            raise PDServerError(
                error_msg + f"its type is {bod_type}.",
                response
            )
    else:
        # Wrapping is disabled for responses:
        return body

###########################
### FUNCTION DECORATORS ###
###########################

def auto_json(method):
    """
    Makes methods return the full response body object after decoding from JSON.

    Intended for use on functions that take a URL positional argument followed
    by keyword arguments and return a `requests.Response`_ object.
    """
    doc = method.__doc__
    def call(self, url, **kw):
        return try_decoding(successful_response(method(self, url, **kw)))
    call.__doc__ = doc
    return call

def requires_success(method):
    """
    Decorator that validates HTTP responses.
    """
    doc = method.__doc__
    def call(self, url, **kw):
        return successful_response(method(self, url, **kw))
    call.__doc__ = doc
    return call

def resource_url(method):
    """
    API call decorator that allows passing a resource dict as the path/URL

    Most resources returned by the API will contain a ``self`` attribute that is
    the URL of the resource itself.

    Using this decorator allows the implementer to pass either a URL/path or
    such a resource dictionary as the ``path`` argument, thus eliminating the
    need to re-construct the resource URL or hold it in a temporary variable.
    """
    doc = method.__doc__
    def call(self, resource, **kw):
        url = resource
        if type(resource) is dict and 'self' in resource: # passing an object
            url = resource['self']
        elif type(resource) is not str:
            name = method.__name__
            raise URLError(f"Value passed to {name} is not a str or dict with "
                "key 'self'")
        return method(self, url, **kw)
    call.__doc__ = doc
    return call

def wrapped_entities(method):
    """
    Automatically wrap request entities and unwrap response entities.

    Used for methods :attr:`APISession.rget`, :attr:`APISession.rpost` and
    :attr:`APISession.rput`. It makes them always return an object representing
    the resource entity in the response (whether wrapped in a root-level
    property or not) rather than the full response body. When making a post /
    put request, and passing the ``json`` keyword argument to specify the
    content to be JSON-encoded as the body, that keyword argument can be either
    the to-be-wrapped content or the full body including the entity wrapper, and
    the ``json`` keyword argument will be normalized to include the wrapper.

    Methods using this decorator will raise a :class:`PDHTTPError` with its
    ``response`` property being being the `requests.Response`_ object in the
    case of any error (as of version 4.2 this is subclassed as
    :class:`PDHTTPError`), so that the implementer can access it by catching the
    exception, and thus design their own custom logic around different types of
    error responses.

    :param method: Method being decorated. Must take one positional argument
        after ``self`` that is the URL/path to the resource, followed by keyword
        any number of keyword arguments, and must return an object of class
        `requests.Response`_, and be named after the HTTP method but with "r"
        prepended.
    :returns: A callable object; the reformed method
    """
    http_method = method.__name__.lstrip('r')
    doc = method.__doc__
    def call(self, url, **kw):
        pass_kw = deepcopy(kw) # Make a copy for modification
        path = canonical_path(self.url, url)
        endpoint = "%s %s"%(http_method.upper(), path)
        req_w, res_w = entity_wrappers(http_method, path)
        # Validate the abbreviated (or full) request payload, and automatically
        # wrap the request entity for the implementer if necessary:
        if req_w is not None and http_method in ('post', 'put') \
                and 'json' in pass_kw and req_w not in pass_kw['json']:
            pass_kw['json'] = {req_w: pass_kw['json']}

        # Make the request:
        r = successful_response(method(self, url, **pass_kw))

        # Unpack the response:
        return unwrap(r, res_w)
    call.__doc__ = doc
    return call


########################
### HELPER FUNCTIONS ###
########################

def deprecated_kwarg(deprecated_name: str, details=None):
    """
    Raises a warning if a deprecated keyword argument is used.

    :param deprecated_name: The name of the deprecated function
    :param details: An optional message to append to the deprecation message
    """
    details_msg = ''
    if details is not None:
        details_msg = f" {details}"
    warn(f"Keyword argument \"{deprecated_name}\" is deprecated.{details_msg}")

def http_error_message(r: Response, context=None) -> str:
    """
    Formats a message describing a HTTP error.

    :param r:
        The response object.
    :param context:
        A description of when the error was received, or None to not include it
    :returns:
        The message to include in the HTTP error
    """
    received_http_response = bool(r.status_code)
    endpoint = "%s %s"%(r.request.method.upper(), r.request.url)
    context_msg = ""
    if type(context) is str:
        context_msg=f" in {context}"
    if received_http_response and not r.ok:
        err_type = 'unknown'
        if r.status_code / 100 == 4:
            err_type = 'client'
        elif r.status_code / 100 == 5:
            err_type = 'server'
        tr_bod = truncate_text(r.text)
        return f"{endpoint}: API responded with {err_type} error (status " \
            f"{r.status_code}){context_msg}: {tr_bod}"
    elif not received_http_response:
        return f"{endpoint}: Network or other unknown error{context_msg}"
    else:
        return f"{endpoint}: Success (status {r.status_code}) but an " \
            f"expectation still failed{context_msg}"

def last_4(secret: str) -> str:
    """
    Truncate a sensitive value to its last 4 characters

    :param secret: text to truncate
    :returns:
        The truncated text
    """
    return '*'+str(secret)[-4:]

def plural_name(obj_type: str) -> str:
    """
    Pluralizes a name, i.e. the API name from the ``type`` property

    :param obj_type:
        The object type, i.e. ``user`` or ``user_reference``
    :returns:
        The name of the resource, i.e. the last part of the URL for the
        resource's index URL
    """
    if obj_type.endswith('_reference'):
        # Strip down to basic type if it's a reference
        obj_type = obj_type[:obj_type.index('_reference')]
    if obj_type.endswith('y'):
        # Because English
        return obj_type[:-1]+'ies'
    else:
        return obj_type+'s'

def singular_name(r_name: str) -> str:
    """
    Singularizes a name, i.e. for the entity wrapper in a POST request

    :para r_name:
        The "resource" name, i.e. "escalation_policies", a plural noun that
        forms the part of the canonical path identifying what kind of resource
        lives in the collection there, for an API that follows classic wrapped
        entity naming patterns.
    :returns:
        The singularized name
    """
    if r_name.endswith('ies'):
        # Because English
        return r_name[:-3]+'y'
    else:
        return r_name.rstrip('s')

def successful_response(r: Response, context=None) -> Response:
    """Validates the response as successful.

    Returns the response if it was successful; otherwise, raises an exception.

    :param r:
        Response object corresponding to the response received.
    :param context:
        A description of when the HTTP request is happening, for error reporting
    :returns:
        The response object, if it was successful
    """
    if r.ok and bool(r.status_code):
        return r
    elif r.status_code / 100 == 5:
        raise PDServerError(http_error_message(r, context=context), r)
    elif bool(r.status_code):
        raise PDHTTPError(http_error_message(r, context=context), r)
    else:
        raise PDClientError(http_error_message(r, context=context))

def truncate_text(text: str) -> str:
    """Truncates a string longer than :attr:`TEXT_LEN_LIMIT`

    :param text: The string to truncate if longer than the limit.
    """
    if len(text) > TEXT_LEN_LIMIT:
        return text[:TEXT_LEN_LIMIT-1]+'...'
    else:
        return text

def try_decoding(r: Response) -> Union[dict, list, str]:
    """
    JSON-decode a response body

    Returns the decoded body if successful; raises :class:`PDServerError`
    otherwise.

    :param r:
        The response object
    """
    try:
        return r.json()
    except ValueError as e:
        raise PDServerError(
            "API responded with invalid JSON: " + truncate_text(r.text),
            r,
        )

###############
### CLASSES ###
###############

class PDSession(Session):
    """
    Base class for making HTTP requests to PagerDuty APIs

    This is an opinionated wrapper of `requests.Session`_, with a few additional
    features:

    - The client will reattempt the request with auto-increasing cooldown/retry
      intervals, with attempt limits configurable through the :attr:`retry`
      attribute.
    - When making requests, headers specified ad-hoc in calls to HTTP verb
      functions will not replace, but will be merged into, default headers.
    - The request URL, if it doesn't already start with the REST API base URL,
      will be prepended with the default REST API base URL.
    - It will only perform requests with methods as given in the
      :attr:`permitted_methods` list, and will raise :class:`PDClientError` for
      any other HTTP methods.

    :param api_key:
        REST API access token to use for HTTP requests
    :param debug:
        Sets :attr:`print_debug`. Set to True to enable verbose command line
        output.
    :type token: str
    :type debug: bool
    """

    log = None
    """
    A ``logging.Logger`` object for logging messages. By default it is
    configured without any handlers and so no messages will be emitted. See
    `logger objects
    <https://docs.python.org/3/library/logging.html#logger-objects>`_
    """

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
    """
    A tuple of the methods permitted by the API which the client implements.

    For instance:

    * The REST API accepts GET, POST, PUT and DELETE.
    * The Events API and Change Events APIs only accept POST.
    """

    retry = {}
    """
    A dict defining the retry behavior for each HTTP response status code.

    Note, any value set for this class variable will not be reflected in
    instances and so it must be set separately for each instance.

    Each key in this dictionary is an int representing a HTTP response code. The
    behavior is specified by the int value at each key as follows:

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
    of how many attempts have already been made so far, unless
    :attr:`stagger_cooldown` is nonzero.
    """

    sleep_timer_base = 2
    """
    After each retry, the time to sleep before reattempting the API connection
    and request will increase by a factor of this amount.
    """

    timeout = TIMEOUT
    """
    This is the value sent to `Requests`_ as the ``timeout`` parameter that
    determines the TCP read timeout.
    """

    url = ""

    def __init__(self, api_key: str, debug=False):
        self.parent = super(PDSession, self)
        self.parent.__init__()
        self.api_key = api_key
        self.log = logging.getLogger(__name__)
        self.print_debug = debug
        self.retry = {}

    def after_set_api_key(self):
        """
        Setter hook for setting or updating the API key.

        Child classes should implement this to perform additional steps.
        """
        pass

    @property
    def api_key(self) -> str:
        """
        API Key property getter.

        Returns the _api_key attribute's value.
        """
        return self._api_key

    @api_key.setter
    def api_key(self, api_key):
        if not (isinstance(api_key, str) and api_key):
            raise ValueError("API credential must be a non-empty string.")
        self._api_key = api_key
        self.headers.update(self.auth_header)
        self.after_set_api_key()

    @property
    def auth_header(self) -> dict:
        """
        Generates the header with the API credential used for authentication.
        """
        raise NotImplementedError

    def cooldown_factor(self) -> float:
        return self.sleep_timer_base*(1+self.stagger_cooldown*random())

    def normalize_params(self, params) -> dict:
        """
        Modify the user-supplied parameters to ease implementation

        Current behavior:

        * If a parameter's value is of type list, and the parameter name does
          not already end in "[]", then the square brackets are appended to keep
          in line with the requirement that all set filters' parameter names end
          in "[]".

        :returns:
            The query parameters after modification
        """
        updated_params = {}
        for param, value in params.items():
            if type(value) is list and not param.endswith('[]'):
                updated_params[param+'[]'] = value
            else:
                updated_params[param] = value
        return updated_params

    def normalize_url(self, url) -> str:
        """Compose the URL whether it is a path or an already-complete URL"""
        return normalize_url(self.url, url)

    def postprocess(self, response):
        """
        Perform supplemental actions immediately after receiving a response.

        This method is called once per request not including retries, and can be
        extended in child classes.
        """
        pass

    def prepare_headers(self, method, user_headers={}) -> dict:
        """
        Append special additional per-request headers.

        :param method:
            The HTTP method, in upper case.
        :param user_headers:
            Headers that can be specified to override default values.
        :returns:
            The final list of headers to use in the request
        """
        headers = deepcopy(self.headers)
        if user_headers:
            headers.update(user_headers)
        return headers

    @property
    def print_debug(self) -> bool:
        """
        Printing debug flag

        If set to True, the logging level of :attr:`log` is set to
        ``logging.DEBUG`` and all log messages are emitted to ``sys.stderr``.
        If set to False, the logging level of :attr:`log` is set to
        ``logging.NOTSET`` and the debugging log handler that prints messages to
        ``sys.stderr`` is removed. This value thus can be toggled to enable and
        disable verbose command line output.

        It is ``False`` by default and it is recommended to keep it that way in
        production settings.
        """
        return self._debug

    @print_debug.setter
    def print_debug(self, debug: bool):
        self._debug = debug
        if debug and not hasattr(self, '_debugHandler'):
            self.log.setLevel(logging.DEBUG)
            self._debugHandler = logging.StreamHandler()
            self.log.addHandler(self._debugHandler)
        elif not debug and hasattr(self, '_debugHandler'):
            self.log.setLevel(logging.NOTSET)
            self.log.removeHandler(self._debugHandler)
            delattr(self, '_debugHandler')
        # else: no-op; only happens if debug is set to the same value twice

    def request(self, method, url, **kwargs) -> Response:
        """
        Make a generic PagerDuty API request.

        :param method:
            The request method to use. Case-insensitive. May be one of get, put,
            post or delete.
        :param url:
            The path/URL to request. If it does not start with the base URL, the
            base URL will be prepended.
        :param **kwargs:
            Custom keyword arguments to pass to ``requests.Session.request``.
        :type method: str
        :type url: str
        :returns:
            The `requests.Response`_ object corresponding to the HTTP response
        """
        sleep_timer = self.sleep_timer
        network_attempts = 0
        http_attempts = {}
        method = method.strip().upper()
        if method not in self.permitted_methods:
            m_str = ', '.join(self.permitted_methods)
            raise PDClientError(f"Method {method} not supported by this API. " \
                f"Permitted methods: {m_str}")
        req_kw = deepcopy(kwargs)
        full_url = self.normalize_url(url)
        endpoint = "%s %s"%(method.upper(), full_url)

        # Add in any headers specified in keyword arguments:
        headers = kwargs.get('headers', {})
        req_kw.update({
            'headers': self.prepare_headers(method, user_headers=headers),
            'stream': False,
            'timeout': self.timeout
        })

        # Special changes to user-supplied parameters, for convenience
        if 'params' in kwargs and kwargs['params']:
            req_kw['params'] = self.normalize_params(kwargs['params'])

        # Make the request (and repeat w/cooldown if the rate limit is reached):
        while True:
            try:
                response = self.parent.request(method, full_url, **req_kw)
                self.postprocess(response)
            except (HTTPError, PoolError, RequestException) as e:
                network_attempts += 1
                if network_attempts > self.max_network_attempts:
                    error_msg = f"{endpoint}: Non-transient network " \
                        'error; exceeded maximum number of attempts ' \
                        f"({self.max_network_attempts}) to connect to the API."
                    raise PDClientError(error_msg) from e
                sleep_timer *= self.cooldown_factor()
                self.log.warning(
                    "%s: HTTP or network error: %s. retrying in %g seconds.",
                    endpoint, e.__class__.__name__, sleep_timer)
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
                        lower_limit = retry_logic
                        if lower_limit > self.max_http_attempts:
                            lower_limit = self.max_http_attempts
                        self.log.error(
                            f"%s: Non-transient HTTP error: exceeded " \
                            'maximum number of attempts (%d) to make a ' \
                            'successful request. Currently encountering ' \
                            'status %d.', endpoint, lower_limit, status)
                        return response
                    http_attempts[status] = 1 + http_attempts.get(status, 0)
                sleep_timer *= self.cooldown_factor()
                self.log.warning("%s: HTTP error (%d); retrying in %g seconds.",
                    endpoint, status, sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif status == 429:
                sleep_timer *= self.cooldown_factor()
                self.log.debug("%s: Hit API rate limit (status 429); " \
                    "retrying in %g seconds", endpoint, sleep_timer)
                time.sleep(sleep_timer)
                continue
            elif status == 401:
                # Stop. Authentication failed. We shouldn't try doing any more,
                # because we'll run into the same problem later anyway.
                raise PDHTTPError(
                    "Received 401 Unauthorized response from the API. The key "
                    "(...%s) may be invalid or deactivated."%self.trunc_key,
                    response)
            else:
                # All went according to plan.
                return response

    @property
    def stagger_cooldown(self) -> float:
        """
        Randomizing factor for wait times between retries during rate limiting.

        If set to number greater than 0, the sleep time for rate limiting will
        (for each successive sleep) be adjusted by a factor of one plus a
        uniformly-distributed random number between 0 and 1 times this number,
        on top of the base sleep timer :attr:`sleep_timer_base`.

        For example:

        * If this is 1, and :attr:`sleep_timer_base` is 2 (default), then after
          each status 429 response, the sleep time will change overall by a
          random factor between 2 and 4, whereas if it is zero, it will change
          by a factor of 2.
        * If :attr:`sleep_timer_base` is 1, then the cooldown time will be
          adjusted by a random factor between one and one plus this number.

        If the number is set to zero, then this behavior is effectively
        disabled, and the cooldown factor (by which the sleep time is adjusted)
        will just be :attr:`sleep_timer_base`

        Setting this to a nonzero number helps avoid the "thundering herd"
        effect that can potentially be caused by many API clients making
        simultaneous concurrent API requests and consequently waiting for the
        same amount of time before retrying.  It is currently zero by default
        for consistent behavior with previous versions.
        """
        if hasattr(self, '_stagger_cooldown'):
            return self._stagger_cooldown
        else:
            return 0

    @stagger_cooldown.setter
    def stagger_cooldown(self, val):
        if type(val) not in [float, int] or val<0:
            raise ValueError("Cooldown randomization factor stagger_cooldown "
                "must be a positive real number")
        self._stagger_cooldown = val

    @property
    def trunc_key(self) -> str:
        """Truncated key for secure display/identification purposes."""
        return last_4(self.api_key)

    @property
    def user_agent(self) -> str:
        return 'pdpyras/%s python-requests/%s Python/%d.%d'%(
            __version__,
            REQUESTS_VERSION,
            sys.version_info.major,
            sys.version_info.minor
        )

class EventsAPISession(PDSession):

    """
    Session class for submitting events to the PagerDuty v2 Events API.

    Implements methods for submitting events to PagerDuty through the Events API
    and inherits from :class:`pdpyras.PDSession`.  For more details on usage of
    this API, refer to the `Events API v2 documentation
    <https://developer.pagerduty.com/docs/events-api-v2/overview/>`_

    Inherits from :class:`PDSession`.
    """

    permitted_methods = ('POST',)

    url = "https://events.pagerduty.com"

    def __init__(self, api_key: str, debug=False):
        super(EventsAPISession, self).__init__(api_key, debug)
        # See: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview#response-codes--retry-logic
        self.retry[500] = 2 # internal server error, 3 requests total
        self.retry[502] = 4 # bad gateway, 5 requests total
        self.retry[503] = 6 # service unavailable, 7 requests total

    @property
    def auth_header(self) -> dict:
        return {}

    def acknowledge(self, dedup_key) -> str:
        """
        Acknowledge an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to set to the acknowledged state.
        :returns:
            The deduplication key
        """
        return self.send_event('acknowledge', dedup_key=dedup_key)

    def prepare_headers(self, method, user_headers={}) -> dict:
        """
        Add user agent and content type headers for Events API requests.

        :param user_headers: User-supplied headers that will override defaults
        :returns:
            The final list of headers to use in the request
        """
        headers = {}
        headers.update(self.headers)
        headers.update({
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
        })
        headers.update(user_headers)
        return headers

    def resolve(self, dedup_key) -> str:
        """
        Resolve an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to resolve.
        """
        return self.send_event('resolve', dedup_key=dedup_key)

    def send_event(self, action, dedup_key=None, **properties) -> str:
        """
        Send an event to the v2 Events API.

        See: https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2

        :param action:
            The action to perform through the Events API: trigger, acknowledge
            or resolve.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param **properties:
            Additional properties to set, i.e. if ``action`` is ``trigger``
            this would include ``payload``.
        :type action: str
        :type dedup_key: str
        :returns:
            The deduplication key of the incident
        """

        actions = ('trigger', 'acknowledge', 'resolve')
        if action not in actions:
            raise ValueError("Event action must be one of: "+', '.join(actions))

        event = {'event_action':action}

        event.update(properties)
        if isinstance(dedup_key, str):
            event['dedup_key'] = dedup_key
        elif not action == 'trigger':
            raise ValueError("The dedup_key property is required for"
                "event_action=%s events, and it must be a string."%action)
        response = successful_response(
            self.post('/v2/enqueue', json=event),
            context='submitting an event to the events API',
        )
        response_body = try_decoding(response)
        if type(response_body) is not dict or 'dedup_key' not in response_body:
            err_msg = 'Malformed response body from the events API; it is ' \
                'not a dict that has a key named "dedup_key" after ' \
                'decoding. Body = '+truncate_text(response.text)
            raise PDServerError(err_msg, response)
        return response_body['dedup_key']

    def post(self, *args, **kw) -> Response:
        """
        Override of ``requests.Session.post``

        Adds the ``routing_key`` parameter to the body before sending.
        """
        if 'json' in kw and hasattr(kw['json'], 'update'):
            kw['json'].update({'routing_key': self.api_key})
        return super(EventsAPISession, self).post(*args, **kw)

    def trigger(self, summary, source, dedup_key=None, severity='critical',
            payload=None, custom_details=None, images=None, links=None) -> str:
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
        :type custom_details: dict
        :type dedup_key: str
        :type images: list
        :type links: list
        :type payload: dict
        :type severity: str
        :type source: str
        :type summary: str
        :returns:
            The deduplication key of the incident, if any.
        """
        for local in ('payload', 'custom_details'):
            local_var = locals()[local]
            if not (local_var is None or type(local_var) is dict):
                raise ValueError(local+" must be a dict")
        event = {'payload': {'summary':summary, 'source':source,
            'severity':severity}}
        if type(payload) is dict:
            event['payload'].update(payload)
        if type(custom_details) is dict:
            details = event.setdefault('payload', {}).get('custom_details', {})
            details.update(custom_details)
            event['payload']['custom_details'] = details
        if images:
            event['images'] = images
        if links:
            event['links'] = links
        return self.send_event('trigger', dedup_key=dedup_key, **event)


class ChangeEventsAPISession(PDSession):

    """
    Session class for submitting events to the PagerDuty v2 Change Events API.

    Implements methods for submitting change events to PagerDuty's change events
    API. See the `Change Events API documentation
    <https://developer.pagerduty.com/docs/events-api-v2/send-change-events/>`_
    for more details.

    Inherits from :class:`PDSession`.
    """

    permitted_methods = ('POST',)

    url = "https://events.pagerduty.com"

    def __init__(self, api_key: str, debug=False):
        super(ChangeEventsAPISession, self).__init__(api_key, debug)
        # See: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview#response-codes--retry-logic
        self.retry[500] = 2 # internal server error, 3 requests total
        self.retry[502] = 4 # bad gateway, 5 requests total
        self.retry[503] = 6 # service unavailable, 7 requests total

    @property
    def auth_header(self) -> dict:
        return {}

    @property
    def event_timestamp(self) -> str:
        return datetime.utcnow().isoformat()+'Z'

    def prepare_headers(self, method, user_headers={}) -> dict:
        """
        Add user agent and content type headers for Change Events API requests.

        :param user_headers: User-supplied headers that will override defaults
        :returns:
            The final list of headers to use in the request
        """
        headers = deepcopy(self.headers)
        headers.update({
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
        })
        if user_headers:
            headers.update(user_headers)
        return headers

    def send_change_event(self, **properties):
        """
        Send a change event to the v2 Change Events API.

        See: https://developer.pagerduty.com/docs/events-api-v2/send-change-events/

        :param **properties:
            Properties to set, i.e. ``payload`` and ``links``
        :returns:
            The response ID
        """
        event = deepcopy(properties)
        response = self.post('/v2/change/enqueue', json=event)
        response_body = try_decoding(successful_response(
            response,
            context="submitting change event",
        ))
        return response_body.get("id", None)

    def submit(self, summary, source=None, custom_details=None, links=None,
            timestamp=None) -> str:
        """
        Submit an incident change

        :param summary:
            Summary / brief description of the change.
        :param source:
            A human-readable name identifying the source of the change.
        :param custom_details:
            The ``payload.custom_details`` property of the payload.
        :param links:
            Set the ``links`` property of the event.
        :param timestamp:
            Specifies an event timestamp. Must be an ISO8601-format date/time.
        :type summary: str
        :type source: str
        :type custom_details: dict
        :type links: list
        :type timestamp: str
        :returns:
            The response ID
        """
        local_var = locals()['custom_details']
        if not (local_var is None or isinstance(local_var, dict)):
            raise ValueError("custom_details must be a dict")
        if timestamp is None:
            timestamp = self.event_timestamp
        event = {
                'routing_key': self.api_key,
                'payload': {
                    'summary': summary,
                    'timestamp': timestamp,
                    }
                }
        if isinstance(source, str):
            event['payload']['source'] = source
        if isinstance(custom_details, dict):
            event['payload']['custom_details'] = custom_details
        if links:
            event['links'] = links
        return self.send_change_event(**event)


class APISession(PDSession):
    """
    PagerDuty REST API v2 session object class.

    Implements the most generic and oft-implemented aspects of PagerDuty's REST
    API v2 as an opinionated wrapper of `requests.Session`_.

    Inherits from :class:`PDSession`.

    :param api_key:
        REST API access token to use for HTTP requests
    :param default_from:
        The default email address to use in the ``From`` header when making
        API calls using an account-level API access key.
    :param auth_type:
        The type of credential in use. If authenticating with an OAuth access
        token, this must be set to ``oauth2`` or ``bearer``.
    :param debug:
        Sets :attr:`print_debug`. Set to True to enable verbose command line
        output.
    :type token: str
    :type name: str or None
    :type default_from: str or None
    :type debug: bool

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
    iterating/querying an index (the ``limit`` parameter).
    """

    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = 'https://api.pagerduty.com'
    """Base URL of the REST API"""

    def __init__(self, api_key: str, default_from=None,
            auth_type='token', debug=False):
        self.api_call_counts = {}
        self.api_time = {}
        self.auth_type = auth_type
        super(APISession, self).__init__(api_key, debug=debug)
        self.default_from = default_from
        self.headers.update({
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def after_set_api_key(self):
        self._subdomain = None

    @property
    def api_key_access(self) -> str:
        """
        Memoized API key access type getter.

        Will be "user" if the API key is a user-level token (all users should
        have permission to create an API key with the same permissions as they
        have in the PagerDuty web UI).

        If the API key in use is an account-level API token (as only a global
        administrator user can create), this property will be "account".
        """
        if not hasattr(self, '_api_key_access') or self._api_key_access is None:
            response = self.get('/users/me')
            if response.status_code == 400:
                message = try_decoding(response).get('error', '')
                if 'account-level access token' in message:
                    self._api_key_access = 'account'
                else:
                    self._api_key_access = None
                    self.log.error("Failed to obtain API key access level; "
                        "the API did not respond as expected.")
                    self.log.debug("Body = %s", truncate_text(response.text))
            else:
                self._api_key_access = 'user'
        return self._api_key_access

    @property
    def auth_type(self) -> str:
        """
        Defines the method of API authentication.

        By default this is "token"; if "oauth2", the API key will be used.
        """
        return self._auth_type

    @auth_type.setter
    def auth_type(self, value: str):
        if value not in ('token', 'bearer', 'oauth2'):
            raise AttributeError("auth_type value must be \"token\" (default) "
                "or \"bearer\" or \"oauth\" to use OAuth2 authentication.")
        self._auth_type = value

    @property
    def auth_header(self) -> dict:
        if self.auth_type in ('bearer', 'oauth2'):
            return {"Authorization": "Bearer "+self.api_key}
        else:
            return {"Authorization": "Token token="+self.api_key}

    def dict_all(self, path: str, **kw) -> dict:
        """
        Dictionary representation of resource collection results

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
        """
        by = kw.pop('by', 'id')
        iterator = self.iter_all(path, **kw)
        return {obj[by]:obj for obj in iterator}

    def find(self, resource, query, attribute='name', params=None) \
            -> Union[dict, None]:
        """
        Finds an object of a given resource type exactly matching a query.

        Works by querying a given resource index endpoint using the ``query``
        parameter. To use this function on any given resource, the resource's
        index must support the ``query`` parameter; otherwise, the function may
        not work as expected. If the index ignores the parameter, for instance,
        this function will take much longer to return; results will not be
        constrained to those matching the query, and so every result in the
        index will be downloaded and compared against the query up until a
        matching result is found or all results have been checked.

        The comparison between the query and matching results is case-insenitive. When
        determining uniqueness, APIs are mostly case-insensitive, and therefore objects
        with similar characters but differing case can't even exist. All results (and
        the search query) are for this reason reduced pre-comparison to a common form
        (all-lowercase strings) so that case doesn't need to match in the query argument
        (which is also interpreted by the API as case-insensitive).

        If said behavior differs for a given API, i.e. the uniqueness constraint on a
        field is case-sensitive, it should still return the correct results because the
        search term sent to the index in the querystring is not lower-cased.

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
        :returns:
            The dictionary representation of the result, if found; ``None`` will
            be returned if there is no exact match result.
        """
        query_params = {}
        if params is not None:
            query_params.update(params)
        query_params.update({'query':query})
        simplify = lambda s: str(s).lower()
        search_term = simplify(query)
        equiv = lambda s: simplify(s[attribute]) == search_term
        obj_iter = self.iter_all(resource, params=query_params)
        return next(iter(filter(equiv, obj_iter)), None)

    def iter_all(self, url, params=None, page_size=None, item_hook=None,
            total=False) -> Iterator[dict]:
        """
        Iterator for the contents of an index endpoint or query.

        Automatically paginates and yields the results in each page, until all
        matching results have been yielded or a HTTP error response is received.

        If the URL to use supports cursor-based pagintation, then this will
        return :attr:`iter_cursor` with the same keyword arguments. Otherwise,
        it implements classic pagination, a.k.a. numeric pagination.

        Each yielded value is a dict object representing a result returned from
        the index. For example, if requesting the ``/users`` endpoint, each
        yielded value will be an entry of the ``users`` array property in the
        response.

        :param url:
            The index endpoint URL to use.
        :param params:
            Additional URL parameters to include.
        :param page_size:
            If set, the ``page_size`` argument will override the
            ``default_page_size`` parameter on the session and set the ``limit``
            parameter to a custom value (default is 100), altering the number of
            pagination results. The actual number of results in the response
            will still take precedence, if it differs; this parameter and
            ``default_page_size`` only dictate what is requested of the API.
        :param item_hook:
            Callable object that will be invoked for each iteration, i.e. for
            printing progress. It will be called with three parameters: a dict
            representing a given result in the iteration, an int representing
            the number of the item in the series, and an int (or str, as of
            v5.0.0) representing the total number of items in the series. If the
            total isn't knowable, the value passed is "?".
        :param total:
            If True, the ``total`` parameter will be included in API calls, and
            the value for the third parameter to the item hook will be the total
            count of records that match the query. Leaving this as False confers
            a small performance advantage, as the API in this case does not have
            to compute the total count of results in the query.
        :type url: str
        :type params: dict or None
        :type page_size: int or None
        :type total: bool
        """
        # Get entity wrapping and validate that the URL being requested is
        # likely to support pagination:
        path = canonical_path(self.url, url)
        endpoint = f"GET {path}"

        # Short-circuit to cursor-based pagination if appropriate:
        if path in CURSOR_BASED_PAGINATION_PATHS:
            return self.iter_cursor(url, params=params)

        nodes = path.split('/')
        if is_path_param(nodes[-1]):
            # NOTE: If this happens for a newer API, the path might need to be
            # added to the EXPAND_PATHS dictionary in
            # scripts/get_path_list/get_path_list.py, after which
            # CANONICAL_PATHS will then need to be updated accordingly based on
            # the new output of the script.
            raise URLError(f"Path {path} (URL={url}) is formatted like an " \
                "individual resource versus a resource collection. It is " \
                "therefore assumed to not support pagination.")
        _, wrapper = entity_wrappers('GET', path)

        if wrapper is None:
            raise URLError(f"Pagination is not supported for {endpoint}.")

        # Parameters to send:
        data = {}
        if page_size is None:
            data['limit'] = self.default_page_size
        else:
            data['limit'] = page_size
        if total:
            data['total'] = 1
        if isinstance(params, (dict, list)):
            # Override defaults with values given:
            data.update(dict(params))

        more = True
        offset = 0
        if params is not None:
            offset = int(params.get('offset', 0))
        n = 0
        while more:
            # Check the offset and limit:
            data['offset'] = offset
            highest_record_index = int(data['offset']) + int(data['limit'])
            if highest_record_index > ITERATION_LIMIT:
                iter_limit = '%d'%ITERATION_LIMIT
                warn(
                    f"Stopping iter_all on {endpoint} at " \
                    f"limit+offset={highest_record_index} " \
                    'as this exceeds the maximum permitted by the API ' \
                    f"({iter_limit}). The set of results may be incomplete."
                )
                return

            # Make the request and validate/unpack the response:
            r = successful_response(
                self.get(url, params=data.copy()),
                context='classic pagination'
            )
            body = try_decoding(r)
            results = unwrap(r, wrapper)

            # Validate and update pagination parameters
            #
            # Note, the number of the results in the actual response is always
            # the most appropriate amount to increment the offset by after
            # receiving each page. If this is the last page, agination should
            # stop anyways because the ``more`` parameter should evaluate to
            # false.
            #
            # In short, the reasons why we don't trust the echoed ``limit``
            # value or stick to the limit requested and hope the server honors
            # it is that it could potentially result in skipping results or
            # yielding duplicates if there's a mismatch, or potentially issues
            # like #61
            data['limit'] = len(results)
            offset += data['limit']
            more = False
            total_count = '?'
            if 'more' in body:
                more = body['more']
            else:
                warn(
                    f"Endpoint GET {path} responded with no \"more\" property" \
                    ' in the response, so pagination is not supported ' \
                    '(or this is an API bug). Only results from the first ' \
                    'request will be yielded. You can use rget with this ' \
                    'endpoint instead to avoid this warning.'
                )
            if 'total' in body:
                total_count = body['total']

            # Perform per-page actions on the response data
            for result in results:
                n += 1
                # Call a callable object for each item, i.e. to print progress:
                if hasattr(item_hook, '__call__'):
                    item_hook(result, n, total_count)
                yield result

    def iter_cursor(self, url, params=None, item_hook=None) -> Iterator[dict]:
        """
        Iterator for results from an endpoint using cursor-based pagination.

        :param url:
            The index endpoint URL to use.
        :param params:
            Query parameters to include in the request.
        :param item_hook:
            A callable object that accepts 3 positional arguments; see
        """
        path = canonical_path(self.url, url)
        if path not in CURSOR_BASED_PAGINATION_PATHS:
            raise URLError(f"{path} does not support cursor-based pagination.")
        _, wrapper = entity_wrappers('GET', path)
        user_params = {}
        if isinstance(params, (dict, list)):
            # Override defaults with values given:
            user_params.update(dict(params))

        more = True
        next_cursor = None
        total = 0

        while more:
            # Update parameters and request a new page:
            if next_cursor:
                user_params.update({'cursor': next_cursor})
            r = successful_response(
                self.get(url, params=user_params),
                context='cursor-based pagination',
            )

            # Unpack and yield results
            body = try_decoding(r)
            results = unwrap(r, wrapper)
            for result in results:
                total += 1
                if hasattr(item_hook, '__call__'):
                    item_hook(result, total, '?')
                yield result
            # Advance to the next page
            next_cursor = body.get('next_cursor', None)
            more = bool(next_cursor)

    @resource_url
    @auto_json
    def jget(self, url, **kw) -> Union[dict, list]:
        """
        Performs a GET request, returning the JSON-decoded body as a dictionary
        """
        return self.get(url, **kw)

    @resource_url
    @auto_json
    def jpost(self, url, **kw) -> Union[dict, list]:
        """
        Performs a POST request, returning the JSON-decoded body as a dictionary
        """
        return self.post(url, **kw)

    @resource_url
    @auto_json
    def jput(self, url, **kw) -> Union[dict, list]:
        """
        Performs a PUT request, returning the JSON-decoded body as a dictionary
        """
        return self.put(url, **kw)

    def list_all(self, url, **kw) -> list:
        """
        Returns a list of all objects from a given index endpoint.

        All keyword arguments passed to this function are also passed directly
        to :attr:`iter_all`; see the documentation on that method for details.

        :param url:
            The index endpoint URL to use.
        """
        return list(self.iter_all(url, **kw))

    def persist(self, resource, attr, values, update=False):
        """
        Finds or creates and returns a resource with a matching attribute

        Given a resource name, an attribute to use as an idempotency key and a
        set of attribute:value pairs as a dict, create a resource with the
        specified attributes if it doesn't exist already and return the resource
        persisted via the API (whether or not it already existed).

        :param resource:
            The URL to use when creating the new resource or searching for an
            existing one. The underlying AP must support entity wrapping to use
            this method with it.
        :param attr:
            Name of the attribute to use as the idempotency key. For instance,
            "email" when the resource is "users" will not create the user if a
            user with the email address given in ``values`` already exists.
        :param values:
            The content of the resource to be created, if it does not already
            exist. This must contain an item with a key that is the same as the
            ``attr`` argument.
        :param update:
            (New in 4.4.0) If set to True, any existing resource will be updated
            with the values supplied.
        :type resource: str
        :type attr: str
        :type values: dict
        :type update: bool
        :rtype: dict
        """
        if attr not in values:
            raise ValueError("Argument `values` must contain a key equal "
                "to the `attr` argument (expected idempotency key: '%s')."%attr)
        existing = self.find(resource, values[attr], attribute=attr)
        if existing:
            if update:
                original = {}
                original.update(existing)
                existing.update(values)
                if original != existing:
                    existing = self.rput(existing, json=existing)
            return existing
        else:
            return self.rpost(resource, json=values)

    def postprocess(self, response: Response, suffix=None):
        """
        Records performance information / request metadata about the API call.

        :param response:
            The `requests.Response`_ object returned by the request method
        :param suffix:
            Optional suffix to append to the key
        :type method: str
        :type response: `requests.Response`_
        :type suffix: str or None
        """
        method = response.request.method.upper()
        url = response.request.url
        status = response.status_code
        request_date = response.headers.get('date', '(missing header)')
        request_id = response.headers.get('x-request-id', '(missing header)')
        request_time = response.elapsed.total_seconds()

        try:
            endpoint = "%s %s"%(method, canonical_path(self.url, url))
        except URLError:
            # This is necessary so that profiling can also support using the
            # basic get / post / put / delete methods with APIs that are not yet
            # explicitly supported by inclusion in CANONICAL_PATHS.
            endpoint = "%s %s"%(method, url)
        self.api_call_counts.setdefault(endpoint, 0)
        self.api_time.setdefault(endpoint, 0.0)
        self.api_call_counts[endpoint] += 1
        self.api_time[endpoint] += request_time

        # Request ID / timestamp logging
        self.log.debug("Request completed: #method=%s|#url=%s|#status=%d|"
            "#x_request_id=%s|#date=%s|#wall_time_s=%g", method, url, status,
            request_id, request_date, request_time)
        if int(status/100) == 5:
            self.log.error("PagerDuty API server error (%d)! "
                "For additional diagnostics, contact PagerDuty support "
                "and reference x_request_id=%s / date=%s",
                status, request_id, request_date)

    def prepare_headers(self, method, user_headers={}) -> dict:
        headers = deepcopy(self.headers)
        headers['User-Agent'] = self.user_agent
        if self.default_from is not None:
            headers['From'] = self.default_from
        if method in ('POST', 'PUT'):
            headers['Content-Type'] = 'application/json'
        if user_headers:
            headers.update(user_headers)
        return headers

    @resource_url
    @requires_success
    def rdelete(self, resource, **kw) -> Response:
        """
        Delete a resource.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.delete``
        :type resource: str or dict
        """
        return self.delete(resource, **kw)

    @resource_url
    @wrapped_entities
    def rget(self, resource, **kw) -> Union[dict, list]:
        """
        Wrapped-entity-aware GET function.

        Retrieves a resource via GET and returns the wrapped entity in the
        response.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.get``
        :returns:
            Dictionary representation of the requested object
        :type resource: str or dict
        """
        return self.get(resource, **kw)

    @wrapped_entities
    def rpost(self, path, **kw) -> Union[dict, list]:
        """
        Wrapped-entity-aware POST function.

        Creates a resource and returns the created entity if successful.

        :param path:
            The path/URL to which to send the POST request, which should be an
            index endpoint.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.post``
        :returns:
            Dictionary representation of the created object
        :type path: str
        """
        return self.post(path, **kw)

    @resource_url
    @wrapped_entities
    def rput(self, resource, **kw) -> Union[dict, list]:
        """
        Wrapped-entity-aware PUT function.

        Update an individual resource, returning the wrapped entity.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.put``
        :returns:
            Dictionary representation of the updated object
        """
        return self.put(resource, **kw)

    @property
    def subdomain(self) -> str:
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
    def total_call_count(self) -> int:
        """The total number of API calls made by this instance."""
        return sum(self.api_call_counts.values())

    @property
    def total_call_time(self) -> float:
        """The total time spent making API calls."""
        return sum(self.api_time.values())

    @property
    def trunc_token(self) -> str:
        """Truncated token for secure display/identification purposes."""
        return last_4(self.api_key)

class URLError(Exception):
    """
    Exception class for unsupported URLs or malformed input.
    """
    pass

class PDClientError(Exception):
    """
    General API errors base class.

    Note, the name of this class does not imply it solely includes errors
    experienced by the client or HTTP status 4xx responses, but descendants can
    include issues with the API backend.
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

class PDHTTPError(PDClientError):
    """
    Error class representing errors strictly associated with HTTP responses.

    This class was created to make it easier to more cleanly handle errors by
    way of a class that is guaranteed to have its ``response`` be a valid
    `requests.Response`_ object.

    Whereas, the more generic :class:`PDClientError` could also be used
    to denote such things as non-transient network errors wherein no response
    was recevied from the API.

    For instance, instead of this:

    ::

        try:
            user = session.rget('/users/PABC123')
        except pdpyras.PDClientError as e:
            if e.response is not None:
                print("HTTP error: "+str(e.response.status_code))
            else:
                raise e

    one could write this:

    ::

        try:
            user = session.rget('/users/PABC123')
        except pdpyras.PDHTTPError as e:
            print("HTTP error: "+str(e.response.status_code))
    """

    def __init__(self, message, response: Response):
        super(PDHTTPError, self).__init__(message, response=response)

class PDServerError(PDHTTPError):
    """
    Error class representing failed expectations made of the server

    This is raised in cases where the response schema differs from the expected
    schema because of an API bug, or because it's an early access endpoint and
    changes before GA, or in cases of HTTP status 5xx where a successful
    response is required.
    """
    pass
