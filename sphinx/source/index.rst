.. include:: ../../README.rst


Developer Interface
-------------------
API client classes supplied by this library are not intended as replacements
for API documentation or wrappers of PagerDuty's APIs, but rather wrappers of the
HTTP client (`requests.Session`_) that make it easier to use PagerDuty's APIs.

Generic API Client
******************
This base class implements features common to all API client classes.

.. autoclass:: pdpyras.PDSession
    :members:

REST API Client
***************

.. autoclass:: pdpyras.APISession
    :members:

    .. automethod:: rdelete(self, path, \*\*kw)
    .. automethod:: rget(self, path, \*\*kw)
    .. automethod:: rpost(self, path, \*\*kw)
    .. automethod:: rput(self, path, \*\*kw)

Events API Client
*****************

.. autoclass:: pdpyras.EventsAPISession
    :members:

Change Events API Client
************************

.. autoclass:: pdpyras.ChangeEventsAPISession
    :members:

Errors
******
.. autoclass:: pdpyras.PDClientError
    :members:

Functions
*********

.. automodule:: pdpyras
    :members:
    :exclude-members: APISession, EventsAPISession, PDClientError, PDSession

Changelog
---------
.. include:: ../../CHANGELOG.rst
