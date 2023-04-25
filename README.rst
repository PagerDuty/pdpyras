===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A lightweight Python client for the PagerDuty REST API.

Also includes client classes for the Events and Change Events APIs.

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
locally, one can simply download ``pdpyras.py`` into the directory where it
will be used.

Basic Usage
-----------
For more topics, see the `Developer Guide
<https://pagerduty.github.io/pdpyras/#developer-guide>`_. For in-depth
documentation on classes and methods, see the `Module Reference
<https://pagerduty.github.io/pdpyras/#module-reference>`_.

Authentication
**************
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

If the `REST API v2`_ session will be used for API endpoints that require a
``From`` header, such as those that take actions on incidents, and if it is
using an account-level API key (created by an administrator via the "API Access
Keys" page in the "Integrations" menu), the user must also supply the
``default_from`` keyword argument. Otherwise, a HTTP 400 response will result
when making requests to such endpoints.

Otherwise, if using a user's API key (created under "API Access" in the "User
Settings" tab of the user's profile), the user will be derived from the key
itself and ``default_from`` is not necessary.

When encountering status ``401 Unauthorized``, the client will immediately raise
``pdpyras.PDClientError``; this is a non-transient error caused by an invalid
credential. When encountering ``403 Forbidden``, 

REST API v2
***********

**Making a request and decoding the response:** obtaining a resource's contents
and having them represented as a dict object using three different methods:

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

**Searching resource collections:** use ``find`` to look up a resource exactly
matching a string using the ``query`` parameter on an index endpoint:

.. code-block:: python

    # Find the user with email address "jane@example35.com"
    user = session.find('users', 'jane@example35.com', attribute='email')

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

Updating/creating using ``persist``, an idempotent create/update function:

.. code-block:: python

    # Create a user if one doesn't already exist based on the dictionary object
    # user_data, using the 'email' key as the uniquely identifying property, and
    # update it if it exists and differs from user_data:
    updated_user = session.persist('users', 'email', user_data, update=True)

Using multi-valued set filters: set the value in the ``params`` dict at the
appropriate key to a list, and include ``[]`` at the end of the paramter name:

.. code-block:: python

    # Query all open incidents assigned to a user:
    incidents = session.list_all(
        'incidents',
        params={'user_ids[]':['PHIJ789'],'statuses[]':['triggered', 'acknowledged']}
    )

Performing multi-update (for endpoints that support it only):

.. code-block:: python

    # Acknowledge all triggered incidents assigned to a user:
    incidents = session.list_all(
        'incidents',
        params={'user_ids[]':['PHIJ789'],'statuses[]':['triggered']}
    )
    for i in incidents:
        i['status'] = 'acknowledged'
    updated_incidents = session.rput('incidents', json=incidents)

Events API v2
*************
Trigger and resolve an alert, getting its deduplication key from the API:

.. code-block:: python

    dedup_key = events_session.trigger("Server is on fire", 'dusty.old.server.net')
    # ...
    events_session.resolve(dedup_key)

Trigger an and acknowledge an alert, using a custom deduplication key:

.. code-block:: python

    events_session.trigger("Server is on fire", 'dusty.old.server.net',
        dedup_key='abc123')
    # ...
    events_session.acknowledge('abc123')

Submit a change event using a ``ChangeEventsAPISession`` instance:

.. code-block:: python

    change_events_session.submit("new build finished at latest HEAD",
        source="automation")


Contributing
------------
Bug reports and pull requests to fix issues are always welcome, as are
contributions to the built-in documentation.

If adding features, or making changes, it is recommended to update or add tests
and assertions to the appropriate test case class in ``test_pdpyras.py`` to ensure
code coverage. If the change(s) fix a bug, please add assertions that reproduce
the bug along with code changes themselves, and include the GitHub issue number
in the commit message.

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

.. |circleci-build| image:: https://circleci.com/gh/PagerDuty/pdpyras.svg?style=svg
    :target: https://circleci.com/gh/PagerDuty/pdpyras
