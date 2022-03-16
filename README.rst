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
This library supplies a class :class:`pdpyras.APISession` extending
`requests.Session`_ from the Requests_ HTTP library. It serves as a practical
and simple-as-possible-but-no-simpler HTTP client for accessing the PagerDuty
REST API and events API.

It takes care of all of the most common prerequisites and necessities
pertaining to accessing the API so that implementers can focus on the request
and response body schemas of each particular resource (as documented in our
`REST API Reference`_) and do what they need to get done.

Features
********
- Uses Requests' automatic HTTP connection pooling and persistence
- Tested in / support for Python 3.5 through 3.9
- Configurable cooldown/reattempt logic for handling rate limiting and
  transient HTTP or network issues
- Abstraction for `pagination`_, `wrapped entities`_, `API authentication`_ and
  more

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

Ultimately, we deemed most other libraries to be both overkill for this task
and also not very conducive to use for experimental API calls.

Copyright
*********
All the code in this distribution is Copyright (c) 2018 PagerDuty.

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

Alternately, if requests_ has already been installed locally, and ``urllib3``
is available, one can simply download `pdpyras.py`_ into the directory where it
will be used.

Usage Guide
-----------

Authentication
**************

All REST API examples included in this documentation assume that the variable
``session`` is an instance of :class:`APISession`. When constructing an
instance, the first argument, required, is always the API key used for `API
authentication`_.

If the session will be used for API endpoints that require a ``From`` header,
such as taking actions on incidents, and if using an account-level API key
(created by an administrator via the "API Access Keys" page in the
"Integrations" menu), it is recommended to also include the ``default_from``
keyword argument, or HTTP 400 responses will result when attempting to
use such endpoints.

Otherwise, if using a user's API key (created under "API Access" in the "User
Settings" tab of the user's profile), the user will be derived from the key
itself and ``default_from`` is not necessary.

Using a basic REST API key
++++++++++++++++++++++++++

For example, given an environment variable ``PD_API_KEY`` set to an
account-wide REST API key, and a dummy user in the PagerDuty account with email
address "api@example-company.com":

.. code-block:: python

    import os
    from pdpyras import APISession

    api_key = os.environ['PD_API_KEY']
    session = APISession(api_key, default_from="api@example-company.com")

Using an OAuth2 token
+++++++++++++++++++++

When using an OAuth2 token, pass the keyword argument ``auth_type='oauth2'``
or ``auth_type='bearer'`` to the constructor. This tells the client to set the
``Authorization`` header appropriately in order to use this type of API
credential.

Example:

.. code-block:: python

    session = APISession(oauth_token_here, auth_type='oauth2')

Note, obtaining an access token via the OAuth 2 flow is outside the purview of
an API client, and should be performed separately by your application.

For further information on OAuth 2 authentication with PagerDuty, refer to the
official documentation:

* `OAuth 2 Functionality <https://v2.developer.pagerduty.com/docs/oauth-2-functionality>`_
* `OAuth 2: PKCE Flow <https://v2.developer.pagerduty.com/docs/oauth-2-functionality-pkce>`_
* `OAuth 2: Authorization Code Grant Flow <https://v2.developer.pagerduty.com/docs/oauth-2-functionality-client-secret>`_


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

**Updating using ``put`` / ``rput``**: assuming there is a variable ``user``
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

General Concepts
****************
In all cases, when sending or receiving data through the REST API using
``pdpyras.APISession``, note the following:

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

Request and Response Bodies
+++++++++++++++++++++++++++
To set the request body in a post or put request, pass a ``json`` keyword
argument that will be JSON-encoded and sent as the body to the HTTP verb
method. To obtain the response from the API:

* If using ``request``, ``get``, ``post`` (etc) directly, a `requests.Response`_ 
  object is returned. That object's ``json()`` method will return the response
  body decoded from JSON as a Python dict object.
* If using the ``j*`` methods (``jget``, ``jpost`` etc) or the ``r*`` methods
  (``rget``, ``rpost`` etc), or any other method that makes API calls: objects
  returned will be from JSON-decoding the body of the API response if successful;
  otherwise :class:`PDClientError` will be raised.

