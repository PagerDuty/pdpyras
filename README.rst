===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A minimal, practical Python client for the PagerDuty REST API.

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
- Efficient API access through automatic HTTP connection pooling and
  persistence
- Tested in / support for Python 3.5 through 3.9
- Configurable cooldown/reattempt logic for rate limiting and transient network
  problems
- Inclusion of required `HTTP Request Headers`_ for PagerDuty REST API requests
- Bulk data retrieval and iteration over `resource index`_ endpoints with
  pagination
- Individual object retrieval by name
- API request profiling
- Bonus Events API client

History
*******
This module was borne of necessity for a basic, reusable API client to
eliminate code duplication in some of PagerDuty Support's internal Python-based
API tools. We needed something that could get the job done without reinventing
the wheel or getting in the way.

We also frequently found ourselves performing REST API requests using beta or
non-documented API endpoints for one reason or another, so we also needed a
client that provided easy access to features of the underlying HTTP library
(i.e. to obtain the response headers, or set special request headers). We
needed something that eliminated tedious tasks like querying, `pagination`_ and
header-setting commonly associated with REST API usage. Finally, we discovered
that the way we were using `requests`_ wasn't making use of connection re-use,
and wanted a way to easily enforce this as a standard practice.

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

Basic Usage
***********

Some examples of usage:

**Basic getting:** Obtain a user profile as a dict object:

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']
    session = APISession(api_token)

    # Using requests.Session.get:
    response = session.get('/users/PABC123')
    user = None

    if response.ok:
        user = response.json()['user']

    # Or, more succinctly:
    user = session.rget('/users/PABC123')

**Iteration (1):** Iterate over all users and print their ID, email and name:

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']
    session = APISession(api_token)

    for user in session.iter_all('users'):
        print(user['id'], user['email'], user['name'])

**Iteration (2):** Compile a list of all services with "SN" in their name:

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']

    session = APISession(api_token)
    services = list(session.iter_all('services', params={'query': 'SN'}))

**Querying and updating:** Find a user exactly matching email address ``jane@example35.com``
and update their name to "Jane Doe":

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']
    session = APISession(api_token)

    user = session.find('users', 'jane@example35.com', attribute='email')

    if user is not None:
        # Update using put directly:
        updated_user = None
        response = session.put(user['self'], json={
            'user':{'type':'user', 'name': 'Jane Doe'}
        })
        if response.ok:
            updated_user = response.json()['user']

        # Alternately / more succinctly:
        try:
            updated_user = session.rput(user['self'], json={
                'type':'user', 'name': 'Jane Doe'
            })
        except PDClientError:
            updated_user = None

**Multiple update:** acknowledge all triggered incidents assigned to user with
ID ``PHIJ789``. Note that to acknowledge, we need to set the ``From`` header.
This example assumes that ``admin@example.com`` corresponds to a user in the
PagerDuty account:

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']
    session = APISession(api_token, default_from='admin@example.com')

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

Using an OAuth 2 Access Token to Authenticate
*********************************************

When using an OAuth2 token, include the keyword argument ``auth_type='oauth2'``
or ``auth_type='bearer'`` to the constructor. This tells the client to set the
``Authorization`` header appropriately in order to use this type of API
credential.

Example:

.. code-block:: python

    from pdpyras import APISession


    session = APISession(oauth_token_here, auth_type='oauth2')

Note, obtaining an access token via the OAuth 2 flow is outside the purview of
an API client, and should be performed separately by your application.

For further information on OAuth 2 authentication with PagerDuty, refer to the
official documentation:

* `OAuth 2 Functionality <https://v2.developer.pagerduty.com/docs/oauth-2-functionality>`_
* `OAuth 2: PKCE Flow <https://v2.developer.pagerduty.com/docs/oauth-2-functionality-pkce>`_
* `OAuth 2: Authorization Code Grant Flow <https://v2.developer.pagerduty.com/docs/oauth-2-functionality-client-secret>`_

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

Request and Response Bodies
+++++++++++++++++++++++++++
Note that when working with the REST API using ``pdpyras.APISession``, the
implementer is not insulated from having to work directly with the schemas of
requests and responses. Rather, one must follow the `REST API Reference`_ which
documents the schemas at length, and construct/access objects representing the
request and response bodies, while the API client takes care of everything else.

* Data is represented as dictionary or list  objects, and should have a
  structure that mirrors that of the API schema:

  - If the data type documented in the schema is
    `object <https://v2.developer.pagerduty.com/docs/types#object>`_, then the
    corresponding type in Python will be ``dict``.

  - If the data type documented in the schema is
    `array <https://v2.developer.pagerduty.com/docs/types#array>`_, then the
    corresponding type in Python will be ``list``.

