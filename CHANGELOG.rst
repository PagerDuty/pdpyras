**2019-04-05: version 3.1.1**

* Changed behavior of HTTP retry that caused issues with some internal tools: raising ``PDClientError`` in the event of non-transient HTTP error, in the ``request`` method, versus returning the request object and logging it. The previous behavior was:
    * Not the intended design
    * At odds with the documentated behavior

**2019-04-05: version 3.1:**

* Introduction of a custom ``User-Agent`` header to distinguish the API client as such, for the purposes of usage analytics

**2019-04-02: version 3.0.2:**

Important bug fixes to the custom HTTP retry logic:

* Fixed ``KeyError`` in ``APISession.request``
* Fixed incorrect behavior (retrying more than the specified amount of times) due to faulty comparison logic

**2019-03-14: version 3.0.1:**

A light Events API client methods refactor:

* All keyword arguments specific to sending trigger events have been refactored out of the generic ``EventsAPISession.send_event`` method
* Now, instead, ``send_event`` and uses a catch-all keyword argument to set event properties.
* The keyword arguments specific to triggering incidents are in the method EventsAPISession.trigger method.

**2019-03-12: version 3.0:**

* Added new Events API session class that still has most of the same functional features as the REST API session class.

**2019-01-28: version 2.4.1:**

* Fixed bug: unpacking wrapped entities does not work with ``/log_entries``

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