Note, implementers are not insulated from having to work directly with the
schemas of resources in requests and responses. Rather, they must follow the
`REST API Reference`_ when working with objects representing the request and
response bodies. Generally speaking, the body should have a structure that
reflects the API schema, where:

* If the data type documented in the schema is
  `object <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#object>`_,
  then the corresponding type in Python will be ``dict``.
* If the data type documented in the schema is
  `array <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#array>`_,
  then the corresponding type in Python will be ``list``.

Using Special Features of Requests
++++++++++++++++++++++++++++++++++
Keyword arguments to the HTTP methods get passed through to the similarly-
named functions in `requests.Session`_. For additional options, please refer
to the documentation provided by the Requests project.

Wrapped Entities
****************
Main article: `wrapped entities <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYx-wrapped-entities>`_
(formerly the term "resource envelope" was used).

Most of PagerDuty's endpoints respond with their data inside of a key at the
root level of the JSON-encoded object in the response. The key is named after
the resource, whether singular or plural.

The "``r*`` methods" ``rput``, ``rpost`` and ``rget`` will perform the same
HTTP actions as ``put``, ``post`` and ``get``, although they will not return a
`requests.Response`_ object. Instead, they will return the contents of the
wrapped entity in the response, if the request was successful, and raise
:class:`pdpyras.PDClientError` otherwise. Furthermore, when sending a body via
the ``json`` keyword argument (for ``rpost``/``rput``), the value can be the
wrapped entity itself, as opposed to needing to be the full contents to be
JSON-encoded in the body including the wrapping.

The functions ``iter_all`` and ``iter_cursor`` will likewise yield results from
wrapped lists of entities, rather than lists in wrapping (the structure of the
API response).

Supported Endpoints
+++++++++++++++++++
The general rules are that the name of the wrapped resource key must follow
from the innermost resource name for the API path in question, and that the
"nodes" in the URL path (between forward slashes) must alternate between
resource type and ID.

**Supported endpoint example:** for ``/escalation_policies/{id}`` the wrapper
name for singular post/put is ``escalation_policy``, and for ``GET
/escalation_policies`` it is ``escalation_policies``. For
``/users/{id}/notification_rules`` the wrapper is named ``notification_rule``
for singular post/put and ``notification_rules`` for the index, ``GET
/users/{id}/notification_rules``.

**Unsupported endpoint example:** in the `user sessions <https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1users~1%7Bid%7D~1sessions/get>`_ API,
URLs are formatted as ``/users/{id}/sessions/{type}/{session_id}`` the wrapped
resource property name is ``user_sessions`` / ``user_session`` rather than
simply ``sessions`` / ``session``.

List of Non-conformal Endpoints
++++++++++++++++++++++++++++++++
The following list of APIs and endpoints (last updated: 2022-03-15) are
unsupported by methods ``rget``, ``rpost``, ``rput``, ``persist``, ``find``,
``iter_all``, ``list_all`` and ``dict_all`` because they do not follow the
classic schema conventions on which the functions are based. They can still be
used with the basic ``get``, ``post``, ``put`` and ``delete`` methods, as well
as the ``j*`` methods, which return the body of the response after
JSON-decoding.

* Analytics
* All Audit endpoints (:attr:`pdpyras.APISession.iter_cursor` should be used instead, as they feature cursor-based pagination)
* All Notification Subscription endpoints
* Paused Incident Reports
* The following Business Services endpoints:
    * ``POST /business_services/{id}/account_subscription``
    * ``GET /business_services/{id}/supporting_services/impacts``
    * ``GET /business_services/impactors``
    * ``GET /business_services/impacts``
    * ``[GET|PUT] /business_services/priority_thresholds``
