**2024-06-03: Version 5.4.1: Final bugfix release**

This version backports minor fixes from the new `pagerduty <https://pypi.org/project/pagerduty/>`_ package and adds a deprecation warning at import time:

* The ``r*`` and ``j*`` shorthand request functions no longer error out when the API (i.e. ``PUT /teams/{team_id}/users/{user_id}``) responds with HTTP 204.
* ``iter_all`` now passes user-supplied arguments thru to ``iter_cursor`` when short-circuiting to that method for cursor-based pagination endpoints.

**2024-12-19: Version 5.4.0:**

* The package build now includes a universal Python 3 wheel. Contributed by @ymyzk

**2024-10-04: Version 5.3.0:**

* Add support for searching by non-string fields in :attr:`pdpyras.APISession.find`

**2023-12-28: Version 5.2.0:**

* Expanded use of type hints in place of ``:rtype`` Sphinx directive
* Remove unused dependency ``deprecation``
* Fix bug: path ``/tags/{id}/{entity_type}`` breaks entity wrapping logic (`issue #130 <https://github.com/PagerDuty/pdpyras/issues/130>`_)

**2023-11-15: Version 5.1.3:**

* Remove deprecated escape sequences, which were causing downstream linter/unit test errors, from docstrings
* Remove references to removed properties from the module reference that were causing Sphinx warnings

**2023-09-12: Version 5.1.2:**

* Address issue `#115 <https://github.com/PagerDuty/pdpyras/issues/115>`_ by adding default values to :attr:`pdpyras.PDSession.retry` for Events and Change Events API client classes
* Upgrade CI images
* Add support for Python 3.11

**2023-07-18: Version 5.1.1:**

* Fix bug: using ``iter_all`` on an endpoint that supports cursor-based pagination should correctly call out to ``iter_cursor`` (it was making the call but with a removed keyword argument)

**2023-06-26: Version 5.1.0:**

* **New features:**
    * Add the ability to specify a timestamp when submitting a change event by supplying keyword argument ``timestamp`` to ``ChangeEventsAPISession.submit``
    * Explicitly include the upstream exception as cause when raising due to a non-transient network error
* **Breaking Changes:**
    * Removal of deprecated functions:
        * ``pdpyras.tokenize_url_path``
        * ``pdpyras.resource_envelope``
        * ``pdpyras.object_type``
        * ``pdpyras.resource_name``
        * ``pdpyras.raise_on_error``
    * Removal of deprecated keyword arguments:
        * ``__init__`` for all session classes no longer accepts ``name``
        * ``pdpyras.APISession.iter_all`` no longer accepts ``paginate``
        * ``pdpyras.APISession.iter_cursor`` no longer accepts ``attribute``
    * Removal of deprecated object methods/properties:
        * ``pdpyras.APISession.profiler_key``
        * ``pdpyras.APISession.raise_if_http_error``

**2023-06-07: Version 5.0.4:**

* Fix bug: ``/users/me`` is also ambiguously matched by canonical path ``/users/{id}``; the solution by @asmith-pd short-circuits if there is an exact match for the URL to a canonical path

**2023-05-17: Version 5.0.3:**

* Incorporate bugfix from `#103 <https://github.com/PagerDuty/pdpyras/issues/103>`_ by @av1m
* Fix the generic issue behind `#102 <https://github.com/PagerDuty/pdpyras/issues/102>`_ (unsafe mix of string formatting styles)
* In HTTP retry exhaustion messages, print only the limit that got reached and not necessarily the per-status HTTP retry

**2023-05-01: Version 5.0:**
Note: version 5.0.0 has been yanked; patch release v5.0.1 addresses an issue in ``setup.py``.

* **New Features:**
    * Methods that assume entity wrapping like ``rget`` and ``iter_all`` now support all API endpoints
    * Property ``PDSession.print_debug`` enables printing verbose log messages to ``sys.stderr``
