.. include:: ../../README.rst


Developer Interface
-------------------

Generic API Client
******************
This base class implements features common to both :class:`pdpyras.APISession`
and :class:`pdpyras.EventsAPISession`. It cannot itself be used as an API client.

.. autoclass:: pdpyras.PDSession
    :members:

REST API Client
***************
The ``APISession`` class inherits from :class:`pdpyras.PDSession` and
implements features specific to usage of the REST API.

.. autoclass:: pdpyras.APISession
    :members:

    .. automethod:: rdelete(self, path, \*\*kw)
    .. automethod:: rget(self, path, \*\*kw)
    .. automethod:: rpost(self, path, \*\*kw)
    .. automethod:: rput(self, path, \*\*kw)

Events API Client
*****************
Class ``EventsAPISession`` implements methods for submitting events to
PagerDuty through the Events API and inherits from :class:`pdpyras.PDSession`.

.. autoclass:: pdpyras.EventsAPISession
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
