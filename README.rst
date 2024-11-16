===========================================
PDPYRAS: PagerDuty Python REST API Sessions
===========================================
A module that supplies lightweight Python clients for the PagerDuty REST API v2 and Events API v2.

For how-to, refer to the `User Guide
<https://pagerduty.github.io/pdpyras/user_guide.html>`_.

|circleci-build|

Overview
--------
This library supplies classes extending `httpx.Client`_ from the HTTPX_
HTTP library that serve as Python interfaces to the `REST API v2`_ and `Events
API v2`_ of PagerDuty. One might call it an opinionated wrapper library. It was
designed based on these tenets:

- The client should not reinvent the wheel when it comes to HTTP.
- A successful API client should emphasize abstractions for only the most
  broadly-applicable and frequently-implemented core patterns and requirements
  of the API(s) that it was built to access.

Decisions concerning how any particular PagerDuty resource is handled, and
which API calls are made to accomplish a design goal, are left to the end user
("implementer") to make. This client's focus is on removing barriers to getting
the API's data into the hands of the implementer, and the implementer's data
into the API, using basic Python types (``dict``, ``list``, ``str`` and
``int``) to represent the data.

Features
--------
- Automatic HTTP connection pooling and persistence
- Tested in / support for Python 3.8 through 3.13
- Abstractions for authentication, pagination and entity wrapping
- Configurable cooldown/reattempt logic for handling rate limiting and
  transient HTTP or network issues

History
-------
This module was borne of necessity for a basic API client to eliminate code
duplication in some of the PagerDuty Customer Support team's internal
Python-based API tooling. We needed something to eliminate the toil of
re-implementing common solutions such as querying objects by name, pagination
and authentication.

We also found ourselves frequently performing REST API requests using beta or
non-documented API endpoints for one reason or another, so we needed the client
that provided easy access to features of the underlying HTTP library (i.e. to
obtain the response headers, or set special request headers). Finally, we
discovered that the way we were using Requests (our erstwhile go-to HTTP
client) wasn't leveraging its connection pooling feature, which led to
performance issues, and we wanted a way to easily enforce best practices.

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

.. _`HTTPX`: https://www.python-httpx.org/
.. _`Errors`: https://developer.pagerduty.com/docs/cd9f75aa7ac93-errors
.. _`Events API v2`: https://developer.pagerduty.com/docs/3d063fd4814a6-events-api-v2-overview
.. _`PagerDuty API Reference`: https://developer.pagerduty.com/api-reference/
.. _`REST API v2`: https://developer.pagerduty.com/docs/531092d4c6658-rest-api-v2-overview
.. _`setuptools`: https://pypi.org/project/setuptools/
.. _httpx.Response: https://www.python-httpx.org/api/#response
.. _httpx.Session: https://www.python-httpx.org/api/#client

.. |circleci-build| image:: https://circleci.com/gh/PagerDuty/pdpyras.svg?style=svg
    :target: https://circleci.com/gh/PagerDuty/pdpyras

.. role:: strike
  :class: strike
