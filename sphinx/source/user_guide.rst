.. _user_guide:

==========
User Guide
==========

This is a topical guide to general API client usage. :ref:`module_reference`
has in-depth documentation on client classes and methods.

Installation
------------
If ``pip`` is available, it can be installed via:

.. code-block:: shell

    pip install pdpyras

Alternately, if the dependencies (Requests_ and "deprecation" Python libraries)
have been installed locally, one can download ``pdpyras.py`` into the directory
where it will be used.

Authentication
--------------
The first step is to construct a session object. The first argument to the
constructor is the secret to use for accessing the API:

.. code-block:: python

    import pdpyras

    # REST API v2:
    session = pdpyras.APISession(API_KEY)

    # REST API v2 with an OAuth2 access token:
    session_oauth = pdpyras.APISession(OAUTH_TOKEN, auth_type='oauth2')

    # Events API v2:
    events_session = pdpyras.EventsAPISession(ROUTING_KEY)

    # A special session class for the change events API (part of Events API v2):
    change_events_session = pdpyras.ChangeEventsAPISession(ROUTING_KEY)

Session objects, being descendants of `requests.Session`_, can also be used as
context managers. For example:

.. code-block:: python

    with pdpyras.APISession(API_KEY) as session:
        do_application(session)

The From header
***************
If the `REST API v2`_ session will be used for API endpoints that require a
``From`` header, such as those that take actions on incidents, and if it is
using an account-level API key (created by an administrator via the "API Access
Keys" page in the "Integrations" menu), the user must also supply the
``default_from`` keyword argument. Otherwise, a HTTP 400 response will result
when making requests to such endpoints.

Otherwise, if using a user's API key (created under "API Access" in the "User
Settings" tab of the user's profile), the user will be derived from the key
itself and ``default_from`` is not necessary.

Using Non-US Service Regions
****************************

If your PagerDuty account is in the EU or other service region outside the US, set the ``url`` attribute according to the
documented `API Access URLs
<https://support.pagerduty.com/docs/service-regions#api-access-urls>`_, i.e. for the EU:

.. code-block:: python

    # REST API
    session.url = 'https://api.eu.pagerduty.com'
    # Events API:
    events_session.url = 'https://events.eu.pagerduty.com'

Basic Usage Examples
--------------------

REST API v2
***********

**Making a request and decoding the response:** obtaining a resource's contents
and having them represented as a dictionary object using three different methods:

.. code-block:: python

    # Using get:
    response = session.get('/users/PABC123')
    user = None
    if response.ok:
        user = response.json()['user']

    # Using jget (return the full body after decoding):
    user = session.jget('/users/PABC123')['user']

    # Using rget (return the response entity after unwrapping):
    user = session.rget('/users/PABC123')

    # >>> user
    # {"type": "user", "email": "user@example.com", ... }

**Using pagination:** ``iter_all``, ``iter_cursor``, ``list_all`` and
``dict_all`` can be used to obtain results from a resource collection:

.. code-block:: python

    # Print each user's email address and name:
    for user in session.iter_all('users'):
        print(user['id'], user['email'], user['name'])

**Pagination with query parameters:** set the ``params`` keyword argument, which is 
converted to URL query parameters by Requests_:

.. code-block:: python

    # Get a list of all services with "SN" in their name:
    services = session.list_all('services', params={'query': 'SN'})

    # >>> services
    # [{'type':'service', ...}, ...]

**Searching resource collections:** use ``find`` to look up a resource exactly
matching a string using the ``query`` parameter on an index endpoint:

.. code-block:: python

    # Find the user with email address "jane@example35.com"
    user = session.find('users', 'jane@example35.com', attribute='email')

    # >>> user
    # {'type': 'user', 'email': 'jane@example35.com', ...}

**Updating a resource:** use the ``json`` keyword argument to set the body:

.. code-block:: python

    # Assuming there is a variable "user" defined that is a dictionary
    # representation of a PagerDuty user, i.e. as returned by rget or find:

    # (1) using put directly:
    updated_user = None
    response = session.put(user['self'], json={
        'user': {
            'type':'user',
            'name': 'Jane Doe'
        }
    })
    if response.ok:
        updated_user = response.json()['user']

    # (2) using rput:
    #   - The URL argument can be the dictionary representation
    #   - The json argument doesn't have to include the "user" wrapper dict
    try:
        updated_user = session.rput(user, json={
            'type':'user',
            'name': 'Jane Doe'
        })
    except PDClientError:
        updated_user = None

**Idempotent create/update:**

.. code-block:: python

    # Create a user if one doesn't already exist based on the dictionary object
    # user_data, using the 'email' key as the uniquely identifying property,
    # and update it if it exists and differs from user_data:
    user_data = {'email': 'user123@example.com', 'name': 'User McUserson'}
    updated_user = session.persist('users', 'email', user_data, update=True)

**Using multi-valued set filters:** set the value in the ``params`` dictionary at
the appropriate key to a list. Ordinarily one must include ``[]`` at the end of the paramter
name; in the case of this client, the brackets are automatically appended to
the names of list-type-value parameters as necessary:

.. code-block:: python

    # Query all open incidents assigned to a user:
    incidents = session.list_all(
        'incidents',
        params={'user_ids':['PHIJ789'],'statuses':['triggered', 'acknowledged']}
    )

**Performing multi-update:** for endpoints that support it only, i.e. ``PUT /incidents``:

.. code-block:: python

    # Acknowledge all triggered incidents assigned to a user:
    incidents = session.list_all(
        'incidents',
        params={'user_ids':['PHIJ789'],'statuses':['triggered']}
    )
    for i in incidents:
        i['status'] = 'acknowledged'
    updated_incidents = session.rput('incidents', json=incidents)

Events API v2
*************
**Trigger and resolve an alert,** getting its deduplication key from the API, using :class:`EventsAPISession`:

.. code-block:: python

    dedup_key = events_session.trigger("Server is on fire", 'dusty.old.server.net') 
    # ...
    events_session.resolve(dedup_key)

**Trigger an alert and acknowledge it** using a custom deduplication key:

.. code-block:: python

    events_session.trigger("Server is on fire", 'dusty.old.server.net',
        dedup_key='abc123')
    # ...
    events_session.acknowledge('abc123')

**Submit a change event** using a :class:`ChangeEventsAPISession` instance:

.. code-block:: python

    change_events_session.submit("new build finished at latest HEAD",
        source="automation")

Generic Client Features
-----------------------
Generally, all of the features of `requests.Session`_ are available to the user
as they would be if using the Requests Python library directly, since
:class:`pdpyras.PDSession` and its subclasses for the REST/Events APIs are
descendants of it. 

The ``get``, ``post``, ``put`` and ``delete`` methods of REST/Events API
session classes are similar to the analogous functions in `requests.Session`_.
The arguments they accept are the same and they all return `requests.Response`_
objects.

Any keyword arguments passed to the ``j*`` or ``r*`` methods will be passed
through to the analogous method in Requests_, though in some cases the
arguments (i.e. ``json``) are first modified.

For documentation on any generic HTTP client features that are available, refer
to the Requests_ documentation.

URLs
----
The first argument to most of the session methods is the URL. However, there is
no need to specify a complete API URL. Any path relative to the root of the
API, whether or not it includes a leading slash, is automatically normalized to
a complete API URL.  For instance, one can specify ``users/PABC123`` or
``/users/PABC123`` instead of ``https://api.pagerduty.com/users/PABC123``.

One can also pass the full URL of an API endpoint and it will still work, i.e.
the ``self`` property of any object can be used, and there is no need to strip
out the API base URL.

The ``r*`` (and ``j*`` methods as of version 5), i.e.
:attr:`pdpyras.APISession.rget`, can also accept a dictionary object
representing an API resource or a resource reference in place of a URL, in
which case the URL at its ``self`` key will be used as the request target.

Query Parameters
----------------
As with `Requests`_, there is no need to compose the query string (everything
that will follow ``?`` in the URL). Simply set the ``params`` keyword argument
to a dictionary, and each of the key/value pairs will be serialized to the
query string in the final URL of the request:

.. code-block:: python

    first_dan = session.rget('users', params={
        'query': 'Dan',
        'limit': 1,
        'offset': 0,
    })
    # GET https://api.pagerduty.com/users?query=Dan&limit=1&offset=0

To specify a multi-value parameter, i.e. ``include[]``, set the argument to a
list. As of v4.4.0, if a list is given, and the key name does not end with
``[]`` (which is required for all such multi-valued parameters in REST API v2),
then ``[]`` will be automatically appended to the parameter name.

.. code-block:: python

    # If there are 82 services with name matching "foo" this will return all of
    # them as a list:
    foo_services = session.list_all('services', params={
        'query': 'foo',
        'include': ['escalation_policies', 'teams'],
        'limit': 50,
    })
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=0
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=50
    # >>> foo_services
    # [{"type": "service" ...}, ... ]


Requests and Responses
----------------------
To set the request body in a post or put request, pass as the ``json`` keyword
argument an object that will be JSON-encoded as the body.

To obtain the response from the API, if using plain ``get``, ``post``, ``put``
or ``delete``, use the returned `requests.Response`_ object. That object's
``json()`` method will return the result of JSON-decoding the response body (it
will typically of type ``dict``). Other metadata such as headers can also be
obtained:

.. code-block:: python

    response = session.get('incidents')
    # The UUID of the API request, which can be supplied to PagerDuty Customer
    # Support in the event of server errors (status 5xx):
    print(response.headers['x-request-id'])

If using the ``j*`` methods, i.e. :attr:`pdpyras.APISession.jget`, the return value
will be the full body of the response from the API after JSON-decoding, and
the ``json`` keyword argument is not modified.

When using the ``r*`` methods, the ``json`` keyword argument is modified before
sending to Requests_, if necessary, to encapsulate the body inside an entity
wrapper.  The response is the decoded body after unwrapping, if the API
endpoint returns wrapped entities. For more details, refer to :ref:`wrapping`.

Data types
**********
Main article: `Types <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types>`_

Note these analogues in structure between the JSON schema and the object
in Python:

* If the data type documented in the schema is
  `"object" <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#object>`_,
  then the corresponding type of the Python object will be ``dict``.
* If the data type documented in the schema is
  `array <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#array>`_,
  then the corresponding type of the Python object will be ``list``.
* Generally speaking, the data type in the decoded object is according to the
  design of the `json <https://docs.python.org/3/library/json.html>`_ Python library.

For example, consider the example structure of an escalation policy as given in
the API reference page for ``GET /escalation_policies/{id}`` ("Get an
escalation policy").. To access the name of the second target in level 1,
assuming the variable ``ep`` represents the unwrapped escalation policy object:

.. code-block:: python

    ep['escalation_rules'][0]['targets'][1]['summary']
    # "Daily Engineering Rotation"

To add a new level, one would need to create a new escalation rule as a
dictionary object and then append it to the ``escalation rules`` property.
Using the example given in the API reference page:

.. code-block:: python

    new_rule = {
        "escalation_delay_in_minutes": 30,
        "targets": [
            {
                "id": "PAM4FGS",
                "type": "user_reference"
            },
            {
                "id": "PI7DH85",
                "type": "schedule_reference"
            }
        ]
    }
    ep['escalation_rules'].append(new_rule)
    # Save changes:
    session.rput(ep, json=ep)

Resource schemas
****************
Main article: `Resource Schemas <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU5-resource-schemas>`_

The details of any given resource's schema can be found in the request and
response examples from the `PagerDuty API Reference`_ pages for the resource's
respective API, as well as the page documenting the resource type itself.

.. _wrapping:

Entity Wrapping
---------------
See also: `Wrapped Entities <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYx-wrapped-entities>`_.
Most of PagerDuty's REST API v2 endpoints respond with their content wrapped
inside of another object with a single key at the root level of the
(JSON-encoded) response body, and/or require the request body be wrapped in
another object that contains a single key. Endpoints with such request/response
schemas are said to wrap entities.

Wrapped-entity-aware Functions
******************************
The following methods will automatically extract and return the wrapped content
of API responses, and wrap request entities for the user as appropriate:

* :attr:`pdpyras.APISession.dict_all`: Create a dictionary of all results from a resource collection
* :attr:`pdpyras.APISession.find`: Find and return a specific result of a resource collection that matches a query
* :attr:`pdpyras.APISession.iter_all`: Iterate through all results of a resource collection
* :attr:`pdpyras.APISession.iter_cursor`: Iterate through all results of a resource collection using cursor-based pagination
* :attr:`pdpyras.APISession.list_all`: Create a list of all results from a resource collection
* :attr:`pdpyras.APISession.persist`: Create a resource entity with specified attributes if one that matches them does not already exist
* :attr:`pdpyras.APISession.rget`: Get the wrapped entity or resource collection at a given endpoint
* :attr:`pdpyras.APISession.rpost`: Send a POST request, wrapping the request entity / unwrapping the response entity
* :attr:`pdpyras.APISession.rput`: Send a PUT request, wrapping the request entity / unwrapping the response entity

Classic Patterns
****************
Typically (but not for all endpoints), the key ("wrapper name") is named after
the last or second to last node of the URL's path. The wrapper name is a
singular noun for an individual resource or plural for a collection of
resources. As of v5.0.0, the above methods support endpoints where that pattern
does not apply. In versions prior to v5.0.0, they may only be used on APIs that
follow these conventions, and will run into ``KeyError`` when used on endpoints
that do not.

Special Cases
*************
On endpoints that do not wrap entities, however, the results for a given ``r*``
method would be the same if using the equivalent ``j*`` method. This is
necessary to avoid discarding features of the response schema.

The configuration that this client uses to decide if entity wrapping is enabled
for an endpoint or not is stored in the module variable
:attr:`pdpyras.ENTITY_WRAPPER_CONFIG` and generally follows this rule: *If the
endpoint's response body or expected request body contains only one property
that points to all the content of the requested resource, entity wrapping is
enabled for the endpoint.* The only exception is for resource collection
endpoints that support pagination, where response bodies have additional
pagination control properties like ``more`` but only one content-bearing
property that wraps the collection of results.

This rule also applies to endpoints like ``POST
/business_services/{id}/subscribers`` where the response is wrapped differently
than the request. One can still pass the content to be wrapped via the ``json``
argument without the ``subscribers`` wrapper, while the return value is the
list representing the content inside of the ``subscriptions`` wrapper in the
response, and there is no need to incorporate any particular endpoint's wrapper
name into the implementation.

Some endpoints are unusual in that the request must be wrapped but the response
is not wrapped or vice versa, i.e. creating Schedule overrides (``POST
/schedules/{id}/overrides``) or to create a status update on an incient (``POST
/incidents/{id}/status_updates``). In all such cases, the user still does not
need to account for this, as the content will be returned and the request
entity is wrapped as appropriate. For instance:

.. code-block:: python

    created_overrides = session.rpost('/schedules/PGHI789/overrides', json=[
        {
            "start": "2023-07-01T00:00:00-04:00",
            "end": "2023-07-02T00:00:00-04:00",
            "user": {
                "id": "PEYSGVA",
                "type": "user_reference"
            },
            "time_zone": "UTC"
        },
        {
            "start": "2023-07-03T00:00:00-04:00",
            "end": "2023-07-01T00:00:00-04:00",
            "user": {
                "id": "PEYSGVF",
                "type": "user_reference"
            },
            "time_zone": "UTC"
        }
    ])
    # >>> created_overrides
    # [
    #     {'status': 201, 'override': {...}},
    #     {'status': 400, 'errors': ['Override must end after its start'], 'override': {...}}
    # ]

Pagination
----------
The method :attr:`pdpyras.APISession.iter_all` returns an iterator that yields
results from an endpoint that returns a wrapped collection of resources. By
default it will use classic, a.k.a. numeric pagination. If the endpoint
supports cursor-based pagination, it will use
:attr:`pdpyras.APISession.iter_cursor` to iterate through results instead. The
methods :attr:`pdpyras.APISession.list_all` and
:attr:`pdpyras.APISession.dict_all` will request all pages of the collection
and return the results as a list or dictionary, respectively.

Pagination functions require that the API endpoint being requested has entity
wrapping enabled, and respond with either a ``more`` or ``cursor`` property
indicating how and if to fetch the next page of results.

For example:

.. code-block:: python

    # Example: Find all users with "Dav" in their name/email (i.e. Dave/David)
    # in the PagerDuty account:
    for dave in session.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

    # Example: Get a dictionary of all users, keyed by email, and use it to
    # find the ID of the user whose email is ``bob@example.com``
    users = session.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

    # Same as above, but using ``find``:
    bob = session.find('users', 'bob@example.com', attribute='email')
    print(bob['id'])

Performance and Completeness of Results
***************************************
Because HTTP requests are made synchronously and not in multiple threads,
requesting all pages of data will happen one page at a time and the functions
``list_all`` and ``dict_all`` will not return until after the final HTTP
response. Simply put, the functions will take longer to return if the total
number of results is higher.

Moreover, if these methods are used to fetch a very large volume of data, and
an error is encountered when this happens, the partial data set will be
discarded when the exception is raised. To make use of partial results, use
:attr:`pdpyras.APISession.iter_all`, perform actions on each result
yielded, and catch/handle exceptions as desired.

Updating, creating or deleting while paginating
***********************************************
If performing page-wise write operations, i.e. making persistent changes to the
PagerDuty application state immediately after fetching each page of results, an
erroneous condition can result if there is any change to the resources in the
result set that would affect their presence or position in the set. For
example, creating objects, deleting them, or changing the attribute being used
for sorting or filtering.

This is because the contents are updated in real time, and pagination contents
are recalculated based on the state of the PagerDuty application at the time of
each request for a page of results. Therefore, records may be skipped or
repeated in results if the state changes, because the content of any given page
will change accordingly. Note also that changes made from other processes,
including manual edits through the PagerDuty web application, can have the same
effect.

To elaborate: let's say that each resource object in the full list is a page in
a notebook. Classic pagination with ``limit=100`` is essentially "go through
100 pages, then repeat starting with the 101st page, then with the 201st, etc."
Deleting records in-between these 100-at-a-time pagination requests would be
like tearing out pages after reading them. At the time of the second page
request, what was originally the 101st page before starting will shift to
become the first page after tearing out the first hundred pages. Thus, when
going to the 101st page after finishing tearing out the first hundred pages,
the second hundred pages will be skipped over, and similarly for pages 401-500,
601-700 and so on. If attaching pages, the opposite happens: some results will be
returned more than once, because they get bumped to the next group of 100 pages.

Multi-updating
--------------
Multi-update actions can be performed using ``rput``. As of this writing,
multi-update support includes the following endpoints:

* `PUT /incidents <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODEzOQ-manage-incidents>`_
* `PUT /incidents/{id}/alerts <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODE0NA-manage-alerts>`_
* PUT /priorities (documentation not yet published as of 2023-04-26, but the endpoint is functional)

For instance, to resolve two incidents with IDs ``PABC123`` and ``PDEF456``:

.. code-block:: python

    session.rput(
        "incidents",
        json=[
            {'id':'PABC123','type':'incident_reference', 'status':'resolved'},
            {'id':'PDEF456','type':'incident_reference', 'status':'resolved'},
        ],
    )

In this way, a single API request can more efficiently perform multiple update
actions.

It is important to note, however, that updating incidents requires using a
user-scoped access token or setting the ``From`` header to the login email
address of a valid PagerDuty user. To set this, pass it through using the
``headers`` keyword argument, or set the
:attr:`pdpyras.APISession.default_from` property, or pass the email address as
the ``default_from`` keyword argument when constructing the session initially.

Error Handling
--------------
For any of the methods that do not return `requests.Response`_, when the API
responds with a non-success HTTP status, the method will raise a
:class:`pdpyras.PDClientError` exception. This way, these methods can always be
expected to return the same structure of data based on the API being used, and
there is no need to differentiate between the response schema for a successful
request and one for an error response.

The exception class has the `requests.Response`_ object as its ``response``
property whenever the exception pertains to a HTTP error. One can thus define
specialized error handling logic in which the REST API response data (i.e.
headers, code and body) are available in the catching scope.

For instance, the following code prints "User not found" in the event of a 404,
prints out the user's email if the user exists, raises the underlying
exception if it's any other HTTP error code, and prints an error otherwise:

.. code-block:: python

    try:
        user = session.rget("/users/PJKL678")
        print(user['email'])

    except pdpyras.PDClientError as e:
        if e.response:
            if e.response.status_code == 404:
                print("User not found")
            else:
                raise e
        else:
            print("Non-transient network or client error")

Version 4.4.0 introduced a new error subclass, PDHTTPError, in which it can be
assumed that the error pertains to a HTTP request and the ``response`` property
is not ``None``:

.. code-block:: python

    try:
        user = session.rget("/users/PJKL678")
        print(user['email'])
    except pdpyras.PDHTTPError as e:
        if e.response.status_code == 404:
            print("User not found")
        else:
            raise e
    except pdpyras.PDClientError as e:
        print("Non-transient network or client error")

Logging
-------
When a session is created, a
`Logger object <https://docs.python.org/3/library/logging.html#logger-objects>`_
is created as follows:

* Its level is unconfigured (``logging.NOTSET``) which causes it to defer to the 
  level of the parent logger. The parent is the root logger unless specified
  otherwise (see `Logging Levels
  <https://docs.python.org/3/library/logging.html#logging-levels>`_).
* The logger is initially not configured with any handlers. Configuring
  handlers is left to the discretion of the user (see `logging.handlers
  <https://docs.python.org/3/library/logging.handlers.html>`_)
* The logger can be accessed and set through the property
  :attr:`pdpyras.PDSession.log`.

In v5.0.0 and later, the attribute :attr:`pdpyras.PDSession.print_debug` was
introduced to enable sending debug-level log messages from the client to
command line output. It is used as follows:

.. code-block:: python

    # Method 1: keyword argument, when constructing a new session:
    session = pdpyras.APISession(api_key, debug=True)

    # Method 2: on an existing session, by setting the property:
    session.print_debug = True

    # to disable:
    session.print_debug = False

What this does is assign a `logging.StreamHandler
<https://docs.python.org/3/library/logging.handlers.html#streamhandler>`_
directly to the session's logger and set the log level to ``logging.DEBUG``.
All log messages are then sent directly to ``sys.stderr``. The default value
for all sessions is ``False``, and it is recommended to keep it that way in
production systems.

Using a Proxy Server
--------------------
To configure the client to use a host as a proxy for HTTPS traffic, update the
``proxies`` attribute:

.. code-block:: python

    # Host 10.42.187.3 port 4012 protocol https:
    session.proxies.update({'https': '10.42.187.3:4012'})

HTTP Retry Configuration
------------------------
Session objects support retrying API requests if they receive a non-success
response or if they encounter a network error. This behavior is configurable
through the following properties:

* :attr:`pdpyras.PDSession.max_http_attempts`: The maximum total number of unsuccessful requests to make in the retry loop of :attr:`pdpyras.PDSession.request` before returning
* :attr:`pdpyras.PDSession.max_network_attempts`: The maximum number of retries that will be attempted in the case of network or non-HTTP error
* :attr:`pdpyras.PDSession.sleep_timer`: The initial cooldown factor
* :attr:`pdpyras.PDSession.sleep_timer_base`: Factor by which the cooldown time is increased after each unsuccessful attempt
* :attr:`pdpyras.PDSession.stagger_cooldown`: Randomizing factor for increasing successive cooldown wait times

Exponential Cooldown
********************
After each unsuccessful attempt, the client will sleep for a short period that
increases exponentially with each retry.

Let:

* a = :attr:`pdpyras.PDSession.sleep_timer_base`
* t\ :sub:`0` = ``sleep_timer``
* t\ :sub:`n` = Sleep time after n attempts
* ρ = :attr:`pdpyras.PDSession.stagger_cooldown`
* r = a random real number between 0 and 1, generated once per request

Assuming ρ = 0:

t\ :sub:`n` = t\ :sub:`0` a\ :sup:`n`

If ρ is nonzero:

t\ :sub:`n` = a (1 + ρ r) t\ :sub:`n-1`

Default Behavior
****************
By default, after receiving a status 429 response, sessions will retry the
request indefinitely until it receives a status other than 429, and this
behavior cannot be overridden. This is a sane approach; if it is ever
responding with 429, the REST API is receiving (for the given REST API key) too
many requests, and the issue should by nature be transient unless there is a
rogue process using the same API key and saturating its rate limit.

Also, it is default behavior when encountering status ``401 Unauthorized`` for
the client to immediately raise ``pdpyras.PDClientError``; this is a
non-transient error caused by an invalid credential.

However, both of these behaviors can be overridden by adding entries in the
retry dictionary. For instance, it may be preferable to error out instead of
hanging indefinitely to continually retry if another API process is saturating
the rate limit.

Setting the retry property
**************************
The property :attr:`pdpyras.PDSession.retry` allows customization of HTTP retry
logic. The client can be made to retry on other statuses (i.e.  502/400), up to
a set number of times. The total number of HTTP error responses that the client
will tolerate before returning the response object is defined in
:attr:`pdpyras.PDSession.max_http_attempts`, and this will supersede the
maximum number of retries defined in :attr:`pdpyras.PDSession.retry` if it is
lower.

**Example:**

.. code-block:: python

    # This will take about 30 seconds plus API request time, carrying out four
    # attempts with 2, 4, 8 and 16 second pauses between them, before finally
    # returning the status 404 response object for the user that doesn't exist:
    session.max_http_attempts = 4 # lower value takes effect
    session.retry[404] = 5 # this won't take effect
    session.sleep_timer = 1
    session.sleep_timer_base = 2
    response = session.get('/users/PNOEXST')

    # Same as the above, but with the per-status limit taking precedence, so
    # the total wait time is 62 seconds:
    session.max_http_attempts = 6
    response = session.get('/users/PNOEXST')

.. References:
.. -----------

.. _`Requests`: https://docs.python-requests.org/en/master/
 .. _`Errors`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYz-errors
.. _`Events API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview
.. _`PagerDuty API Reference`: https://developer.pagerduty.com/api-reference/
.. _`REST API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUw-rest-api-v2-overview
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions
