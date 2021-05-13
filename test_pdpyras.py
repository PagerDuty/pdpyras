#!/usr/bin/env python

"""
Unit tests for pdpyras

Python 3, or the backport of unittest.mock for Python 2, is required.

See:

https://docs.python.org/3.5/library/unittest.mock.html
https://pypi.org/project/backports.unittest_mock/1.3/
"""
import argparse
import copy
import datetime
import json
import logging
import os
import requests
import sys
import unittest

if sys.version_info.major < 3:
    import backports.unittest_mock
    backports.unittest_mock.install()

from unittest.mock import MagicMock, patch, call

import pdpyras

pdpyras.APISession.raise_if_http_error = True

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

    def __init__(self, code, text, method='GET', url=None):
        super(Response, self).__init__()
        self.status_code = code
        self.text = text
        self.ok = code < 400
        self.headers = MagicMock()
        if url:
            self.url = url
        else:
            self.url = 'https://api.pagerduty.com/resource/id'
        self.elapsed = datetime.timedelta(0,1.5)
        self.request = MagicMock()
        self.headers = {'date': 'somedate',
            'x-request-id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
        self.request.method = method
        self.json = MagicMock()
        self.json.return_value = json.loads(text)

class SessionTest(unittest.TestCase):

    def assertDictContainsSubset(self, d0, d1):
        self.assertTrue(set(d0.keys()).issubset(set(d1.keys())),
            msg="First dict is not a subset of second dict")
        self.assertEqual(d0, dict([(k, d1[k]) for k in d0]))

class EventsSessionTest(SessionTest):

    def test_send_event(self):
        sess = pdpyras.EventsAPISession('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [
            Response(202, '{"dedup_key":"abc123"}'),
            Response(202, '{"dedup_key":"abc123"}'),
            Response(202, '{"dedup_key":"abc123"}')
        ]
        with patch.object(sess, 'parent', new=parent):
            ddk = sess.trigger('testing 123', 'triggered.from.pdpyras',
                custom_details={"this":"that"}, severity='warning',
                images=[{'url':'https://http.cat/502.jpg'}])
            self.assertEqual('abc123', ddk)
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/enqueue',
                parent.request.call_args[0][1])
            self.assertDictContainsSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'X-Routing-Key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'event_action':'trigger',
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'source': 'triggered.from.pdpyras',
                        'severity': 'warning',
                        'custom_details': {'this':'that'},
                    },
                    'images': [{'url':'https://http.cat/502.jpg'}]
                },
                parent.request.call_args[1]['json'])
            ddk = sess.resolve('abc123')
            self.assertEqual(
                {
                    'event_action':'resolve',
                    'dedup_key':'abc123',
                    'routing_key':'routingkey',
                },
                parent.request.call_args[1]['json'])

            ddk = sess.acknowledge('abc123')
            self.assertEqual(
                {
                    'event_action':'acknowledge',
                    'dedup_key':'abc123',
                    'routing_key':'routingkey',
                },
                parent.request.call_args[1]['json'])

    def test_send_explicit_event(self):
        # test sending an event by calling `post` directly as opposed to any of
        # the methods written into the client for sending events
        sess = pdpyras.EventsAPISession('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [Response(202, '{"dedup_key":"abc123"}')]
        with patch.object(sess, 'parent', new=parent):
            response = sess.post('/v2/enqueue', json={
                'payload': {
                    'summary': 'testing 123',
                    'source': 'pdpyras integration',
                    'severity': 'critical'
                },
                'event_action': 'trigger'
            })
            json_sent = parent.request.call_args[1]['json']
            self.assertTrue('routing_key' in json_sent)
            self.assertEqual(json_sent['routing_key'], 'routingkey')

class APISessionTest(SessionTest):

    def debug(self, sess):
        """
        Enables debug level logging to stderr in order to see logging
        """
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        sess.log.addHandler(sh)
        sess.log.setLevel(logging.DEBUG)

    def test_oauth_headers(self):
        secret = 'randomly generated lol'
        for authtype in 'oauth2', 'bearer':
            sess = pdpyras.APISession(secret, auth_type=authtype)
            self.assertEqual(
                sess.headers['Authorization'],
                "Bearer "+secret
            )

    def test_profiler_key(self):
        sess = pdpyras.APISession('token')
        self.assertEqual(
            'post:users/{id}/contact_methods/{index}',
            sess.profiler_key(
                'POST',
                'https://api.pagerduty.com/users/PCWKOPZ/contact_methods'
            )
        )

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
        page = lambda n, t, l: {
            'users': [{'id':i} for i in range(10*n, 10*(n+1))],
            'total': t,
            'more': n<(t/10)-1,
            'limit': l
        }
        iter_param = lambda p: json.dumps({
            'limit':10, 'total': True, 'offset': 0
        })
        get.side_effect = [
            Response(200, json.dumps(page(0, 30, 10))),
            Response(200, json.dumps(page(1, 30, 10))),
            Response(200, json.dumps(page(2, 30, 10))),
        ]
        weirdurl='https://api.pagerduty.com/users?number=1'
        hook = MagicMock()
        items = list(sess.iter_all(weirdurl, item_hook=hook, total=True, page_size=10))
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

        # Test stopping iteration on non-success status
        get.reset_mock()
        error_encountered = [
            Response(200, json.dumps(page(0, 50, 10))),
            Response(200, json.dumps(page(1, 50, 10))),
            Response(200, json.dumps(page(2, 50, 10))),
            Response(400, json.dumps(page(3, 50, 10))), # break
            Response(200, json.dumps(page(4, 50, 10))),
        ]
        get.side_effect = copy.deepcopy(error_encountered)
        sess.raise_if_http_error = False
        new_items = list(sess.iter_all(weirdurl))
        self.assertEqual(items, new_items)

        # Now test raising an exception:
        get.reset_mock()
        get.side_effect = copy.deepcopy(error_encountered)
        sess.raise_if_http_error = True
        self.assertRaises(pdpyras.PDClientError, list, sess.iter_all(weirdurl))

        # Test reaching the iteration limit:
        get.reset_mock()
        bigiter = sess.iter_all('log_entries', page_size=100,
            params={'offset': '9901'})
        self.assertRaises(StopIteration, next, bigiter)

        # Test (temporary, until underlying issue in the API is resolved) using
        # the result count to increment offset instead of `limit` reported in
        # API response
        get.reset_mock()
        iter_param = lambda p: json.dumps({
            'limit':10, 'total': True, 'offset': 0
        })
        get.side_effect = [
            Response(200, json.dumps(page(0, 30, None))),
            Response(200, json.dumps(page(1, 30, 42))),
            Response(200, json.dumps(page(2, 30, 2020))),
        ]
        weirdurl='https://api.pagerduty.com/users?number=1'
        hook = MagicMock()
        items = list(sess.iter_all(weirdurl, item_hook=hook, total=True, page_size=10))
        self.assertEqual(30, len(items))

    @patch.object(pdpyras.APISession, 'rpost')
    @patch.object(pdpyras.APISession, 'iter_all')
    def test_persist(self, iterator, creator):
        user = {
            "name": "User McUserson",
            "email": "user@organization.com",
            "type": "user"
        }
        iterator.return_value = iter([user])
        sess = pdpyras.APISession('apiKey')
        sess.persist('users', 'email', user)
        creator.assert_not_called()
        iterator.return_value = iter([])
        sess.persist('users', 'email', user)
        creator.assert_called_with('users', json=user)

    def test_postprocess(self):
        logger = MagicMock()
        response = Response(201, json.dumps({'key':'value'}), method='POST')
        response.url = 'https://api.pagerduty.com/users/PCWKOPZ/contact_methods'
        sess = pdpyras.APISession('apikey')
        sess.postprocess(response)
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
        sess.postprocess(response)
        # Individual resource access endpoint
        self.assertEqual(1, sess.api_call_counts['get:users/{id}'])
        self.assertEqual(1.5, sess.api_time['get:users/{id}'])
        response = Response(500, json.dumps({'key': 'value'}), method='GET')
        response.url = 'https://api.pagerduty.com/users/PCWKOPZ/contact_methods'
        sess = pdpyras.APISession('apikey')
        sess.log = logger
        sess.postprocess(response)
        if not (sys.version_info.major == 3 and sys.version_info.minor == 5):
            # These assertion methods are not available in Python 3.5
            logger.error.assert_called_once()
            logger.debug.assert_called_once()
        # Make sure we have correct logging params / number of params:
        logger.error.call_args[0][0]%logger.error.call_args[0][1:]
        logger.debug.call_args[0][0]%logger.debug.call_args[0][1:]

    def test_raise_on_error(self):
        self.assertRaises(pdpyras.PDClientError, pdpyras.raise_on_error,
            Response(400, json.dumps({})))
        try:
            pdpyras.raise_on_error(Response(400, json.dumps({})))
        except pdpyras.PDClientError as e:
            self.assertTrue(e.response is not None)

    @patch.object(pdpyras.APISession, 'postprocess')
    def test_request(self, postprocess):
        sess = pdpyras.APISession('12345')
        parent = Session()
        request = MagicMock()
        # Expected headers:
        headers_get = {
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': 'Token token=12345',
            'User-Agent': 'pdpyras/%s python-requests/%s Python/%d.%d'%(
                pdpyras.__version__,
                requests.__version__,
                sys.version_info.major,
                sys.version_info.minor
            ),
        }
        # Check default headers:
        self.assertDictContainsSubset(headers_get, sess.prepare_headers('GET'))
        headers_get.update(sess.prepare_headers('GET'))
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
            postprocess.assert_called_with(request.return_value)
            headers = headers_get.copy()
            request.assert_called_once_with('GET',
                'https://api.pagerduty.com/users', headers=headers_get,
                stream=False, timeout=pdpyras.TIMEOUT)
            request.reset_mock()

            # Test POST/PUT (in terms of code coverage they're identical)
            request.return_value = Response(201, json.dumps({'user': user}))
            sess.request('post', 'users', json={'user':user})
            request.assert_called_once_with(
                'POST', 'https://api.pagerduty.com/users',
                headers=headers_post, json={'user':user}, stream=False, timeout=pdpyras.TIMEOUT)
            request.reset_mock()

            # Test GET with parameters and using a HTTP verb method
            request.return_value = Response(200, json.dumps({'users': [user]}))
            user_query = {'query': 'user@example.com'}
            r = sess.get('/users', params=user_query)
            request.assert_called_once_with(
                'GET', 'https://api.pagerduty.com/users',
                headers=headers_get, params=user_query, stream=False,
                allow_redirects=True, timeout=pdpyras.TIMEOUT)
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
                data=None, timeout=pdpyras.TIMEOUT)
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
                    pdpyras.HTTPError("D'oh!")
                ]*sess.max_network_attempts
                returns.append(Response(200, json.dumps({'user': user})))
                request.side_effect = returns
                r = sess.get('/users/P123456')
                self.assertEqual(sess.max_network_attempts+1,
                    request.call_count)
                self.assertEqual(sess.max_network_attempts, sleep.call_count)
                self.assertTrue(r.ok)
                request.reset_mock()
                sleep.reset_mock()

                # Now test handling a non-transient error when the client
                # library itself hits odd issues that it can't handle, i.e.
                # network:
                raises = [pdpyras.RequestException("D'oh!")]*(
                    sess.max_network_attempts-1)
                raises.extend([pdpyras.HTTPError("D'oh!")]*2)
                request.side_effect = raises
                self.assertRaises(pdpyras.PDClientError, sess.get, '/users')
                self.assertEqual(sess.max_network_attempts+1,
                    request.call_count)
                self.assertEqual(sess.max_network_attempts, sleep.call_count)

                # Test custom retry logic:
                sess.retry[404] = 3
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({'user': user})),
                ]
                r = sess.get('/users/P123456')
                self.assertEqual(200, r.status_code)
                # Test retry logic with too many 404s
                sess.retry[404] = 1
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({'user': user})),
                ]
                sess.log = MagicMock()
                r = sess.get('/users/P123456')
                self.assertEqual(404, r.status_code)

    def test_resource_envelope(self):
        do_http_things = MagicMock()
        response = MagicMock()
        do_http_things.return_value = response
        my_self = pdpyras.APISession('some_key')
        self.debug(my_self)
        dummy_session = MagicMock()
        def reset_mocks():
            do_http_things.reset_mock()
            response.reset_mock()
            do_http_things.return_value = response
            dummy_session.reset_mock()

        # OK response, good JSON: JSON-decode and unpack response
        response.ok = True
        response.json.return_value = {'service': {'name': 'value'}}
        do_http_things.__name__ = 'rput' # just for instance
        self.assertEqual(
            pdpyras.resource_envelope(do_http_things)(my_self,
                '/services/PTHINGY'),
            {'name': 'value'}
        )
        reset_mocks()

        # OK response, bad JSON: raise exception.
        response.ok = True
        do_http_things.__name__ = 'rput' # just for instance
        response.json.side_effect = [ValueError('Bad JSON!')]
        self.assertRaises(pdpyras.PDClientError,
            pdpyras.resource_envelope(do_http_things), my_self, '/services')
        reset_mocks()

        # OK response, but ruh-roh we hit an anti-pattern (probably won't exist
        # except maybe in beta/reverse-engineered endpoints; this design is thus
        # anticipatory rather than practical). Raise exception.
        do_http_things.reset_mock()
        response.reset_mock()
        response.json = MagicMock()
        response.ok = True
        do_http_things.return_value = response
        do_http_things.__name__ = 'rput' # just for instance
        response.json.return_value = {'nope': 'nopenope'}
        self.assertRaises(pdpyras.PDClientError,
            pdpyras.resource_envelope(do_http_things), my_self, '/services')
        reset_mocks()

        # Not OK response, raise (daisy-chained w/raise_on_error decorator)
        response.reset_mock()
        response.ok = False
        do_http_things.__name__ = 'rput' # just for instance
        self.assertRaises(pdpyras.PDClientError,
            pdpyras.resource_envelope(do_http_things), my_self, '/services')
        reset_mocks()

        # GET /<index>: use a different envelope name
        response.ok = True
        users_array = [{"type":"user","email":"user@example.com",
            "summary":"User McUserson"}]
        response.json.return_value = {'users': users_array}
        do_http_things.__name__ = 'rget'
        dummy_session.url = 'https://api.pagerduty.com'
        self.assertEqual(users_array,
            pdpyras.resource_envelope(do_http_things)(dummy_session, '/users',
                query='user'))
        reset_mocks()

        # Test request body JSON envelope stuff in post/put
        # Response body validation
        do_http_things.__name__ = 'rpost'
        user_payload = {'email':'user@example.com', 'name':'User McUserson'}
        self.assertRaises(
            pdpyras.PDClientError,
            pdpyras.resource_envelope(do_http_things),
            dummy_session, '/users', json=user_payload
        )
        reset_mocks()
        # Add type property; should work now and automatically pack the user
        # object into a JSON object inside the envelope.
        user_payload['type'] = 'user'
        do_http_things.__name__ = 'rpost'
        response.ok = True
        created_user = user_payload.copy()
        created_user['id'] = 'P456XYZ'
        response.json.return_value = {'user':created_user}
        self.assertEqual(
            created_user,
            pdpyras.resource_envelope(do_http_things)(dummy_session, '/users',
                json=user_payload)
        )
        do_http_things.assert_called_with(dummy_session, '/users',
            json={'user':user_payload})

        reset_mocks()
        # Test auto-envelope functionality for multi-update
        # TODO: This test is loosely coupled but somewhat naive. Tighten if need
        # be.
        incidents = [{'id':'PABC123'}, {'id':'PDEF456'}]
        do_http_things.__name__ = 'rput'
        response.ok = True
        updated_incidents = copy.deepcopy(incidents)
        response.json.return_value = {'incidents': updated_incidents}
        self.assertEqual(
            updated_incidents,
            pdpyras.resource_envelope(do_http_things)(dummy_session,
                '/incidents', json=incidents)
        )


    @patch.object(pdpyras.APISession, 'put')
    def test_resource_path(self, put_method):
        sess = pdpyras.APISession('some-key')
        resource_url = 'https://api.pagerduty.com/users/PSOMEUSR'
        user = {
            'id': 'PSOMEUSR',
            'type': 'user',
            'self': resource_url,
            'name': 'User McUserson',
            'email': 'user@organization.com'
        }
        put_method.return_value = Response(200, json.dumps({'user': user}),
            method='PUT', url=resource_url)
        sess.rput(user, json=user)
        put_method.assert_called_with(resource_url, json={'user': user})

    @patch.object(pdpyras.APISession, 'get')
    def test_rget(self, get):
        response200 = Response(200, '{"user":{"type":"user_reference",'
            '"email":"user@example.com","summary":"User McUserson"}}')
        get.return_value = response200
        s = pdpyras.APISession('token')
        self.assertEqual(
            {"type":"user_reference","email":"user@example.com",
                "summary":"User McUserson"},
            s.rget('/users/P123ABC'))
        # This is (forcefully) valid JSON but no matter; it should raise
        # PDClientErorr nonetheless
        response404 = Response(404, '{"user": {"email": "user@example.com"}}')
        get.reset_mock()
        get.return_value = response404
        self.assertRaises(pdpyras.PDClientError, s.rget, '/users/P123ABC')

    @patch.object(pdpyras.APISession, 'rget')
    def test_subdomain(self, rget):
        rget.return_value = [{'html_url': 'https://something.pagerduty.com'}]
        sess = pdpyras.APISession('key')
        self.assertEqual('something', sess.subdomain)
        self.assertEqual('something', sess.subdomain)
        rget.assert_called_once_with('users', params={'limit':1})

    def test_truncated_token(self):
        sess = pdpyras.APISession('abcd1234')
        self.assertEqual('*1234', sess.trunc_token)


