#!/usr/bin/env python

"""
Unit tests for pdpyras

Python 3, or the backport of unittest.mock for Python 2, is required.

See:

https://docs.python.org/3.5/library/unittest.mock.html
https://pypi.org/project/backports.unittest_mock/1.3/
"""
import argparse
import datetime
import json
import logging
import os
import sys
import unittest

if sys.version_info.major < 3:
    import backports.unittest_mock
    backports.unittest_mock.install()

from unittest.mock import MagicMock, patch, call

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
    """

    def __init__(self, code, text, method='GET'):
        self.status_code = code
        self.text = text
        self.ok = code < 400
        self.url = 'https://api.pagerduty.com/resource/id'
        self.elapsed = datetime.timedelta(0,1.5)
        self.request = MagicMock()
        self.request.method = method

    def json(self):
        return json.loads(self.text)


class APISessionTest(unittest.TestCase):

    def assertDictContainsSubset(self, d0, d1):
        self.assertEqual(d0, dict([(k, d1[k]) for k in d0 if k in d1]))

    def debug(self, sess):
        """
        Enables debug level logging to stderr in order to see logging 
        """
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        sess.log.addHandler(sh)
        sess.log.setLevel(logging.DEBUG)

    @patch.object(pdpyras.APISession, 'iter_all')
    def test_find(self, iter_all):
        sess = pdpyras.APISession('token')
        iter_all.return_value = iter([
            {'type':'user', 'name': 'Someone Else', 'email':'some1@me.me.me'},
            {'type':'user', 'name': 'Space Person', 'email':'some1@me.me '},
            {'type':'user', 'name': 'Someone Personson', 'email':'some1@me.me'},
        ])
        self.assertEqual(
            'Someone Personson',
            sess.find('users', 'some1@me.me', attribute='email')['name']
        )
        iter_all.assert_called_with('users', params={'query':'some1@me.me'})

    @patch.object(pdpyras.APISession, 'get')
    def test_iter_all(self, get):
        sess = pdpyras.APISession('token')
        sess.log = MagicMock() # Or go with self.debug(sess) to see output
        sess.default_page_size = 10
        page = lambda n, t: {
            'users': [{'id':i} for i in range(10*n, 10*(n+1))],
            'total': t,
            'more': n<(t/10)-1
        }
        iter_param = lambda p: json.dumps({
            'limit':10, 'total': True, 'offset': 0
        })
        get.side_effect = [
            Response(200, json.dumps(page(0, 30))),
            Response(200, json.dumps(page(1, 30))),
            Response(200, json.dumps(page(2, 30))),
        ]
        weirdurl='https://api.pagerduty.com/users?number=1'
        hook = MagicMock()
        items = list(sess.iter_all(weirdurl, item_hook=hook, total=True))
        self.assertEqual(3, get.call_count)
        self.assertEqual(30, len(items))
        get.assert_has_calls(
            [
                call(weirdurl, params={'limit':10, 'total':1, 'offset':0}),
                call(weirdurl, params={'limit':10, 'total':1, 'offset':10}),
                call(weirdurl, params={'limit':10, 'total':1, 'offset':20}),
            ],
        )
        hook.assert_any_call({'id':14}, 15, 30)
        get.reset_mock()

        # Test stopping iteration on non-success status
        get.side_effect = [
            Response(200, json.dumps(page(0, 50))),
            Response(200, json.dumps(page(1, 50))),
            Response(200, json.dumps(page(2, 50))),
            Response(400, json.dumps(page(3, 50))), # break
            Response(200, json.dumps(page(4, 50))),
        ]
        new_items = list(sess.iter_all(weirdurl))
        self.assertEqual(items, new_items)

    def test_profile(self):
        response = Response(201, json.dumps({'key':'value'}), method='POST')
        response.url = 'https://api.pagerduty.com/users/PCWKOPZ/contact_methods'
        sess = pdpyras.APISession('apikey')
        sess.profile(response)
        # Nested index endpoint
        self.assertEqual(
            1,
            sess.api_call_counts['post:users/{id}/contact_methods/{index}']
        )
        self.assertEqual(
            1.5,
            sess.api_time['post:users/{id}/contact_methods/{index}']
        )
        response.url = 'https://api.pagerduty.com/users/PCWKOPZ'
        response.request.method = 'GET'
        sess.profile(response)
        # Individual resource access endpoint
        self.assertEqual(1, sess.api_call_counts['get:users/{id}'])
        self.assertEqual(1.5, sess.api_time['get:users/{id}'])

    @patch.object(pdpyras.APISession, 'profile')
    def test_request(self, profile):
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

            # Test basic GET & profiling
            request.return_value = Response(200, json.dumps(users))
            r = sess.request('get', '/users')
            profile.assert_called_with(request.return_value)
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
            request.return_value = Response(201, json.dumps({'user': user}),
                method='POST')
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
                self.assertEqual(3, request.call_count)
                self.assertEqual(2, sleep.call_count)
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
                    pdpyras.Urllib3Error("D'oh!")
                ]*sess.max_attempts
                returns.append(Response(200, json.dumps({'user': user})))
                request.side_effect = returns
                r = sess.get('/users/P123456')
                self.assertEqual(sess.max_attempts+1, request.call_count)
                self.assertEqual(sess.max_attempts, sleep.call_count)
                self.assertTrue(r.ok)
                request.reset_mock()
                sleep.reset_mock()

                # Now test handling a non-transient error:
                raises = [pdpyras.RequestsError("D'oh!")]*(sess.max_attempts-1)
                raises.extend([pdpyras.Urllib3Error("D'oh!")]*2)
                request.side_effect = raises
                self.assertRaises(pdpyras.PDClientError, sess.get, '/users')
                self.assertEqual(sess.max_attempts+1, request.call_count)
                self.assertEqual(sess.max_attempts, sleep.call_count)

    @patch.object(pdpyras.APISession, 'iter_all')
    def test_subdomain(self, iter_all):
        iter_all.return_value = iter([
            {'html_url': 'https://something.pagerduty.com'}
        ])
        sess = pdpyras.APISession('key')
        self.assertEqual('something', sess.subdomain)
        self.assertEqual('something', sess.subdomain)
        iter_all.assert_called_once_with('users', params={'limit':1})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('-d', dest='debug', action='store_true', default=0)
    unittest.main()

if __name__ == '__main__':
    main()
