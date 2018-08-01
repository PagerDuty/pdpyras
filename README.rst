===========================================
pdpyras: PagerDuty Python REST API Sessions
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
header-setting. Ultimately, we deemed most other libraries to be both overkill
for this task and also not very conducive to use for experimental API calls.

Features
--------
- Efficient API access through automatic HTTP connection pooling and
  persistence 
- Supports Python 2.7 through 3.6
- Automatic cooldown/reattempt for rate limiting and transient network problems
- Inclusion of required `HTTP Request Headers`_ for PagerDuty REST API requests
- Bulk data retrieval and iteration over `resource index`_ endpoints with
  automatic pagination
- Individual object retrieval by name
- API request profiling

Installation
------------
If ``pip`` is available, it can be installed via:

::

    pip install pdpyras

Alternately, if Requests_ has already been installed locally, and ``urllib3``
is available, one can simply download `pdpyras.py`_ into the directory where it
will be used.

Usage
-----

**Basic getting:** Obtain a user profile as a dict object:

::

    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    response = session.get('/users/PABC123')
    if response.ok:
        user = response.json()['user']


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
        session.put(user['self'], json={
            'user':{'type':'user', 'name': 'Jane Doe'}
        })

Contributing
------------
Bug reports and pull requests to fix issues are always welcome. 

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
.. _`pdpyras.py`: https://raw.githubusercontent.com/PagerDuty/pdpyras/master/pdpyras.py

.. codeauthor:: Demitri Morgan <demitri@pagerduty.com>
