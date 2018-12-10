Ideas For Later
---------------

Generic Lazy Error Handling
===========================
How about this: take all the error handling cruft you're rewriting and find
some way of making it user-configurable, i.e. as some kind of hook or function,
with ways of reusing it and stuff.

You can pass a callable object to the constructor to define the error handling
behavior.

Also, have a locally-scoped variable recording the number of retries for each
reason (network issues, 429's, other statuses, etc)

I have come to realize that a more appropriate and "Pythonic" behavior of ``APISession.iter_all`` would be to raise an exception instead of quietly halting iteration in the case of encountering a HTTP error, keeping with the following from `PEP 20<https://www.python.org/dev/peps/pep-0020/>`_:

::

    Explicit is better than implicit.
    Errors should never pass silently.
    Unless explicitly silenced.

I am thinking of doing this starting with a new keyword argument