class ChangeEventsSessionTest(SessionTest):
    @patch('pdpyras.ChangeEventsAPISession.event_timestamp',
        '2020-03-25T00:00:00Z')
    def test_submit_change_event(self):
        sess = pdpyras.ChangeEventsAPISession('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [ Response(202, '{"id":"abc123"}') ]
        with patch.object(sess, 'parent', new=parent):
            ddk = sess.submit(
                    'testing 123',
                    'triggered.from.pdpyras',
                    custom_details={"this":"that"},
                    links=[{'href':'https://http.cat/502.jpg'}],
                    )
            self.assertEqual('abc123', ddk)
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/change/enqueue',
                parent.request.call_args[0][1])
            self.assertDictContainsSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'X-Routing-Key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'timestamp': '2020-03-25T00:00:00Z',
                        'source': 'triggered.from.pdpyras',
                        'custom_details': {'this':'that'},
                    },
                    'links': [{'href':'https://http.cat/502.jpg'}]
                },
                parent.request.call_args[1]['json'])
    @patch('pdpyras.ChangeEventsAPISession.event_timestamp',
        '2020-03-25T00:00:00Z')
    def test_submit_lite_change_event(self):
        sess = pdpyras.ChangeEventsAPISession('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [ Response(202, '{"id":"abc123"}') ]
        with patch.object(sess, 'parent', new=parent):
            ddk = sess.submit('testing 123')
            self.assertEqual('abc123', ddk)
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/change/enqueue',
                parent.request.call_args[0][1])
            self.assertDictContainsSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'X-Routing-Key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'timestamp': '2020-03-25T00:00:00Z',
                    },
                },
                parent.request.call_args[1]['json'])

