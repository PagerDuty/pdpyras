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

Client Defaults
---------------
These are properties of the module that configure default behavior for the API
client. There should be no need for the end user to modify them.

.. automodule:: pdpyras
    :members: ITERATION_LIMIT, TEXT_LEN_LIMIT, TIMEOUT, ENTITY_WRAPPER_CONFIG, CANONICAL_PATHS, CURSOR_BASED_PAGINATION_PATHS

Functions
---------
These are generic functions used by the API session classes and are not on
their own typically needed, but which are documented for the benefit of anyone
who may find use in them.

URL Handling
************
URL related functions.

.. automodule:: pdpyras
    :members: canonical_path, endpoint_matches, is_path_param, normalize_url

Entity Wrapping
***************
Functions that implement entity wrapping logic.

.. automodule:: pdpyras
    :members: entity_wrappers, infer_entity_wrapper, unwrap

Function Decorators
*******************
Intended for use with functions based on the HTTP verb functions of subclasses
of `httpx.Client`_, i.e. that would otherwise return a `httpx.Response`_
object.

.. automodule:: pdpyras
    :members: auto_json, requires_success, resource_url, wrapped_entities

Helpers
*******
Miscellaneous functions

.. automodule:: pdpyras
    :members: deprecated_kwarg, http_error_message, last_4, plural_name, successful_response, truncate_text, try_decoding



.. References:
.. -----------

.. _`HTTPX`: https://docs.python-requests.org/en/master/
.. _httpx.Response: https://docs.python-requests.org/en/master/api/#httpx.Response
.. _httpx.Client: https://docs.python-requests.org/en/master/api/#request-sessions
