===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A minimal, practical Python client for the PagerDuty REST API.

GitHub: `PagerDuty/pdpyras <https://github.com/PagerDuty/pdpyras>`_

About
-----
This library supplies a class ``APISession`` extending `requests.Session`_ from
the Requests_ HTTP library. It serves as a practical and
simple-as-possible-but-no-simpler abstraction layer for accessing the PagerDuty
REST API, differing minimally from the already well-known and well-documented
underlying HTTP library. This makes it appropriate for use as the foundation of
anything from a feature-rich REST API client library to a quick-and-dirty API
script.

This module was borne of necessity for a basic, reusable API client to
eliminate code duplication in some of PagerDuty Support's internal Python-based
API tools, and to get the job done without reinventing the wheel or getting in
the way. We also frequently found ourselves performing REST API requests using
beta or non-documented API endpoints for one reason or another, so we also
needed a client that provided easy access to features of the underlying HTTP
library, but that eliminated tedious tasks like querying, `pagination`_ and
header-setting. Finally, we discovered that the way we were using `requests`_
wasn't making use of connection re-use, and wanted a way to easily enforce this
as a standard practice.

Ultimately, we deemed most other libraries to be both overkill for this task
and also not very conducive to use for experimental API calls.

Features
********
- Efficient API access through automatic HTTP connection pooling and
  persistence 
- Tested in / support for Python 2.7 through 3.7
- Automatic cooldown/reattempt for rate limiting and transient network problems
- Inclusion of required `HTTP Request Headers`_ for PagerDuty REST API requests
- Bulk data retrieval and iteration over `resource index`_ endpoints with
  automatic pagination
- Individual object retrieval by name
- API request profiling


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

Usage Guide
-----------

Installation
************
If ``pip`` is available, it can be installed via:

::

    pip install pdpyras

Alternately, if requests_ has already been installed locally, and ``urllib3``
is available, one can simply download `pdpyras.py`_ into the directory where it
will be used.

Basic Usage
***********

**Basic getting:** Obtain a user profile as a dict object:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)

    # Using requests.Session.get:
    response = session.get('/users/PABC123')
    user = None
    if response.ok:
        user = response.json()['user']

    # Or, more succinctly:
    user = session.rget('/users/PABC123')

**Iteration (1):** Iterate over all users and print their ID, email and name:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    for user in session.iter_all('users'):
        print(user['id'], user['email'], user['name'])

**Iteration (2):** Compile a list of all servies with "SN" in their name:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    services = list(session.iter_all('services', params={'query': 'SN'}))

**Querying and updating:** Find a user exactly matching email address ``jane@example35.com``
and update their name to "Jane Doe":

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    sesion = APISession(api_token)
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

Data Access Abstraction
***********************
Using the ``iter_all`` and ``find`` of :class:`pdpyras.APISession` as
documented, it is easier to directly get to the underlying data representing a
given PagerDuty object. Both of these methods yield/return dicts representing
the PagerDuty objects with their defined schemas (see: `REST API Reference`_).

In version 2, it is even easier to do this, and in more ways, with four new
methods of :class:`pdpyras.APISession`, named exactly after the original HTTP
verb functions but with ``r`` prepended to them: ``rget``, ``rpost``, ``rput``
and ``rdelete``.

Reading
+++++++
The method ``pdpyras.APISession.rget`` gets a resource, returning the object
within the resource name envelope after JSON-decoding the response body. In
other words, if retrieving an individual user (for instance), where one would
have to JSON-decode and then access the ``user`` key in the resulting
dictionary object, that object itself is directly returned. 

The ``rget`` method can be called with as little as one argument: the URL (or
URL path) to request. Example:

::

    service = session.rget('/services/PZYX321')
    print("Service PZYX321's name: "+service['name'])

One can also use it on a `resource index`_, although if the goal is to get all
results rather than a specific page, ``iter_all`` is recommended for this
purpose, as it will automatically iterate through all pages of results, rather
than just the first. When using ``rget`` in this way, the return value will be
a list of dicts instead of a dict.

The method also accepts other keyword arguments, which it will pass along to
``reqeusts.Session.get``, i.e. if requesting an index, ``params`` can be used
to set a filter:

::

    first_100_daves = session.rget(
        '/users',
        params={'query':"Dave",'limit':100}
    )

Creating and Updating
+++++++++++++++++++++

Just as ``rget`` eliminates the need to JSON-decode and then pull the data out
of the envelope in the response schema, ``rpost`` and ``rput`` return the data
in the envelope property. Furthermore, they eliminate the need to enclose the
dictionary object representing the data to be transmitted in an envelope, and
just like ``rget``, they accept at an absolute minimum one positional argument
(the URL), and all keyword arguments are passed through to the underlying
request method function.

For instance, instead of having to set the keyword argument ``json = {"user":
{...}}`` to ``put``, one can pass ``json = {...}`` to ``rput``, to update a
user. The following function takes a PagerDuty user ID and gives the
user the admin role and prints a message when done:

::

    def promote_to_admin(session, uid):
        user = session.rput(
            '/users/'+uid,
            json={'role':'admin'}
        )
        print("%s now has admin superpowers"%user['name'])

Deleting
++++++++

The ``rdelete`` method has no return value, but otherwise behaves in exactly
the same way as the other request methods with ``r`` prepended to their name.
Like the other ``r*`` methods, it will raise ``PDClientError`` if the API responds
with a non-success HTTP status.

Example:

::

    session.rdelete("/services/PI86NOW")
    print("Service deleted.")

Error Handling
**************

What happens when, for any of the ``r*`` methods, the API responds with a
non-success HTTP status? Obviously in this case, they cannot return the
JSON-decoded response, because the response would not be the sought-after data
but a different schema altogether (see: `Errors`_), and this would put the onus
on the end user to distinguish between success and error based on the structure
of the returned dictionary object (yuck).

Instead, when this happens, an exception of class ``pdpyras.PDClientError`` is
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

::

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

Contributing
------------
Bug reports and pull requests to fix issues are always welcome. 

If adding features, or making changes, it is recommended to update or add tests
and assertions to the class ``APISessionTest`` to ensure code coverage. If the
change(s) fix a bug, please add assertions that reproduce the bug along with
code changes themselves, and include the GitHub issue number in the commit
message.

.. References:
.. -----------

.. _`Errors`: https://v2.developer.pagerduty.com/docs/errors
.. _`HTTP Request Headers`: https://v2.developer.pagerduty.com/docs/rest-api#http-request-headers
.. _make: https://www.gnu.org/software/make/
.. _pagination: https://v2.developer.pagerduty.com/docs/pagination
.. _pypd: https://github.com/PagerDuty/pagerduty-api-python-client/
.. _Requests: http://docs.python-requests.org/en/master/
.. _requests.Response: http://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: http://docs.python-requests.org/en/master/api/#request-sessions
.. _requests.Session.request: http://docs.python-requests.org/en/master/api/#requests.Session.request
.. _`resource index`: https://v2.developer.pagerduty.com/docs/endpoints#resources-index
.. _`REST API Reference`: v2.developer.pagerduty.com/v2/page/api-reference#!/API_Reference/get_api_reference
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _`pdpyras.py`: https://raw.githubusercontent.com/PagerDuty/pdpyras/master/pdpyras.py

.. codeauthor:: Demitri Morgan <demitri@pagerduty.com>
