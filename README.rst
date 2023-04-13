===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A lightweight Python client for the PagerDuty REST API.

Also includes clients for the Events and Change Events APIs.

|circleci-build|

* `GitHub repository <https://github.com/PagerDuty/pdpyras>`_
* `Documentation <https://pagerduty.github.io/pdpyras>`_
* `Changelog <https://github.com/PagerDuty/pdpyras/tree/master/CHANGELOG.rst>`_

About
-----
This library supplies classes extending `requests.Session`_ from the Requests_
HTTP library that serve as Python interfaces to the `REST API v2`_ and `Events
API v2`_ of PagerDuty. One might call it an opinionated wrapper library. It was
designed with the philosophy that Requests_ is a perfectly adequate HTTP
client, and that abstraction should focus only on the most generally applicable
and frequently-implemented core features, requirements and tasks. Design
decisions concerning how any particular PagerDuty resource is accessed or
manipulated through APIs are left to the user or implementer to make.

Features
********
- Uses Requests' automatic HTTP connection pooling and persistence
- Tested in / support for Python 3.5 through 3.9
- Abstraction layer for authentication, pagination, scalar filtering and
  wrapped entities
- Configurable cooldown/reattempt logic for handling rate limiting and
  transient HTTP or network issues

History
*******
This module was borne of necessity for a basic API client to eliminate code
duplication in some of PagerDuty Support's internal Python-based API tooling.

We found ourselves frequently performing REST API requests using beta or
non-documented API endpoints for one reason or another, so we needed the client
that provided easy access to features of the underlying HTTP library (i.e. to
obtain the response headers, or set special request headers). We also needed
something that eliminated tedious tasks like querying objects by name,
pagination and authentication. Finally, we discovered that the way we were
using `Requests`_ wasn't making use of its connection pooling feature, and
wanted a way to easily enforce this as a standard practice.

We evaluated at the time a few other open-source API libraries and deemed them
to be either overkill for our purposes or not giving the implementer enough
control over how API calls were made.

Copyright
*********
All the code in this distribution is Copyright (c) 2023 PagerDuty.

``pdpyras`` is made available under the MIT License:

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

Warranty
********
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

Installation
------------
If ``pip`` is available, it can be installed via:

.. code-block:: shell

    pip install pdpyras

Alternately, if the Requests_ Python library has already been installed
locally, one can simply download `pdpyras.py`_ into the directory where it will
be used.

Usage Guide
-----------

Authentication
**************

The first step is to construct a session instance. The first argument to the
constructor is the API key used to access the API:

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