class APIUtilsTest(unittest.TestCase):

    def test_tokenize_url_path(self):
        cm_path = ('users', '{id}', 'contact_methods', '{index}')
        cm_path_str = 'users/PABC123/contact_methods'
        baseurl = 'https://rest.pd/'
        self.assertEqual(cm_path, pdpyras.tokenize_url_path(cm_path_str))
        self.assertEqual(cm_path, pdpyras.tokenize_url_path(baseurl+cm_path_str,
            baseurl=baseurl))
        self.assertRaises(ValueError, pdpyras.tokenize_url_path,
            '/https://api.pagerduty.com/?')
        self.assertRaises(ValueError, pdpyras.tokenize_url_path,
            'https://api.pagerduty.com/')
        self.assertRaises(ValueError, pdpyras.tokenize_url_path,
            'https://api.pagerduty.com')
        self.assertRaises(ValueError, pdpyras.tokenize_url_path,
            '/')
        self.assertRaises(ValueError, pdpyras.tokenize_url_path,
            '/users/')
        self.assertEqual(('users','{index}'),
            pdpyras.tokenize_url_path('/users'))

    def test_plural_deplural(self):
        # forward
        for r_name in ('escalation_policies', 'services', 'log_entries'):
            self.assertEqual(
                r_name,
                pdpyras.resource_name(pdpyras.object_type(r_name))
            )
        # reverse
        for o_name in ('escalation_policy', 'service', 'log_entry'):
            self.assertEqual(
                o_name,
                pdpyras.object_type(pdpyras.resource_name(o_name))
            )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('-d', dest='debug', action='store_true', default=0)
    unittest.main()

if __name__ == '__main__':
    main()
