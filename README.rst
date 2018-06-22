===========================================
pdpyras: PagerDuty Python REST API Sessions
===========================================

A minimal, practical client for the PagerDuty REST API.

About
-----
This library supplies a class ``APISession`` extending `requests.Session`_ from
the Requests_ HTTP library, which provides the means to perform most basic
tasks associated with accessing the PagerDuty REST API in a succinct manner.

It is intended to be a practical and dead-simple abstraction layer for
PagerDuty REST API access that differs minimally from the already well-known
and well-documented underlying HTTP library. This makes it ideal to use as the
foundation of anything from a feature-rich REST API client library to a
quick-and-dirty API script. 

**Why not pypd?**

This module was borne of necessity for a basic, reusable API client library to
eliminate code duplication in PagerDuty Support's internal Python-based API
tools, and to get the job done without reinventing the wheel or getting in the
way.

We frequently find ourselves performing experimental REST API requests using
non-documented API endpoints for one reason or another, so we also needed a
client that provided easy access to low-level features of the `Requests`_
library, but that eliminated tedious tasks like querying, `pagination`_ and
header-setting. Ultimately, we deemed `pypd`_ to be overkill for this task.

With :class:`pdpyras.APISession`, higher-level features, i.e. model classes for
handling the particulars of any given resource type, are left to the end user
to develop as they see fit. Using this module by itself is thus a good approach
for those who simply want to go by what the `REST API Reference`_ says and have
explicit control over each resource schema feature.

Features
--------
- Efficient API access through automatic HTTP connection pooling and
  persistence 
- Supports Python 2.7 through 3.6
- Automatic cooldown/reattempt for rate limiting and momentary/transient
  network issues
- Inclusion of required `HTTP Request Headers`_ for PagerDuty REST API requests
- Bulk data retrieval and iteration over `resource index`_ endpoints with
  automatic pagination
- Lookup of individual objects matching a query
- API request profiling

Build & Install
-----------------
To manually build and install the Python module to your local distribution
packages, make sure you have `setuptools`_ installed.

If you have `make`_ installed, you can then run:

::

    make build

Otherwise, run:

::

    python setup.py bdist

To install locally:

::

    make install # if you have make
    python setup.py install # otherwise

Note, unless you are using a local/userspace virtual environment, you will need
to run the above as root.

Usage
-----
**Example 1:** get a user:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    response = session.get('/users/PABC123')
    if response.ok:
        user = response.json()['user']


**Example 2:** iterate over all users and print their ID, email and name:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    for user in session.iter_all('/users'):
        print(user['id'], user['email'], user['name'])


**Example 3:** Find a user exactly matching email address ``jane@example35.com``
and update their name to "Jane Doe":

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    sesion = APISession(api_token)
    user = session.find('users', 'jane@example35.com', attribute='email')
    if user is not None:
        session.put(user['self'], json={
            'user':{'type':'user', 'name': 'Jane Doe'}
        })

Contributing
------------
Bug reports and pull requests to fix issues are always welcome. 

The ``tests`` directory contains a standalone script ``test_APISession.py``
that performs unit testing.

If adding features, or making changes, it is recommended to update or add tests
and assertions to the class ``APISessionTest`` to ensure code coverage. If the
change(s) fix a bug, please add assertions that reproduce the bug along with
code changes themselves, and include the GitHub issue number in the commit
message.

Copyright
---------
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
--------
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

.. References:
.. -----------

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