If the `REST API v2`_ session will be used for API endpoints that require a
``From`` header, such as those that take actions on incidents, and if it is
using an account-level API key (created by an administrator via the "API Access
Keys" page in the "Integrations" menu), it is recommended to also include the
``default_from`` keyword argument. If one does not, or does not set the header
in a keyword argument when making the request to such an API endpoint, a HTTP
400 response will result.

Otherwise, if using a user's API key (created under "API Access" in the "User
Settings" tab of the user's profile), the user will be derived from the key
itself and ``default_from`` is not necessary.

When encountering status 401 (unauthorized), the client will immediately raise
``pdpyras.PDClientError``, as this can be considered a non-transient error.

Basic Usage
***********

Some examples of usage:

**Basic getting:** Obtain a user profile as a dict object:

.. code-block:: python

    # Using get:
    response = session.get('/users/PABC123')
    user = None

    if response.ok:
      user = response.json()['user']

    # Using rget:
    user = session.rget('/users/PABC123')

**Pagination (1):** Iterate over all users and print their ID, email and name:

.. code-block:: python

    for user in session.iter_all('users'):
        print(user['id'], user['email'], user['name'])

**Pagination (2):** Compile a list of all services with "SN" in their name:

.. code-block:: python

    services = session.list_all('services', params={'query': 'SN'})

**Cursor-based pagination:** look up audit trail records for all PagerDuty objects going back 24 hours:

.. code-block:: python

    audit_records = list(session.iter_cursor('/audit/records'))

**Querying:** Find a user exactly matching email address ``jane@example35.com``

.. code-block:: python

    user = session.find('users', 'jane@example35.com', attribute='email')

**Updating using put / rput**: assuming there is a variable ``user``
defined that is a dictionary representation of a PagerDuty user,

.. code-block:: python

    if user is not None:
      updated_user = None

      # (1) using put directly:
      response = session.put(user['self'], json={
        'user':{'type':'user', 'name': 'Jane Doe'}
      })
      if response.ok:
        updated_user = response.json()['user']

      # (2) using rput (no entity wrapping required):
      try:
        updated_user = session.rput(user['self'], json={
            'type':'user', 'name': 'Jane Doe'
        })
      except PDClientError:
        updated_user = None

**Updating/creating using persist (idempotent create/update function)**:
assuming a dict object ``user_data`` is defined, and it is structured like a
PagerDuty user object, containing at least the name and email address fields,
this will look for a user with its ``email`` field equal to the ``email`` value
in ``user_data``, and update that user according to the contents of
``user_data`` (or create one with attributes according to ``user_data`` if it
doesn't already exist):

.. code-block:: python

      try:
        updated_user = session.persist('users', 'email', user_data, update=True)
      except PDClientError:
        updated_user = None

**Multiple update:** acknowledge all triggered incidents assigned to user with
ID ``PHIJ789``. Note that to acknowledge, we need to set the ``From`` header.
This example assumes that ``admin@example.com`` corresponds to a user in the
PagerDuty account:

.. code-block:: python

    # Query incidents
    incidents = session.list_all(
        'incidents',
        params={'user_ids[]':['PHIJ789'],'statuses[]':['triggered']}
    )

    # Change their state
    for i in incidents:
        i['status'] = 'acknowledged'

    # PUT the updated list back up to the API
    updated_incidents = session.rput('incidents', json=incidents)

Logging and debugging
*********************
When a session is created, a
`Logger object <https://docs.python.org/3/library/logging.html#logger-objects>`_
is created as follows:

* Its level is unconfigured (``logging.NOTSET``) which causes it to defer to the 
  level of the parent logger, which is the root logger unless specified
  otherwise (see `Logging Levels
  <https://docs.python.org/3/library/logging.html#logging-levels>`_).
* The logger is initially not configured with any handlers. Configuring
  handlers is left to the discretion of the implementer (see `logging.handlers
  <https://docs.python.org/3/library/logging.handlers.html>`_)
* The logger can be accessed through the property :attr:`pdpyras.PDSession.log`.
  The property is mutable and can be set to a custom logger object.

In version 4.6.0 and later, for debugging and API request troubleshooting, one
can enable and disable sending log messages to command line output via the
:attr:`pdpyras.PDSession.debug` property as follows:

.. code-block:: python

    # Method 1: keyword argument, when constructing a new session:
    session = pdpyras.APISession(api_key, debug=True)

    # Method 2: on an existing session, by setting the property:
    session.debug = True

    # to disable:
    session.debug = False


What this does is assign a `logging.StreamHandler
<https://docs.python.org/3/library/logging.handlers.html#streamhandler>`_
directly to the session's logger and set the log level to debug (``logging.DEBUG``).
All log messages are then sent directly to ``sys.stderr``.

General API Concepts
********************
In all cases, when sending or receiving data through the REST API using
:class:`pdpyras.APISession`, the following will apply.

URLs
++++
* **There is no need to include the API base URL.** Any path relative to the web
  root, leading slash or no, is automatically appended to the base URL when
  constructing an API request, i.e. one can specify ``users/PABC123`` or
  ``/users/PABC123`` instead of ``https://api.pagerduty.com/users/PABC123``.
* One can also pass the full URL of an API endpoint and it will still work, i.e.
  the ``self`` property of any object can be used, and there is no need to strip
  out the API base URL.
* The ``r*`` methods, i.e. ``rget``, can accept a dictionary object
  representing an API resource in place of a URL (in which case the value at
  the ``self`` key will be used as the URL).

Request and response bodies
+++++++++++++++++++++++++++
To set the request body in a post or put request, pass a ``json`` keyword
argument that will be JSON-encoded and sent as the body to the HTTP verb
method. To obtain the response from the API:

* If using ``request``, ``get``, ``post`` (etc) directly, a `requests.Response`_ 
  object is returned. That object's ``json()`` method will return the response
  body decoded from JSON as a Python dict object.
* If using the ``j*`` methods (``jget``, ``jpost`` etc.) or the ``r*`` methods
  (``rget``, ``rpost`` etc), or any other method that makes API calls: objects
  returned will be from JSON-decoding the body of the API response if successful;
  otherwise :class:`PDClientError` will be raised.

Resource schemas
++++++++++++++++
Main article: `Resource Schemas <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU5-resource-schemas>`_

The details of any given resource's schema can be found in the request and
response examples from the `REST API Reference`_ pages for the resource's
respective API, as well as the page documenting the resource type itself.

Data types
++++++++++
Main article: `Types <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types>`_

Note these analogues in structure between the JSON schema and the object
in Python:

* If the data type documented in the schema is
  `object <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#object>`_,
  then the corresponding type of the Python object will be ``dict``.
* If the data type documented in the schema is
  `array <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#array>`_,
  then the corresponding type of the Python object will be ``list``.
* Generally speaking, the data type in the decoded object is according to the
  design of the `json <https://docs.python.org/3/library/json.html>`_ Python library.

For example, consider the example structure of an escalation policy as given in the
`GET /escalation_policies/{id} <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODEyNg-get-an-escalation-policy>`_
API reference page. To access the name of the second target in level 1,
assuming the variable ``ep`` represents the unwrapped escalation policy object:

.. code-block:: python

    ep['escalation_rules'][0]['targets'][1]['summary']
    # "Daily Engineering Rotation"

To add a new level, one would need to create a new 
`escalation rule <https://developer.pagerduty.com/api-reference/c2NoOjI3NDgwMjI-escalation-rule>`_
and then append it to the ``escalation rules`` property. Using the example
given in the above API reference page:

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

Using HTTP client library features
++++++++++++++++++++++++++++++++++
For all request functions: keyword arguments to the HTTP verb methods and their
``r*`` / ``j*`` equivalents get passed through to the similarly-named
functions in `requests.Session`_. Furthermore, the methods ``get``, ``post``,
``put``, ``delete`` and ``request`` return `requests.Response`_ objects, whose
properties contain information about the request and response.

Note also that since :class:`pdpyras.PDSession` is subclassed directly from
`requests.Session`_ , it behaves as a ``Session`` object and so all of the
documented features of that class can also be used. For example, to configure
``10.42.187.3:4012`` as a proxy for HTTPS traffic:

.. code-block:: python

    session.proxies.update({'https': '10.42.187.3:4012'})

For documentation on additional options and features, refer to
`Requests' developer interface documentation <https://requests.readthedocs.io/en/latest/api/>`_

Wrapped Entities
****************

Many of PagerDuty's endpoints respond with their data inside of a key at the
root level of the JSON-encoded object in the response, or require the request
body be wrapped in another object that contains a single key. The key is
typically named after the last or second to last node of the URL's path
(between "/"), and is a singular (for an individual resource) or plural (for a
collection of resources) noun. 

This client provides an abstraction layer for wrapped entities so that there
is no need to access a key in the JSON-decoded response to get the content, or
wrap the object to be JSON-encoded and sent as the response body in another
dictionary with a single key that differs based on which API endpoint is in
use.

Functions that implement entity wrapping
+++++++++++++++++++++++++++++++++++++

Generally, instead of returning a `requests.Response`_ object or requiring
entity wrapping in the object to be JSON-encoded as the request body, the
following methods will accept an unwrapped entity to be sent in the request
body via the ``json`` keyword argument, and/or will return the contents of the
wrapped entity in the response from the API: If the request's status was not
success, or a wrapped entity could not be found in the response,
:class:`pdpyras.PDHTTPError` will be raised.

* The "``r*`` methods" ``rput``, ``rpost`` and ``rget``. They will perform the
  same HTTP actions as ``put``, ``post`` and ``get`` and similarly accept the
  same keyword arguments as ``requests.Session.request``. the ``json`` keyword
  argument (for ``rpost``/``rput``), the value can be the
* :attr:`pdpyras.APISession.find`, :attr:`pdpyras.APISession.iter_all`,
  :attr:`pdpyras.APISession.list_all` and :attr:`pdpyras.APISession.dict_all`
  each assume that the API index endpoint being queried follows the classic
  entity wrapping conventions.
* :attr:`pdpyras.APISession.persist` uses ``rput``, ``rpost`` and ``find``
* :attr:`pdpyras.APISession.iter_cursor` uses the ``attribute`` keyword
  argument to unwrap results, if specified; otherwise it determines the wrapper
  automatically.

How to tell if an endpoint has entity wrapping
++++++++++++++++++++++++++++++++++++++++++++++
The following 

# 1:
#   If the endpoint's response body or expected request body contains only one
#   property that points to all the content of the requested object, or if it is
#   a request made to an endpoint that supports pagination*, entity wrapping is
#   enabled for the endpoint.
#
# 2:
#   If there are any other properties, and the endpoint does not support
#   pagination, entity wrapping is disabled, and using methods on them that
#   require entity wrapping will produce warnings and/or raise exceptions.
#
# 3: 
#   For all endpoints that support pagination but whose responses contain any
#   properties other than the wrapped list of response entities and the standard
#   pagination properties (i.e. limit, offset, more, cursor), those properties
#   are discarded from responses, and only the response entities are returned.
#
# 4:
#   As with previous versions, entity wrapping can be bypassed for request
#   bodies by passing a complete request object (i.e. a dictionary that when
#   marshaled to JSON will represent the whole request body structure that is
#   expected by the endpoint).
#
# * An endpoint is said to support pagination if it takes the query parameters
# ``limit`` and either ``offset`` (classic pagination) or ``cursor``
# (cursor-based pagination).


Pagination
**********

The method :attr:`pdpyras.APISession.iter_all` returns an iterator that yields
results from an endpoint that returns a wrapped collection of resources. By
default it will use classic, a.k.a. numeric pagination. If the endpoint
supports cursor-based pagination, it will use that method to iterate through
results instead. The methods :attr:`pdpyras.APISession.list_all` and
:attr:`pdpyras.APISession.dict_all` will request all pages of the collection
and return the results as a list or dictionary, respectively.

Pagination functions require that the API endpoint being requested has entity
wrapping enabled.

To pass query parameters to the endpoint, all pagination methods accept a
``params`` keyword argument (a dictionary) that is sent through to
:attr:`pdpyras.APISession.request`. Any parameters in this keyword argument
will be automatically merged with the pagination parameters and serialized into
the final URL, so there is no need to manually construct the URL, i.e.
appending ``?key1=value1&key2=value2``.

**Example:** Find all users with "Dav" in their name/email (i.e. Dave/David) in
the PagerDuty account:

.. code-block:: python

    for dave in session.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

**Example:** Get a dictionary of all users, keyed by email, and use it to find
the ID of the user whose email is ``bob@example.com``:

.. code-block:: python

    users = session.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

Performance
+++++++++++
Because HTTP requests are made synchronously and not in multiple threads,
requesting all pages of data will happen one page at a time and the functions
``list_all`` and ``dict_all`` will not return until after the final HTTP
response. Simply put, the functions will take longer to return if the total
number of results is higher.

Completeness of results
+++++++++++++++++++++++
If at any point a pagination function cannot retrieve a page due to a
non-transient HTTP error, it will raise an exception. This ensures that the
results returned are always complete. However, if 
 a partial result is still acceptable, one can override
this behavior by setting the
:attr:`pdpyras.APISession.require_complete_results` attribute of the session to
``False``. Then, when an error is encountered, ``iter_all`` will simply stop
iterating when it encounters a HTTP error, and the ``*_all`` methods will
return the partial results instead of discarding the whole set.

Updating, creating or deleting while paginating
+++++++++++++++++++++++++++++++++++++++++++++++
If performing page-wise operations, i.e. making changes immediately after
fetching each page of results, rather than pre-fetching all objects and then
operating on them (i.e. with :attr:`pdpyras.APISession.list_all`), one must be
cautious not to perform any changes to the results that would affect the set
over which iteration is taking place, such as creating objects, deleting them,
or modifying them in such a way that their status of being in the set of
results changes.

This is because indexes' contents are updated in real time, and this can affect
the position of objects in the overall list (and thus the edges of each page).
Changes made apart from the API client can have the same effect.

To elaborate: let's say that each resource object in the full list is a page in
a notebook  Classic pagination with ``limit=100`` is essentially "go through
100 pages, then repeat starting with the 101st page, then with the 201st, etc."
Deleting records in between these 100-at-a-time pagination requests would be
like tearing out pages after reading them. At the time of the second page
request, what was originally the 101st page before starting will shift to
become the first page after tearing out the first hundred pages. Thus, when
going to the 101st page after finishing tearing out the first hundred pages,
the second hundred pages will be skipped over, and similarly for pages 401-500,
601-700 and so on. If attaching pages, the opposite happens: some results will be
returned more than once, because they get bumped to the next group of 100 pages.

Multi-updating
**************
Introduced in version 2.1 is support for multi-update actions using ``rput``.
As of this writing, multi-update support includes the following endpoints:

* `PUT /incidents <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODEzOQ-manage-incidents>`_
* `PUT /incidents/{id}/alerts <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODE0NA-manage-alerts>`_
* PUT /priorities (documentation not yet published as of 2022-03-15, but the endpoint is functional)

To use, simply pass in a list of objects or references (dictionaries having a
structure according to the API schema reference for that object type) to the
``json`` keyword argument of :attr:`pdpyras.APISession.rput`, and the final
payload will be an object with one property named after the resource,
containing that list.

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

It is important to note, however, that certain actions such as updating
incidents require the ``From`` header, which should be the login email address
of a valid PagerDuty user. To set this, pass it through using the ``headers``
keyword argument, or set the :attr:`pdpyras.APISession.default_from` property,
or pass the email address as the ``default_from`` keyword argument when
constructing the session initially.

Error handling
**************
What happens when, for any of the methods that do not return
`requests.Response`_, the API response is a non-success HTTP status, is that it
will not return the decoded body. Instead, when this happens, a
:class:`pdpyras.PDClientError` exception is raised. This way, methods can
always be expected to return the same structure of data based on the API being
used. If there is a break in this expectation, the flow is appropriately
interrupted. 

As of version 2, this exception class has the `requests.Response`_ object as
its ``response`` property (whenever the exception pertains to a HTTP error).
The implementer can thus define specialized error handling logic in which the
REST API response data (i.e. headers, code and body) are directly available.

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
assumed that the error pertains to a HTTP request:

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

HTTP retry logic
****************
Session objects support retrying API requests if they receive a non-success
response or if they encounter a network error. This behavior is configurable
through the following properties, which are each documented with further
implementation details:

* :attr:`pdpyras.PDSession.max_http_attempts`
* :attr:`pdpyras.PDSession.max_network_attempts`
* :attr:`pdpyras.PDSession.sleep_timer`
* :attr:`pdpyras.PDSession.sleep_timer_base`
* :attr:`pdpyras.PDSession.stagger_cooldown`

Cooldown
++++++++
After each unsuccessful attempt, if retry logic is active for the given HTTP
status, the client will sleep for a short period that increases exponentially
with each retry. 

Let:

* a = ``sleep_timer_base``
* t\ :sub:`0` = ``sleep_timer``
* t\ :sub:`n` = Sleep time after n attempts
* ρ = ``stagger_cooldown``
* r = a random real number between 0 and 1


Assuming ρ = 0:

t\ :sub:`n` = t\ :sub:`0` a\ :sup:`n`

If ρ is nonzero:

t\ :sub:`n` = a (1 + ρ r) t\ :sub:`n-1`

Rate Limiting
+++++++++++++
By default, after receiving a status 429 response, sessions will retry the
request indefinitely until it receives a status other than 429. This is a sane
approach; if it is ever responding with 429, the REST API is receiving (for the
given REST API key) too many requests, and the issue should by nature be
transient unless there is a rogue process using the key and saturating its rate
limit.

HTTP retry configuration
++++++++++++++++++++++++
The property :attr:`pdpyras.PDSession.retry` allows customization of HTTP retry
logic, so that the client can be made to retry on other statuses (i.e.
502/400), up to a set number of times. The total number of HTTP error responses
that the client will tolerate before returning the response object is defined
in :attr:`pdpyras.PDSession.max_http_attempts`, and this will supersede the
maximum number of retries defined in :attr:`pdpyras.PDSession.retry`.

**Example:**

The following will take about 30 seconds plus API request time
(carrying out four attempts, with 2, 4, 8 and 16 second pauses between them),
before finally returning with the status 404 `requests.Response`_ object:

.. code-block:: python

    session.retry[404] = 5
    session.max_http_attempts = 4
    session.sleep_timer = 1
    session.sleep_timer_base = 2
    response = session.get('/users/PNOEXST')


Events API
**********

As an added bonus, ``pdpyras`` provides an additional Session class for submitting
alert data to the Events API and triggering incidents asynchronously:
:class:`pdpyras.EventsAPISession`. It has most of the same features as
:class:`pdpyras.APISession`:

* Connection persistence
* Automatic cooldown and retry in the event of rate limiting or a transient network error
* Setting all required headers
* Configurable HTTP retry logic

To instantiate a session object, pass the constructor the routing key. Code
samples in this section will assume a variable named ``session`` constructed in
this way. For example, given an environment variable ``PD_API_KEY`` set to an
events API v2 (or global event routing) API key:

.. code-block:: python

    import os
    import pdpyras

    routing_key = os.environ['PD_API_KEY']
    session = pdpyras.EventsAPISession(routing_key)

To transmit alerts and perform actions through the events API, one would use:

* :attr:`pdpyras.EventsAPISession.trigger`
* :attr:`pdpyras.EventsAPISession.acknowledge`
* :attr:`pdpyras.EventsAPISession.resolve`


**Example 1:** Trigger an event and use the PagerDuty-supplied deduplication key to resolve it later:

.. code-block:: python

    dedup_key = session.trigger("Server is on fire", 'dusty.old.server.net')
    # ...
    session.resolve(dedup_key)

**Example 2:** Trigger an event, specifying a dedup key, and use it to later acknowledge the incident

.. code-block:: python

    session.trigger("Server is on fire", 'dusty.old.server.net',
        dedup_key='abc123')
    # ...
    session.acknowledge('abc123')

Change Events API
*****************

To submit a change event, create an instance of
:class:`pdpyras.ChangeEventsAPISession`, passing an Events API v2 key to the
class constructor as with :class:`EventsAPISession`. Then, call
:attr:`pdpyras.ChangeEventsAPISession.submit`, i.e.

.. code-block:: python

    session.submit("new build finished at latest HEAD", source="automation")


Contributing
------------
Bug reports and pull requests to fix issues are always welcome, as are
contributions to the built-in documentation.

If adding features, or making changes, it is recommended to update or add tests
and assertions to the appropriate test case class in ``test_pdpyras.py`` to ensure
code coverage. If the change(s) fix a bug, please add assertions that reproduce
the bug along with code changes themselves, and include the GitHub issue number
in the commit message.

Releasing
---------
(Target audience: package maintainers)

Initial Setup
*************

To be able to rebuild the documentation and release a new version, first make
sure you have `make <https://www.gnu.org/software/make/>`_ and `pip
<https://pip.pypa.io/en/stable/installation/>`_ installed in your shell
environment.

Next, install Python dependencies for building and publishing:

.. code-block:: shell

    pip install -r requirements-publish.txt 

Before publishing
*****************

You will need valid user accounts on both ``pypi.org`` and ``test.pypi.org``
that have the "Maintainer" role on the project.

Perform end-to-end publish and installation testing
++++++++++++++++++++++++++++++++++++++++++++++++++++

To test publishing and installing from the package index, first make sure you
have a valid user account on ``test.pypi.org`` that has publisher access to the
project as on ``pypi.org``.

Note, once a release is uploaded, it is no longer possible to upload a release
with the same version number, even if that release is deleted. For that reason,
it is a good idea to first add a suffix, i.e. ``-dev001``, to ``__version__``
in ``setup.py``.

To perform end-to-end tests, run the following, entering credentials for
``test.pypi.org`` when prompted:

.. code-block:: shell

    make testpublish

The make target ``testpublish`` performs the following:

* Build the Python egg in ``dist/``
* Upload the new library to ``test.pypi.org``
* Test-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv that does not already have the library installed, to test
  installing for the first time
* Tests-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv where the library is already installed, to test upgrading

If any errors are encountered, the script should immediately exit. Errors
should be investigated and mitigated before publishing. To test again,
temporarily change ``__version__`` so that it counts as a new release
and gets uploaded, and set it to the desired version before the actual
release.

Merge changes and tag
+++++++++++++++++++++

A pull request for releasing a new version should be created, which along with
the functional changes should also include at least:

* An update to the changelog, where all items corresponding to community
  contributions end with (in parentheses) the GitHub user handle of the
  contributor, a slash, and a link to the pull request (see CHANGELOG.rst for
  preexisting examples).
* A change in the version number in both setup.py and pdpyras.py, to a new
  version that follows `Semantic Versioning <https://semver.org/>`_.
* Rebuilt HTML documentation

The HTML documentation can be rebuilt with the ``docs`` make target:

.. code-block:: shell

    make docs

After rebuilding the documentation, it can then be viewed by opening the file
``docs/index.html`` in a web browser. Including rebuilt documentation helps
reviewers by not requiring them to have the documentation-building tools
installed.

Once the pull request is approved, merge, then checkout main and tag:

.. code-block:: shell

    git checkout main && \
      git pull origin main && \
      git tag "v$(python -c 'from pdpyras import __version__; print(__version__)')" && \
      git push --tags origin main

Publishing a new version
************************

Once the changes are merged and tagged, make sure your local repository clone
has the ``main`` branch checked out at the latest avialable commit, and the
local file tree is clean (has no uncommitted changes). Then run:

.. code-block:: shell

    make publish

.. References:
.. -----------

.. _`REST API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUw-rest-api-v2-overview
.. _`Events API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview
.. _Requests: https://docs.python-requests.org/en/master/
.. _`Errors`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYz-errors
.. _`PagerDuty API Reference`: https://developer.pagerduty.com/api-reference/
.. _`PagerDuty Developer Platform Documentation`: https://developer.pagerduty.com/docs/
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _make: https://www.gnu.org/software/make/
.. _requests.Response.json: https://docs.python-requests.org/en/master/api/#requests.Response.json
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session.request: https://docs.python-requests.org/en/master/api/#requests.Session.request
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions

.. |circleci-build| image:: https://circleci.com/gh/PagerDuty/pdpyras.svg?style=svg
    :target: https://circleci.com/gh/PagerDuty/pdpyras
