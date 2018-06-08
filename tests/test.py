#!/usr/bin/env python

"""
Unit tests for pdpyras

Python 3, or the backport of unittest.mock for Python 2, is required.

See:

https://docs.python.org/3.5/library/unittest.mock.html
https://pypi.org/project/backports.unittest_mock/1.3/
"""

import json
import os
import sys
import unittest

if sys.version_info.major < 3:
    import backports.unittest_mock
    backports.unittest_mock.install()
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pdpyras

class Session(object):
    """
    Python reqeusts.Session mockery class
    """
    request = None
    headers = None

class Response(object):
    """Mock class for emulating requests.Response objects
    
    Look for existing use of this class for examples on how to use.
    
    @TODO Replace with stuff from unittest.mock once fully migrated to Python 3
    """

    def __init__(self, code, text):
        self.status_code = code
        self.text = text
        self.ok = code < 400
        self.url = 'https://api.pagerduty.com/resource/id'

    def json(self):
        return json.loads(self.text)


class APISessionTest(unittest.TestCase):

    @patch.object(pdpyras.APISession, 'iter_all')
    def test_find(self, iter_all):
        # TODO
        # This function calls pdpyras.APISession.iter_all so we mock it here
        pass 
    
    @patch.object(pdpyras.APISession, 'request')
    def test_iter_all(self, request):
        # TODO
        # This function calls pdpyras.APISession.request repeatedly so we mock
        # it here
        pass

    def test_request(self):
        sess = pdpyras.APISession('12345')
        parent = Session()
        request = MagicMock()
        # Expected headers:
        headers_get = {
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': 'Token token=12345'
        }
        # Check default headers:
        self.assertDictContainsSubset(headers_get, sess.headers)
        headers_get.update(sess.headers)
        # When submitting post/put, the content type should also be set
        headers_post = headers_get.copy()
        headers_post.update({'Content-Type': 'application/json'})
        parent.headers = headers_get

        with patch.object(sess, 'parent', new=parent):
            parent.request = request
            # Test bad request method
            self.assertRaises(
                pdpyras.PDClientError,
                sess.request,
                *['poke', '/something']
            )
            request.assert_not_called()
            # Dummy user
            user = {
                "name": "User McUserson",
                "type": "user",
                "role": "limited_user",
                "email": "user@example.com",
            }
            users = {'users': user} 

            # Test basic GET 
            request.return_value = Response(200, json.dumps(users))
            r = sess.request('get', '/users')
            headers = headers_get.copy()
            request.assert_called_once_with('GET',
                'https://api.pagerduty.com/users', headers=headers_get,
                stream=False)
            request.reset_mock()

            # Test POST/PUT (in terms of code coverage they're identical)
            request.return_value = Response(201, json.dumps({'user': user}))
            sess.request('post', 'users', json={'user':user})
            request.assert_called_once_with(
                'POST', 'https://api.pagerduty.com/users',
                headers=headers_post, json={'user':user}, stream=False)
            request.reset_mock()

            # Test GET with parameters and using a HTTP verb method
            request.return_value = Response(200, json.dumps({'users': [user]}))
            user_query = {'query': 'user@example.com'}
            r = sess.get('/users', params=user_query)
            request.assert_called_once_with(
                'GET', 'https://api.pagerduty.com/users',
                headers=headers_get, params=user_query, stream=False,
                allow_redirects=True)
            request.reset_mock()

            # Test a POST request with additional headers 
            request.return_value = Response(201, json.dumps({'user': user}))
            headers_special = headers_post.copy()
            headers_special.update({"X-Tra-Special-Header": "1"})
            r = sess.post('/users/PD6LYSO/future_endpoint',
                headers=headers_special, json={'user':user}) 
            request.assert_called_once_with('POST',
                'https://api.pagerduty.com/users/PD6LYSO/future_endpoint',
                headers=headers_special, json={'user': user}, stream=False,
                data=None)
            request.reset_mock()

            # Test hitting the rate limit
            request.side_effect = [
                Response(429, json.dumps({'error': {'message': 'chill out'}})),
                Response(429, json.dumps({'error': {'message': 'chill out'}})),
                Response(200, json.dumps({'user': user})),
            ]
            with patch.object(pdpyras.time, 'sleep') as sleep:
                r = sess.get('/users')
                self.assertTrue(r.ok) # should only return after success
                self.assertEquals(3, request.call_count)
                self.assertEquals(2, sleep.call_count)
            request.reset_mock()
            request.side_effect = None

            # Test a 401 (should raise Exception)
            request.return_value = Response(401, json.dumps({
                'error': {
                    'code': 2006,
                    'message': "You shall not pass.",
                }
            }))
            self.assertRaises(pdpyras.PDClientError, sess.request, 'get', 
                '/services')
            request.reset_mock()

            # Test retry logic;
            with patch.object(pdpyras.time, 'sleep') as sleep:
                # Test getting a connection error and succeeding the final time.
                returns = [
                    pdpyras.ConnectionError("D'oh!")
                ]*sess.max_attempts
                returns.append(Response(200, json.dumps({'user': user})))
                request.side_effect = returns
                r = sess.get('/users/P123456')
                self.assertEquals(sess.max_attempts+1, request.call_count)
                self.assertEquals(sess.max_attempts, sleep.call_count)
                self.assertTrue(r.ok)
                request.reset_mock()
                sleep.reset_mock()

                # Now test a non-transient error:
                request.side_effect = [
                    pdpyras.ConnectionError("D'oh!")
                ]*(sess.max_attempts+1)
                self.assertRaises(pdpyras.PDClientError, sess.get, '/users')
                self.assertEquals(sess.max_attempts+1, request.call_count)
                self.assertEquals(sess.max_attempts, sleep.call_count)

    @patch.object(pdpyras.APISession, 'iter_all')
    def test_subdomain(self, iter_all):
        # TODO
        pass

unittest.main()