* Everything is automatically JSON-encoded and decoded, using it as follows:

  - To send a JSON request body, pass a ``dict`` object (or ``list``, where
    applicable) in the ``json`` keyword argument.

  - To get the response body as a ``dict`` (or ``list``, if applicable), call
    the `requests.Response.json`_ object returned by any of the functions named
    exactly after their respective lower-case HTTP methods.

  - If using the ``r{VERB}`` methods, i.e.  ``rget``, the return value will be
    the ``dict``/``list`` object decoded from the `wrapped entity
    <https://v2.developer.pagerduty.com/docs/wrapped-entities>`_  and there is
    no need to call ``response.json()``.

  - Similarly, the ``j{VERB}`` methods, i.e.  ``jget``, return the object
    decoded from the JSON string in the response body (but without attempting
    to unwrap any wrapped entities it may contain).

Using Special Features of Requests
++++++++++++++++++++++++++++++++++
Keyword arguments to the HTTP methods get passed through to the similarly-
named functions in `requests.Session`_, so for additional options, please refer
to the documentation provided by the Requests project.

Data Access Abstraction
***********************
The ``APISession`` class, in addition to providing a more convenient way of
making the HTTP requests to the API, provides methods that yield/return dicts
representing the PagerDuty objects with their defined schemas (see: `REST API
Reference`_) without needing to go through enclosing them in a data envelope.

In other words, in the process of getting from an API call to the object
representing the desired result, all of the following are taken care of:

1. Validate that the response HTTP status is not an error.
2. Predict the name of the envelope property which will contain the object.
3. Validate that the result contains the predicted envelope property.
4. Access the property that is encapsulated within the response.

Supported Endpoints
+++++++++++++++++++

**Please note,** not all API endpoints are supported for these convenience
functions. The general rules are that the name of the wrapped resource
property must follow from the innermost resource name for the API path in
question, and that the "nodes" in the URL path (between forward slashes) must
alternate between resource type and ID.

For instance, for ``/escalation_policies/{id}`` the name must be
``escalation_policy``, and or for ``/users/{id}/notification_rules`` it must be
``notification_rules``.

For example, with `user sessions <https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1users~1%7Bid%7D~1sessions/get>`_
(one API resource/endpoint that does not follow these rules), one will need to
use the plain ``get`` and ``post`` functions, or ``jget`` / ``jpost``, because
their URLs are formatted as ``/users/{id}/sessions/{type}/{session_id}`` and
the wrapped resource property name is ``user_sessions`` / ``user_session``
rather than simply ``sessions`` / ``session``.

Iteration
+++++++++
The method :attr:`pdpyras.APISession.iter_all` returns an iterator that yields
all results from a resource index, automatically incrementing the ``offset``
parameter to advance through each page of data.

Note, one can perform `filtering
<https://v2.developer.pagerduty.com/docs/filtering>`_ with iteration to constrain
constrain the range of results, by passing in a dictionary object as the ``params``
keyword argument. Any parameters will be automatically merged with the pagination
parameters and serialized into the final URL, so there is no need to manually
construct the URL, i.e. append ``?key1=value1&key2=value2``.

**Example:** Find all users with "Dav" in their name/email (i.e. Dave/David) in
the PagerDuty account:

.. code-block:: python

    for dave in session.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

Also, note, as of version 2.2, there are the methods
:attr:`pdpyras.APISession.list_all` and :attr:`pdpyras.APISession.dict_all`
which return a list or dictionary of all results, respectively.

**Example:** Get a dictionary of all users, keyed by email, and use it to find
the ID of the user whose email is ``bob@example.com``

.. code-block:: python

    users = session.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

Disclaimers Regarding Iteration
+++++++++++++++++++++++++++++++

**Regarding Performance:**

Because HTTP requests are made synchronously and not in parallel threads, the
data will be retrieved one page at a time and the functions ``list_all`` and
``dict_all`` will not return until after the HTTP response from the final API
call is received. Simply put, the functions will take longer to return if the
total number of results is higher.

**On Updating and Deleting Records:**

If performing page-wise operations, i.e. making changes immediately after
fetching each page of results, rather than pre-fetching all objects and then
operating on them, one must be cautious not to perform any changes to the
results that would affect the set over which iteration is taking place.

To elaborate, this happens whenever a resource object is deleted, or it is
updated in such a way that the filter parameters in ``iter_all`` no longer
apply to it. This is because indexes' contents update in real time. Thus,
should any objects be removed from the set (the objects included in the
iteration), then the offset when accessing the next page of results will still
be incremented, whereas the position of the first object in the next page will
shift to a lower rank in the overall list of objects.

