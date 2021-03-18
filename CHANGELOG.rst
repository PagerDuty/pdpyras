**2021-03-18: Version 4.1.4**

* Fix regression in :attr:`EventsAPISession.post`
    * Use case: explicitly-defined body (``json`` keyword argument) without a ``routing_key`` parameter
    * This was previously possible (before version 4.1.3) with the ``X-Routing-Key`` header (an undocumented API feature)

**2021-03-10: Version 4.1.3**

* Use documented method for including the routing key in the request for API V2 (addresses `#53 <https://github.com/PagerDuty/pdpyras/issues/53>`_)
* Add warning for Python 2.7

**2020-09-15: Version 4.1.2**

* Address issue #37 and add other enhancements to ``iter_all``:
    * Stop iteration in ``iter_all`` if the iteration limit (10000) is encountered, versus erroring out (because exceeding it will elicit a 400 response)
    * Add the ability to set an initial offset via ``params`` versus always starting from ``offset=0`` in ``iter_all``
* Capitalize "constants"

**2020-06-26: Version 4.1.1**

* Define class variable ``retry`` initially as ``{}`` instead of ``None`` (`#32 <https://github.com/PagerDuty/pdpyras/issues/32>`_)

**2020-03-08: Version: 4.1**

* Added new idempotent resource creator function, :attr:`APISession.persist`
* Added the ability to use resource dictionaries (that have a ``self`` attribute) in place of URLs.

**2020-02-04: Version 4.0**

* Added support for using OAuth 2 access tokens to authenticate (`#23 <https://github.com/PagerDuty/pdpyras/issues/23>`_)
* Added a property that indicates the access level/scope of a given API credential (`#22 <https://github.com/PagerDuty/pdpyras/issues/22>`_)

**2020-01-10: version 3.2.1**

* Fixed bug in :attr:`APISession.trunc_token`; property name typo causes ``AttributeError``

**2019-10-31: version 3.2**

* The page size (``limit``) parameter can now be set on a per-call basis in any of the ``*_all`` methods (i.e. :attr:`PDSession.iter_all`) by passing the ``page_size`` keyword argument. If the argument is not present, the default page size will be used.
* The ``X-Request-Id`` header in responses is now captured in log messages to make it easier to identify API calls when communicating with PagerDuty Support
* Extended API call metadata is also now logged.
* The cooldown time between rate limit responses can optionally be randomized by setting :attr:`PDSession.stagger_cooldown` to a positive number.

**2019-10-01: version 3.1.2**

* Fixed regression bug / departure from documentation (#17): the ``payload`` parameter does not merge with but rather completely replaces the default payload

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