* The following Incident API endpoints:
    * ``[GET|PUT] /incidents/{id}/business_services/impacts```: list or manually change any of an incident's impacts on business services
    * ``POST /incidents/{id}/responder_requests``: create a responder request for an incident
    * ``POST /incidents/{id}/snooze``: snooze an incident
* Event Orchestrations
* ``POST /schedules/{id}/overrides`` (create one or more schedule overrides)
* Service Dependencies
* ``POST /{entity_type}/{id}/change_tags`` (assign tags)
* Updating team membership (adding or removing users or escalation policies)
* Team notification subscriptions
* User sessions

Pagination
++++++++++
The method :attr:`pdpyras.APISession.iter_all` returns an iterator that yields
results from a resource index, automatically incrementing the ``offset``
parameter to advance through each page of data and make API requests on-demand.

For all endpoints that support cursor-based pagination,
:attr:`pdpyras.APISession.iter_cursor` should be used instead.

Note, one can perform `filtering
<https://v2.developer.pagerduty.com/docs/filtering>`_ with iteration to constrain
constrain the range of results, by passing in a dictionary object as the ``params``
keyword argument. Any parameters will be automatically merged with the pagination
parameters and serialized into the final URL, so there is no need to manually
construct the URL, i.e. appending ``?key1=value1&key2=value2``.

**Example:** Find all users with "Dav" in their name/email (i.e. Dave/David) in
the PagerDuty account:

.. code-block:: python

    for dave in session.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

Also, note, as of version 2.2, there are the methods
:attr:`pdpyras.APISession.list_all` and :attr:`pdpyras.APISession.dict_all`
which return a list or dictionary of all results, respectively.

**Example:** Get a dictionary of all users, keyed by email, and use it to find
the ID of the user whose email is ``bob@example.com``:

.. code-block:: python

    users = session.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

Pagination Disclaimers
++++++++++++++++++++++

**Regarding performance:**

Because HTTP requests are made synchronously and not in multiple threads, the
data will be retrieved one page at a time and the functions ``list_all`` and
``dict_all`` will not return until after the HTTP response from the final API
call is received. Simply put, the functions will take longer to return if the
total number of results is higher.

**On updating, creating or deleting records while iterating through them:**

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

Multi-Updating
++++++++++++++
Introduced in version 2.1 is support for automatic entity wrapping and unwrapping
in multi-update actions.

As of this writing, multi-update support includes the following actions:

* `PUT /incidents <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODEzOQ-manage-incidents>`_
* `PUT /incidents/{id}/alerts <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODE0NA-manage-alerts>`_
* PUT /priorities (documentation not yet published as of 2022-03-15, but the endpoint is functional)

**Please note:** as of yet, merging incidents is not supported by ``rput``.
For this and other unsupported endpoints, you will need to call ``put`` directly,
or ``jput`` to get the response body as a dictionary object.

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

Error Handling
**************
What happens when, for any of the ``r*`` methods, the API responds with a
non-success HTTP status? Obviously in this case, they cannot return the
JSON-decoded response, because the response would not be the sought-after data
but a different schema altogether (see: `Errors`_), and this would put the onus
on the end user to distinguish between success and error based on the structure
of the returned dictionary object.

Instead, when this happens, a :class:`pdpyras.PDClientError` exception is
raised. The advantage of this design lies in how the methods can always be
expected to return the same sort of data, and if they can't, the program flow
that depends on getting this specific structure of data is appropriately
interrupted. Moreover, because (as of version 2) this exception class will have
the `requests.Response`_ object as its ``response`` property (whenever the
exception pertains to a HTTP error), the end user can define specialized error
handling logic in which the REST API response data (i.e. headers, code and body)
are directly available.

For instance, the following code prints "User not found" in the event of a 404,
raises the underlying exception in the event of an incorrect API access token (401
Unauthorized) or non-transient network error, prints out the user's email if
the user exists, and does nothing otherwise:

.. code-block:: python

    try:
        user = session.rget("/users/PJKL678")
        print(user['email'])

    except pdpyras.PDClientError as e:
        if e.response:
            if e.response.status_code == 404:
                print("User not found")
            elif e.response.status_code == 401:
                raise e
        else:
            raise e

