===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A module that supplies lightweight Python clients for the PagerDuty REST API v2 and Events API v2.

For how-to, refer to the `User Guide
<https://pagerduty.github.io/pdpyras/user_guide.html>`_.

|circleci-build|

Overview
--------
This library supplies classes extending `requests.Session`_ from the Requests_
HTTP library that serve as Python interfaces to the `REST API v2`_ and `Events
API v2`_ of PagerDuty. One might call it an opinionated wrapper library. It was
designed with the philosophy that Requests_ is a perfectly adequate HTTP
client, and that abstraction should focus only on the most generally applicable
and frequently-implemented core features, requirements and tasks. Design
decisions concerning how any particular PagerDuty resource is accessed or
manipulated through APIs are left to the user or implementer to make.

Features
--------
- Uses Requests' automatic HTTP connection pooling and persistence
- Tested in / support for Python 3.6 through 3.11
- Abstraction layer for authentication, pagination, filtering and wrapped
  entities
- Configurable cooldown/reattempt logic for handling rate limiting and
  transient HTTP or network issues

History
-------
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

License
-------
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
