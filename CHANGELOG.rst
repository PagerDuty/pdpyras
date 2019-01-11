Changelog
---------

**2019-01-10: version 2.4:**

* Whitelisting of endpoints supported by the ``r*`` / ``*_all`` methods has been rescinded, and documentation has been updated with how to identify endpoints that these methods can be used with.

**2019-01-03: version 2.3:**

* More helpful error messaging when using ``r*`` / ``*_all`` methods on endpoints they don't support
* Resource envelope auto-unpacking no longer validates for the presence of a ``type`` property in order to support posting to business impact metrics

**2018-12-04: version 2.2:**

* Methods ``list_all`` and ``dict_all`` turn all results from an index into a list/dict to save a bit of effort

**2018-11-28: version 2.1:**

* Support for performing multi-update actions (i.e. *Manage Incidents*) via the ``rput`` method.
* The default behavior of ``iter_all`` is now to raise an exception if an error response is received from the API during iteration.

**Changelog Started 2018-11-28**