HTTP Retry Logic
****************
By default, after receiving a response, :attr:`pdpyras.PDSession.request` will
return the `requests.Response`_ object unless its status is ``429`` (rate
limiting), in which case it will retry until it gets a status other than ``429``.

The property :attr:`pdpyras.PDSession.retry` allows customization in this
regard, so that the client can be made to retry on other statuses (i.e.
502/400), up to a set number of times. The total number of HTTP error responses
that the client will tolerate before returning the response object is defined
in :attr:`pdpyras.PDSession.max_http_attempts`, and this will supersede the
maximum number of retries defined in
:attr:`pdpyras.PDSession.retry`.

**Example:**

The following will take about 30 seconds plus API request time
(carrying out four attempts, with 2, 4, 8 and 16 second pauses between them),
before finally returning with the status 404 `requests.Response`_ object:

.. code-block:: python

    session.retry[404] = 5
    session.max_http_attempts = 4
    session.sleep_timer = 1
    session.sleep_timer_base = 2
    # isinstance(session, pdpyras.APISession)
    response = session.get('/users/PNOEXST')

**Default Behavior:**

Note that without specifying any retry behavior:

* When encountering status 429 (rate limiting), the client will retry
  indefinitely. This is a sane approach; if it is ever responding
  with 429, this means that the REST API is receiving (for the given REST API
  key) too many requests, and the issue should by nature be transient.
* When encountering status 401 (unauthorized), the client will immediately
  raise :class:`pdpyras.PDClientError`, as this can be considered a
  non-transient error under any circumstance.

It is still possible to override these behaviors by updating
:attr:`pdpyras.PDSession.retry`, but it is not recommended.

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

To be able to rebuild the documentation and release a new version, first
make sure you have `make <https://www.gnu.org/software/make/>`_ and `pip
<https://pip.pypa.io/en/stable/installation/>`_ installed.

Next, install Python dependencies for building and publishing:

.. code-block:: shell

    pip install -r requirements-publish.txt 

Before publishing
*****************

A pull request for releasing a new version should be created, which should include at least:

* An update to CHANGELOG.rst, where all lines corresponding to community contributions end with (in parentheses) the GitHub user handle of the contributor, a slash, and a link to the pull request.
* A change in the version number in both setup.py and pdpyras.py, to a new version that follows `Semantic Versioning <https://semver.org/>`_.

The pull request should then be reviewed before committing a rebuild of the
documentation. This is because it adds many file changes that are not meant
to be reviewed manually, as they are generated. Documentation can be built
locally for review and proofreading via:

.. code-block:: shell

    make docs

The documentation can then be viewed in the file ``docs/index.html``.

Publishing a new version
************************
Once the pull request is approved, rebuild the documentation, commit/push
the changes, and merge.

Once the changes are merged, tag the merge onto the main branch as
``v{version}``, i.e. ``v4.4.0``, and with that as the current git head (and
a clean local file tree) run:

.. code-block:: shell

    make publish

.. References:
.. -----------

.. _Requests: https://docs.python-requests.org/en/master/
.. _`API authentication`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUx-authentication
.. _`Errors`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYz-errors
.. _`HTTP Request Headers`: https://v2.developer.pagerduty.com/docs/rest-api#http-request-headers
.. _`REST API Reference`: https://developer.pagerduty.com/api-reference/
.. _`pdpyras.py`: https://raw.githubusercontent.com/PagerDuty/pdpyras/master/pdpyras.py
.. _`resource index`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU0-endpoints#resources-index
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _`wrapped entities`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYx-wrapped-entities
.. _make: https://www.gnu.org/software/make/
.. _pagination: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU4-pagination
.. _pypd: https://github.com/PagerDuty/pagerduty-api-python-client/
.. _requests.Response.json: https://docs.python-requests.org/en/master/api/#requests.Response.json
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session.request: https://docs.python-requests.org/en/master/api/#requests.Session.request
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions

.. |circleci-build| image:: https://circleci.com/gh/PagerDuty/pdpyras.svg?style=svg
    :target: https://circleci.com/gh/PagerDuty/pdpyras
