# PagerDuty REST API Client

This module supplies a class `PDREST`, an extension of `requests.Session`. This class makes it more convenient to perform PagerDuty REST API requests by eliminating redundant tasks such as:

* Prepending the PagerDuty REST API's base URL
* Setting the necessary headers 
* Rate-limiting cooldown

Its intention is not to be a full client library (i.e. with model classes) but a practical building block for basic scripts and projects.

## Usage

Example: get users 150-200 

```
import pdrac

users = []
api_token = 'your-token-here'
api_session = pdrac.REST(api_token)

response = api_session.get('/users', params={'limit':50, 'offset': 150})
if response.ok:
  users.extend(response.json()['users'])
```

## TODO

* Pagination & iteration over resources
* Lookup of objects by name
* Memoization