In other words: let's say that one is reading and then tearing pages from a
notebook. If the algorithm is "go through 100 pages, do things with the pages,
then repeat starting with the 101st page, then with the 201st, etc" but one
tears out pages immediately after going through them, then what was originally
the 101st page before starting will shift to become the first page after going
through the first hundred pages. Thus, when going to the 101st page after
finishing tearing out the first hundred pages, the second hundred pages will be
skipped over, and similarly for pages 401-500, 601-700 and so on.

Also, note, a similar effect would occur if creating objects during iteration.

As of version 3, this issue is still applicable. To avoid it, do not use
``iter_all``, but use ``list_all`` or ``dict_all`` to pre-fetch the set of
records to be operated on, and then iterate over the results. This still does
not constitute a completely bulletproof safeguard against set changes caused by
insert/update/delete operations carried out by other simultaneous processes
(i.e. a user renaming a service through the web UI).

Reading
+++++++
The method :attr:`pdpyras.APISession.rget` gets a resource, returning the object
within the resource name envelope after JSON-decoding the response body. In
other words, if retrieving an individual user (for instance), where one would
have to JSON-decode and then access the ``user`` key in the resulting
dictionary object, that object itself is directly returned.

The ``rget`` method can be called with as little as one argument: the URL (or
URL path) to request. Example:

.. code-block:: python

    service = session.rget('/services/PZYX321')
    print("Service PZYX321's name: "+service['name'])

One can also use it on a `resource index`_, although if the goal is to get all
results rather than a specific page, :class:`pdpyras.APISession.iter_all` is
recommended for this purpose, as it will automatically iterate through all
pages of results, rather than just the first. When using ``rget`` in this way,
the return value will be a list of dicts instead of a dict.

The method also accepts other keyword arguments, which it will pass along to
``reqeusts.Session.get``, i.e. if requesting an index, ``params`` can be used
to set a filter:

.. code-block:: python

    first_100_daves = session.rget(
        '/users',
        params={'query':"Dave",'limit':100}
    )

Creating and Updating
+++++++++++++++++++++
Just as ``rget`` eliminates the need to JSON-decode and then pull the data out
of the envelope in the response schema, :attr:`pdpyras.APISession.rpost` and
:attr:`pdpyras.APISession.rput` return the data in the envelope property.
Furthermore, they eliminate the need to enclose the dictionary object
representing the data to be transmitted in an envelope, and just like ``rget``,
they accept at an absolute minimum one positional argument (the URL), and all
keyword arguments are passed through to the underlying request method function.

For instance, instead of having to set the keyword argument ``json = {"user":
{...}}`` to ``put``, one can pass ``json = {...}`` to ``rput``, to update a
user. The following function takes a PagerDuty user ID and gives the
user the admin role and prints a message when done:

.. code-block:: python

    def promote_to_admin(session, uid):
        user = session.rput(
            '/users/'+uid,
            json={'role':'admin'}
        )
        print("%s now has admin superpowers"%user['name'])


Example of creating an incident:

.. code-block:: python

    import os
    from pdpyras import APISession

    api_token = os.environ['PD_API_KEY']
    sender = 'user@example.com'
    session = APISession(api_token, default_sender=sender)

    payload = {
      "type": "incident",
      "title": "This is a test 4",
      "service": {"id": "service_id", "type": "service_reference"},
      "assignments": [{"assignee": {"id": "user_id", "type": "user_reference"}}],
      "body": {
          "type": "incident_body",
          "details": "utf8 data displayed the more details section of the alert"
      }
    }
    pd_incident = session.rpost("incidents", json=payload)


Idempotent Resource Creation
++++++++++++++++++++++++++++
Beyond just creating a resource, :attr:`pdpyras.APISession.persist` can be used
to perform a check for a preexisting object before creating it; it returns the
persisted resource, whether or not the object already existed.

For instance, the following will create a user having email address
``user@organization.com`` if one does not already exist, and print that user's
name:

.. code-block:: python

    user = session.persist('users', 'email', {
        "name": "User McUserson",
        "email": "user@organization.com",
        "type": "user"
    })

    print(user['name'])

Deleting
++++++++
The ``rdelete`` method has no return value, but otherwise behaves in exactly
the same way as the other request methods with ``r`` prepended to their name.
Like the other ``r*`` methods, it will raise :class:`pdpyras.PDClientError` if
the API responds with a non-success HTTP status.

Example:

.. code-block:: python

    session.rdelete("/services/PI86NOW")

    print("Service deleted.")

Managing, a.k.a. Multi-Updating
+++++++++++++++++++++++++++++++
Introduced in version 2.1 is support for automatic data envelope functionality
in multi-update actions.

As of this writing, multi-update is limited to the following actions:

