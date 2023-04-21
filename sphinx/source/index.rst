.. include:: ../../README.rst
.. include:: DEVELOPER_GUIDE.rst
.. include:: ADVANCED_TOPICS.rst
.. include:: RELEASING.rst


Developer Interface
-------------------
API client classes supplied by this library are not intended as replacements
for API documentation or wrappers of PagerDuty's APIs, but rather wrappers of the
HTTP client (`requests.Session`_) that make it easier to use PagerDuty's APIs.

API Client Classes
******************

.. autoclass:: pdpyras.PDSession
    :members:


.. autoclass:: pdpyras.APISession
    :members:

.. autoclass:: pdpyras.EventsAPISession
    :members:


.. autoclass:: pdpyras.ChangeEventsAPISession
    :members:


Errors
******
.. autoclass:: pdpyras.PDClientError
    :members:
.. autoclass:: pdpyras.PDHTTPError
    :members:
.. autoclass:: pdpyras.PDServerError
    :members:
.. autoclass:: pdpyras.URLError

Functions
*********
.. automodule:: pdpyras
    :members:
    :exclude-members: APISession, EventsAPISession, ChangeEventsAPISession, PDClientError, PDHTTPError, PDSession, URLError, PDServerError

Changelog
---------
.. include:: ../../CHANGELOG.rst
