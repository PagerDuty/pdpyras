.. include:: ../../README.rst

Developer Interface
-------------------

Classes
*******
.. autoclass:: pdpyras.APISession
    :members:

    .. automethod:: rdelete(self, path, \*\*kw)
    .. automethod:: rget(self, path, \*\*kw)
    .. automethod:: rpost(self, path, \*\*kw)
    .. automethod:: rput(self, path, \*\*kw)

.. autoclass:: pdpyras.PDClientError
    :members:

Functions
*********
.. automodule:: pdpyras
    :members:
    :exclude-members: APISession, PDClientError

.. Changelog:
.. include:: ../../CHANGELOG.rst
