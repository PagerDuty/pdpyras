Developer Guide
---------------
These topics refer to usage of the REST API v2, and objects in code examples
named ``session`` are instances of :class:`pdpyras.APISession`, unless
otherwise specified.

Using Requests
**************
The ``get``, ``post``, ``put`` and ``delete`` methods of REST/Events API
session classes are identical to the analogous functions in `requests.Session`_
in terms of their arguments and how they return `requests.Response`_ objects.

Moreover, all of the features of `requests.Session`_ are available to the user
as they would be if using the Requests Python library directly, since
:class:`pdpyras.PDSession` and its subclasses for the REST/Events APIs are
descendants of it. 

For documentation on any other generic HTTP client features that are available,
see the Requests developer interface documentation:
<https://requests.readthedocs.io/en/latest/api/>`_

URLs
****
The first argument to most of the session methods is the URL. However, there is
no need to specify a complete API URL. Any path relative to the root of the
API, whether or not it includes a leading slash, is automatically normalized to
a complete API URL.  For instance, one can specify ``users/PABC123`` or
``/users/PABC123`` instead of ``https://api.pagerduty.com/users/PABC123``.

One can also pass the full URL of an API endpoint and it will still work, i.e.
the ``self`` property of any object can be used, and there is no need to strip
out the API base URL.

