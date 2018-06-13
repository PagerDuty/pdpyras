
===========================================
pdpyras: PagerDuty Python REST API Sessions
===========================================

A lightweight, practical REST API client for the PagerDuty REST API.

About
-----
This library supplies a class ``APISession`` extending the class
``requests.Session`` from the Requests_ library. This has the means to handle
the most common tasks associated with accessing the PagerDuty REST API in a
succinct manner.

Its intention is to be a practical and efficient abstraction of PagerDuty REST
API access with minimal differences on top of the underlying HTTP library. This
makes it ideal to use as the foundation of anything from a feature-rich REST API
client library to a quick-and-dirty API script.

Higher-level features, i.e. model classes for handling the particulars of any
given resource type, are left to the end user to develop as they see fit.

Features
--------
Supports Python 2.7 through 3.6

- HTTP connection persistence for more efficient API requests
- Automatic cooldown/reattempt for rate limiting and transient network issues
- Inclusion of required headers for PagerDuty REST API requests
- Iteration over `resource index`_ endpoints with automatic pagination
- Retrieval of individual objects matching a query
- API request profiling
- It gets the job done without getting in the way

Usage
-----

**Example 1:** get a user:

::
    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    response = session.get('/users/PABC123')
    if response.ok:
        user = response.json()['user']

**Example 2:** iterate over all users and print their ID, email and name:

::
    from pdpyras import APISession
    api_token = 'your-token-here'
    session = APISession(api_token)
    for user in session.iter_all('/users'):
        print(user['id'], user['email'], user['name'])

**Example 3:** Find a user exactly matching email address ``jane@example35.com``
and update their name to "Jane Doe":

::
    from pdpyras import APISession
    api_token = 'your-token-here'
    sesion = APISession(api_token)
    user = session.find('users', 'jane@example35.com', attribute='email')
    if user is not None:
        session.put(user['self'], json={
            'user':{'type':'user', 'name': 'Jane Doe'}
        })

.. _pagination: https://v2.developer.pagerduty.com/docs/pagination
.. _Requests: http://docs.python-requests.org/en/master/
.. _`resource index`: https://v2.developer.pagerduty.com/docs/endpoints#resources-index