* **Breaking Changes:**
    * Removal of the deprecated method ``PDSession.set_api_key``
    * End support for `Python v3.5 <https://www.python.org/downloads/release/python-350/>`_, which has reached end-of-life.
* **Deprecations:** the following will be removed in the next minor release, and use of them in v5.0.0 will trigger warnings:
    * Keyword argument ``name`` of the session constructor: this previously set the name of the logger; now it has no effect.
    * Keyword argument ``paginate`` of ``APISession.iter_all``: this previously could be set to ``False`` to make ``iter_all`` stop iteration after the first page of results; now it has no effect.
    * Keyword argument ``attribute`` of ``APISession.iter_cursor``: this previously could be used to specify the entity wrapper name of results. The wrapper is now determined automatically and this argument has no effect.
    * Function ``tokenize_url_path``
    * Function (decorator) ``resource_envelope``
    * Function ``object_type``
    * Function ``raise_on_error``
    * Function ``resource_name``
    * Property ``APISession.raise_if_http_error``: this previously allowed partial results to be returned from ``iter_all`` in the case of HTTP errors; now it has no effect.
    * Function ``APISession.profiler_key``

**2022-10-13: Version 4.5.2**

* The default value for request timeouts is now 60s.
* Method ``api_key_access`` is now implemented as a property in the class ``APISession``. Formerly it was implemented in the parent class ``PDSession`` and inherited in classes that did not need it and could not use it.
* Bug in version 4.5.1 (removed) in package distribution/build fixed

**2022-02-22: Version 4.5.0**

* Add a new API generator ``iter_cursor`` to :class:`APISession` that yields results from API endpoints that support cursor-based pagination, requesting the next page of results whenever needed.

**2022-01-18: Version 4.4.0**

* Added new error class :class:`PDHTTPError` for strictly application-level errors (i.e. HTTP responses vs. network errors), inherits from :class:`PDClientError`
* Removed unnecessary dependencies that were hold-outs from Python 2.7 compatibility (deprecated)
* Automatically add square brackets to query parameters that are of list type if the user forgets to do so, per the requirement of using `set filters <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU2-filtering#set-filters>`_
* Fix bug: the :attr:`PDSession.stagger_cooldown` feature added in version 3.2 only applied to network error/retry; it now applies to all forms of retrial
* Add "update" keyword argument to :attr:`APISession.persist` that updates any existing resource with the provided values

**2021-06-28: Version 4.3.0**

* Make timeout configurable per-session as an instance variable (based on `a suggestion in pull #48 <https://github.com/PagerDuty/pdpyras/pull/48#discussion_r529711040>`_ made by @badnetmask)
* Drop support for Python 2.7
* Improve code samples formatting improvement (@jackton1 / `#65 <https://github.com/PagerDuty/pdpyras/pull/65>`_)
* Replace deprecated escape sequence for the double-splat operator in docstrings (@ashwin153 / `#68 <https://github.com/PagerDuty/pdpyras/pull/68>`_)

**2021-05-13: Version 4.2.1**

* Implement work-around for issue in response plays API (issue `#61 <https://github.com/PagerDuty/pdpyras/issues/61>`_)

**2021-05-04: Version 4.2.0**

* Add new change events API client class (@hunner / `#56 <https://github.com/PagerDuty/pdpyras/pull/56>`_)

**2021-03-18: Version 4.1.4**

* Fix regression in :attr:`EventsAPISession.post`
    * Use case: explicitly-defined body (``json`` keyword argument) without a ``routing_key`` parameter
    * This was previously possible (before version 4.1.3) with the ``X-Routing-Key`` header (an undocumented API feature)

**2021-03-10: Version 4.1.3**

* Use documented method for including the routing key in the request for API V2 (addresses `#53 <https://github.com/PagerDuty/pdpyras/issues/53>`_)
* Add warning for Python 2.7
* Configurable timeout: argument to ``requests.Session.request`` set in default args to backwards-compatible 5 second value that can be set at the module level (@ctrlaltdel / `#48 <https://github.com/PagerDuty/pdpyras/pull/48>`_)

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