The ``r*`` (and ``j*`` methods as of version 5), i.e. ``rget``, can also accept
a dictionary object representing an API resource or a resource reference in
place of a URL, in which case the URL at its ``self`` key will be used as the
request target (see 

Query Parameters
****************
As with `Requests`_, there is no need to compose the query string (everything
that will follow ``?``) in the URL. Simply set the ``params`` keyword argument
to a dictionary, and each of the key/value pairs will be serialized to the
query string in the final URL of the request:

.. code-block:: python

    first_dan = session.rget('users', params={
        'query': 'Dan',
        'limit': 1,
        'offset': 0,
    })
    # GET https://api.pagerduty.com/users?query=Dan&limit=1&offset=0

To specify a multi-value parameter, i.e. ``include[]``, set the argument to a
list. As of v4.4.0, if a list is given, and the key name does not end with
``[]`` (which is required for all such multi-valued parameters in REST API v2),
then ``[]`` will be automatically appended to the parameter name.

.. code-block:: python

    # If there are 82 services with name matching "foo" this will return all of
    # them as a list:
    foo_services = session.list_all('services', params={
        'query': 'foo',
        'include[]': ['escalation_policies', 'teams'],
        'limit': 50,
    })
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=0
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=50
    # [{"type": "service" ...}, ... ]

Request and Response Bodies
***************************
To set the request body in a post or put request, set the ``json`` keyword
argument; its type should be ``dict``. If using
:attr:`pdpyras.APISession.rpost` or :attr:`pdpyras.APISession.rput`, the
supplied value may omit the wrapper (see "Entity Wrapping").

To obtain the response from the API, if using  ``get``, ``post``, ``put`` or
``delete``, use the returned `requests.Response`_ object. That object's
``json()`` method will return the response body decoded from JSON as a Python
dict object. Other metadata such as headers can also be obtained:

.. code-block:: python

    response = session.get('incidents')
    # The UUID of the API request, which can be supplied to PagerDuty Customer
    # Support in the event of server errors (status 5xx):
    print(response.headers['x-request-id'])

If using the ``j*`` methods, i.e. :attr:`APISession.jget`, the return value
will be the full body of the response from the API after JSON-decoding. These
methods accept the same arguments as the body of the API response if
successful; otherwise :class:`PDClientError` will be raised.

Finally, when using the ``r*`` methods, the response is the decoded body after
unwrapping, if the API endpoint returns wrapped entities (see "Entity Wrapping")

Data types
++++++++++
Main article: `Types <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types>`_

Note these analogues in structure between the JSON schema and the object
in Python:

* If the data type documented in the schema is
  "object" <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#object>`_,
  then the corresponding type of the Python object will be ``dict``.
* If the data type documented in the schema is
  `array <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU1-types#array>`_,
  then the corresponding type of the Python object will be ``list``.
* Generally speaking, the data type in the decoded object is according to the
  design of the `json <https://docs.python.org/3/library/json.html>`_ Python library.

For example, consider the example structure of an escalation policy as given in
the API reference page for ``GET /escalation_policies/{id}`` ("Get an
escalation policy").. To access the name of the second target in level 1,
assuming the variable ``ep`` represents the unwrapped escalation policy object:

.. code-block:: python

    ep['escalation_rules'][0]['targets'][1]['summary']
    # "Daily Engineering Rotation"

To add a new level, one would need to create a new escalation rule as a
dictionary object and then append it to the ``escalation rules`` property.
Using the example given in the API reference page:

.. code-block:: python

    new_rule = {
      "escalation_delay_in_minutes": 30,
      "targets": [
        {
          "id": "PAM4FGS",
          "type": "user_reference"
        },
        {
          "id": "PI7DH85",
          "type": "schedule_reference"
        }
      ]
    }
    ep['escalation_rules'].append(new_rule)
    # Save changes:
    session.rput(ep, json=ep)

Resource schemas
++++++++++++++++
Main article: `Resource Schemas <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU5-resource-schemas>`_

The details of any given resource's schema can be found in the request and
response examples from the `PagerDuty API Reference`_ pages for the resource's
respective API, as well as the page documenting the resource type itself.

Entity Wrapping
***************
See also: `Wrapped Entities <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYx-wrapped-entities>`_.
Most of PagerDuty's REST API v2 endpoints respond with their data inside of a
key at the root level of the JSON-encoded response body, and/or require the
request body be wrapped in another object that contains a single key. 

The following methods will automatically extract and return the wrapped content
of API responses, and wrap request entities for the user as appropriate:

* :attr:`pdpyras.APISession.dict_all`
* :attr:`pdpyras.APISession.find`
* :attr:`pdpyras.APISession.iter_all`
* :attr:`pdpyras.APISession.iter_cursor`
* :attr:`pdpyras.APISession.list_all`
* :attr:`pdpyras.APISession.persist`
* :attr:`pdpyras.APISession.rdelete`
* :attr:`pdpyras.APISession.rget`
* :attr:`pdpyras.APISession.rpost`
* :attr:`pdpyras.APISession.rput`

Typically (but not for all endpoints), the key ("wrapper name") is named after
the last or second to last node of the URL's path. The wrapper name is a
singular noun for an individual resource or plural for a collection of
resources. Prior to v5.0.0, the above methods may only be used on APIs that
follow these conventions, and will run into ``KeyError`` when used on
endpoints that do not. As of v5.0.0, they support non-conformal endpoints.

On some endpoints, however, entity wrapping is disabled, and the results would
be the same if using the equivalent ``j*`` method. The configuration that this
client uses to decide if entity wrapping is enabled for an endpoint or not are
stored in the module variable  ``pdpyras.ENTITY_WRAPPER_CONFIG`` and generally
follows this rule: **If the endpoint's response body or expected request body
contains only one property that points to all the content of the requested
resource, or if it is a request made to an endpoint that features pagination,
entity wrapping is enabled for the endpoint.**

Some endpoints are unusual in that the request must be wrapped but the response
is not wrapped or vice versa, i.e. creating Schedule overrides (``POST
/schedules/{id}/overrides``) or to create a status update on an incient (``POST
/incidents/{id}/status_updates``). In all such cases, the above rule still
applies, albeit differently for the request as for the response.

Pagination
**********
The method :attr:`pdpyras.APISession.iter_all` returns an iterator that yields
results from an endpoint that returns a wrapped collection of resources. By
default it will use classic, a.k.a. numeric pagination. If the endpoint
supports cursor-based pagination, it will use
:attr:`pdpyras.APISession.iter_cursor` to iterate through results instead. The
methods :attr:`pdpyras.APISession.list_all` and
:attr:`pdpyras.APISession.dict_all` will request all pages of the collection
and return the results as a list or dictionary, respectively.

Pagination functions require that the API endpoint being requested has entity
wrapping enabled, and respond with either a ``more`` or ``cursor`` property
indicating how and if to fetch the next page of results.

For example: 

.. code-block:: python

    # Example: Find all users with "Dav" in their name/email (i.e. Dave/David)
    # in the PagerDuty account:

    for dave in session.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

    # Get a dictionary of all users, keyed by email, and use it to find
    # the ID of the user whose email is ``bob@example.com``:

    users = session.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

Performance
+++++++++++
Because HTTP requests are made synchronously and not in multiple threads,
requesting all pages of data will happen one page at a time and the functions
``list_all`` and ``dict_all`` will not return until after the final HTTP
response. Simply put, the functions will take longer to return if the total
number of results is higher.

Updating, creating or deleting while paginating
+++++++++++++++++++++++++++++++++++++++++++++++
If performing page-wise operations, i.e. making changes immediately after
fetching each page of results, rather than pre-fetching all objects and then
operating on them (i.e. with :attr:`pdpyras.APISession.list_all`), an erroneous
condition can result if there is any change to the resources in the result set
that would affect their presence or position in the set. For example, creating
objects, deleting them, or changing the attribute being used for sorting or filtering.

This is because the contents are updated in real time, and pagination contents
are recalculated based on the state of the PagerDuty application at the time of
each request for a page of results. Therefore, records may be skipped or
repeated in results. Note also that changes made from other processes,
including manual edits through the PagerDuty web application, can have the same
effect.

To elaborate: let's say that each resource object in the full list is a page in
a notebook  Classic pagination with ``limit=100`` is essentially "go through
100 pages, then repeat starting with the 101st page, then with the 201st, etc."
Deleting records in between these 100-at-a-time pagination requests would be
like tearing out pages after reading them. At the time of the second page
request, what was originally the 101st page before starting will shift to
become the first page after tearing out the first hundred pages. Thus, when
going to the 101st page after finishing tearing out the first hundred pages,
the second hundred pages will be skipped over, and similarly for pages 401-500,
601-700 and so on. If attaching pages, the opposite happens: some results will be
returned more than once, because they get bumped to the next group of 100 pages.

Multi-updating
**************
Introduced in version 2.1 is support for multi-update actions using ``rput``.
As of this writing, multi-update support includes the following endpoints:

* `PUT /incidents <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODEzOQ-manage-incidents>`_
* `PUT /incidents/{id}/alerts <https://developer.pagerduty.com/api-reference/b3A6Mjc0ODE0NA-manage-alerts>`_
* PUT /priorities (documentation not yet published as of 2022-03-15, but the endpoint is functional)

For instance, to resolve two incidents with IDs ``PABC123`` and ``PDEF456``:

.. code-block:: python

    session.rput(
        "incidents",
        json=[
          {'id':'PABC123','type':'incident_reference', 'status':'resolved'},
          {'id':'PDEF456','type':'incident_reference', 'status':'resolved'},
        ],
    )

In this way, a single API request can more efficiently perform multiple update
actions.

It is important to note, however, that certain actions such as updating
incidents require the ``From`` header, which should be the login email address
of a valid PagerDuty user. To set this, pass it through using the ``headers``
keyword argument, or set the :attr:`pdpyras.APISession.default_from` property,
or pass the email address as the ``default_from`` keyword argument when
constructing the session initially.

Error handling
**************
What happens when, for any of the methods that do not return
`requests.Response`_, the API response is a non-success HTTP status, is that it
will not return the decoded body. Instead, when this happens, a
:class:`pdpyras.PDClientError` exception is raised. This way, methods can
always be expected to return the same structure of data based on the API being
used. If there is a break in this expectation, the flow is appropriately
interrupted.

As of version 2, this exception class has the `requests.Response`_ object as
its ``response`` property (whenever the exception pertains to a HTTP error).
The implementer can thus define specialized error handling logic in which the
REST API response data (i.e. headers, code and body) are directly available.

For instance, the following code prints "User not found" in the event of a 404,
prints out the user's email if the user exists, raises the underlying
exception if it's any other HTTP error code, and prints an error otherwise:

.. code-block:: python

    try:
      user = session.rget("/users/PJKL678")
      print(user['email'])

    except pdpyras.PDClientError as e:
      if e.response:
        if e.response.status_code == 404:
          print("User not found")
        else:
          raise e
      else:
        print("Non-transient network or client error")

Version 4.4.0 introduced a new error subclass, PDHTTPError, in which it can be
assumed that the error pertains to a HTTP request:

.. code-block:: python

    try:
      user = session.rget("/users/PJKL678")
      print(user['email'])

    except pdpyras.PDHTTPError as e:
      if e.response.status_code == 404:
        print("User not found")
      else:
        raise e
    except pdpyras.PDClientError as e:
      print("Non-transient network or client error")

