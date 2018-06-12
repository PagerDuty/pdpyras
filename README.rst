
===========================================
pdpyras: PagerDuty Python REST API Sessions
===========================================

A lightweight, practical REST API client for the PagerDuty REST API.

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
- HTTP connection persistence for more efficient API requests
- Automatic cooldown/reattempt for rate limiting and transient network issues
- Inclusion of required headers for PagerDuty REST API requests
- Iteration over `resource index`_ endpoints with automatic pagination
- Retrieval of individual objects matching a query
- API request profiling
- It gets the job done without getting in the way.

Usage
-----

**Example 1:** get a user:

::
  import pdpyras
  api_token = 'your-token-here'
  session = pdpyras.APISession(api_token)
  response = session.get('/users/PABC123')
  if response.ok:
    user = response.json()['user']

**Example 2:** iterate over all users and print their ID, email and name:

::
  import pdpyras
  api_token = 'your-token-here'
  session = pdpyras.APISession(api_token)
  for user in session.iter_all('/users'):
    print(user['id'], user['email'], user['name'])

Resources
---------
.. _pagination: https://v2.developer.pagerduty.com/docs/pagination
.. _Requests: http://docs.python-requests.org/en/master/
.. _`resource index`: https://v2.developer.pagerduty.com/docs/endpoints#resources-index