* `PUT /incidents <https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1incidents/put>`_
* `PUT /incidents/{id}/alerts <https://developer.pagerduty.com/api-reference/reference/REST/openapiv3.json/paths/~1incidents~1%7Bid%7D~1alerts/put>`_
* **PUT /priorities** (not yet published, as of 2018-11-28)

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
keyword argument, or set the :attr:`pdpyras.APISession.default_from` property.

Using Resources in Place of URLs
++++++++++++++++++++++++++++++++
As of version 4.1, one may send the dictionary representation of a resource to
any of the ``r*`` methods, with the exception of ``rpost``, in place of a URL
or path. The dictionary must contain a ``self`` item that is the URL of the
resource.

This eliminates the need to construct the resource's path/URL, or to keep a
temporary variable with the URL needed for accessing the object.

For instance, to reload a service object previously fetched from the API, i.e.
to ensure one has the latest data for that resource:

.. code-block:: python

    user = session.rget('users/PSOMEUSR')

    # Do things that take a lot of time during which the user might change
    # ...

    # Reload the user:
    user = session.rget(user)
    # as opposed to:
    # user = session.rget('users/PSOMEUSR')

Another example: to delete a service:

.. code-block:: python

    session.rdelete(service)
    # as opposed to:
    # session.rdelete(service['self'])

Error Handling
**************
What happens when, for any of the ``r*`` methods, the API responds with a
non-success HTTP status? Obviously in this case, they cannot return the
JSON-decoded response, because the response would not be the sought-after data
but a different schema altogether (see: `Errors`_), and this would put the onus
on the end user to distinguish between success and error based on the structure
of the returned dictionary object (yuck).

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

    except PDClientError as e:
        if e.response:
            if e.response.status_code == 404:
                print("User not found")
            elif e.response.status_code == 401:
                raise e
        else:
            raise e

Just make sure to import `PDClientError` or reference it throught he namespace, i.e.

.. code-block:: python

    from pdpyras import APISession, PDClientError

    except PDClientError as e:

Or:

.. code-block:: python

    import pdpyras

    ...

    except pdpyras.PDClientError as e:
    ...


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

Note that without specifying any retry behavior for status 429 (rate limiting),
it will retry indefinitely. This is a sane approach; if it is ever responding
with 429, this means that the REST API is receiving (for the given REST API
key) too many requests, and the issue should by nature be transient.

Similarly, there is hard-coded default behavior for status 401 (unauthorized):
immediately raise :class:`pdpyras.PDClientError` (as this can be considered in
all cases a completely non-transient error).

It is still possible to override these behaviors using
:attr:`pdpyras.PDSession.retry`, but it is not recommended.

Events API Usage
****************

As an added bonus, ``pdpyras`` provides an additional Session class for submitting
alert data to the Events API and triggering incidents asynchronously:
:class:`pdpyras.EventsAPISession`. It has most of the same features as
:class:`pdpyras.APISession`:

* Connection persistence
* Automatic cooldown and retry in the event of rate limiting or a transient network error
* Setting all required headers
* Configurable HTTP retry logic

To transmit alerts and perform actions through the events API, one would use:

* :attr:`pdpyras.EventsAPISession.trigger`
* :attr:`pdpyras.EventsAPISession.acknowledge`
* :attr:`pdpyras.EventsAPISession.resolve`

To instantiate a session object, pass the constructor the routing key:

.. code-block:: python

    import pdpyras


    routing_key = '0123456789abcdef0123456789abcdef'
    session = pdpyras.EventsAPISession(routing_key)


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

.. _`Errors`: https://v2.developer.pagerduty.com/docs/errors
.. _`HTTP Request Headers`: https://v2.developer.pagerduty.com/docs/rest-api#http-request-headers
.. _make: https://www.gnu.org/software/make/
.. _pagination: https://v2.developer.pagerduty.com/docs/pagination
.. _pypd: https://github.com/PagerDuty/pagerduty-api-python-client/
.. _Requests: https://docs.python-requests.org/en/master/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Response.json: https://docs.python-requests.org/en/master/api/#requests.Response.json
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions
.. _requests.Session.request: https://docs.python-requests.org/en/master/api/#requests.Session.request
.. _`resource index`: https://v2.developer.pagerduty.com/docs/endpoints#resources-index
.. _`REST API Reference`: https://developer.pagerduty.com/api-reference/
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _`pdpyras.py`: https://raw.githubusercontent.com/PagerDuty/pdpyras/master/pdpyras.py

.. |travis-build| image:: https://travis-ci.com/Deconstrained/pdpyras.svg?branch=master
    :target: https://travis-ci.com/Deconstrained/pdpyras
.. |circleci-build| image:: https://circleci.com/gh/PagerDuty/pdpyras.svg?style=svg
    :target: https://circleci.com/gh/PagerDuty/pdpyras
