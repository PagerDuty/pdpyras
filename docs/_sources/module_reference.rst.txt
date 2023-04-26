.. _module_reference:

================
Module Reference
================

This page covers the documentation of individual methods and classes provided
by the module. For general usage and examples, refer to the :ref:`user_guide`.

API Client Classes
------------------
.. autoclass:: pdpyras.PDSession
    :members:


.. autoclass:: pdpyras.APISession
    :members:

.. autoclass:: pdpyras.EventsAPISession
    :members:


.. autoclass:: pdpyras.ChangeEventsAPISession
    :members:

Errors
------
.. autoclass:: pdpyras.PDClientError
    :members:
.. autoclass:: pdpyras.PDHTTPError
    :members:
.. autoclass:: pdpyras.PDServerError
    :members:
.. autoclass:: pdpyras.URLError

Functions
---------
.. automodule:: pdpyras
    :members:
    :exclude-members: APISession, EventsAPISession, ChangeEventsAPISession, PDClientError, PDHTTPError, PDSession, URLError, PDServerError


.. References:
.. -----------

.. _`Requests`: https://docs.python-requests.org/en/master/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions
