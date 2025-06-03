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
import requests
import sys
import unittest

from json.decoder import JSONDecodeError
from unittest.mock import Mock, MagicMock, patch, call

import pdpyras

class SessionTest(unittest.TestCase):
    def assertDictContainsSubset(self, d0, d1):
        self.assertTrue(set(d0.keys()).issubset(set(d1.keys())),
            msg="First dict is not a subset of second dict")
        self.assertEqual(d0, dict([(k, d1[k]) for k in d0]))

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
            self.url = 'https://api.pagerduty.com'
        self.elapsed = datetime.timedelta(0,1.5)
        self.request = Mock(url=self.url)
        self.headers = {'date': 'somedate',
            'x-request-id': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'}
        self.request.method = method
        self.json = MagicMock()
        try:
            self.json.return_value = json.loads(text)
        except JSONDecodeError as e:
            self.json.side_effect = e

class URLHandlingTest(unittest.TestCase):

    def test_canonical_path(self):
        identified_urls = [
            (
                '/services/{id}',
                '/services/POOPBUG',
            ),
            (
                '/automation_actions/actions/{id}/teams/{team_id}',
                '/automation_actions/actions/PABC123/teams/PDEF456',
            ),
            (
                '/status_dashboards/url_slugs/{url_slug}/service_impacts',
                '/status_dashboards/url_slugs/my-awesome-dashboard/service_impacts',
            ),
            (
                '/{entity_type}/{id}/change_tags',
                '/services/POOPBUG/change_tags',
            ),
            ( # for https://github.com/PagerDuty/pdpyras/pull/109
                '/users/me',
                '/users/me',
            ),
        ]
        for (pattern, url) in identified_urls:
            base_url = 'https://api.pagerduty.com'
            self.assertEqual(pattern, pdpyras.canonical_path(base_url, url))

    def test_is_path_param(self):
        self.assertTrue(pdpyras.is_path_param('{id}'))
        self.assertFalse(pdpyras.is_path_param('services'))

    def test_normalize_url(self):
        urls_expected = [
            (
                ('https://api.pagerduty.com/', 'users'),
                'https://api.pagerduty.com/users',
            ),
            (
                ('https://api.pagerduty.com', '/users'),
                'https://api.pagerduty.com/users',
            ),
            (
                (
                    'https://api.pagerduty.com',
                    'https://api.pagerduty.com/users',
                ),
                'https://api.pagerduty.com/users',
            )
        ]
        for (base_url_url, expected_url) in urls_expected:
            self.assertEqual(
                expected_url,
                pdpyras.normalize_url(*base_url_url)
            )
        invalid_input = [ # URL does not start with base_url
            (
                'https://api.pagerduty.com/incidents',
                'https://events.pagerduty.com/api/v2/enqueue',
            ),
            (
                'https://api.pagerduty.com/services',
                'https://some.shady-site.com/read-auth-headers',
            )
        ]
        for args in invalid_input:
            self.assertRaises(pdpyras.URLError, pdpyras.normalize_url, *args)

class EntityWrappingTest(unittest.TestCase):

    def test_entity_wrappers(self):
        io_expected = [
            # Special endpoint (broken support v5.0.0 - 5.1.x) managed by script
            (('get', '/tags/{id}/users'), ('users', 'users')),
            # Conventional endpoint: singular read
            (('get', '/services/{id}'), ('service', 'service')),
            # Conventional endpoint: singular update
            (('put', '/services/{id}'), ('service', 'service')),
            # Conventional endpoint: create new
            (('pOsT', '/services'), ('service', 'service')),
            # Conventional endpoint: multi-update
            (('PUT', '/incidents/{id}/alerts'), ('alerts', 'alerts')),
            # Conventional endpoint: list resources
            (('get', '/incidents/{id}/alerts'), ('alerts', 'alerts')),
            # Expanded endpoint support: different request/response wrappers
            (('put', '/incidents/{id}/merge'), ('source_incidents', 'incident')),
            # Expanded support: same wrapper for req/res and all methods
            (
                ('post', '/event_orchestrations'),
                ('orchestrations', 'orchestrations')
            ),
            (
                ('get', '/event_orchestrations'),
                ('orchestrations', 'orchestrations')
            ),
            # Disabled
            (('post', '/analytics/raw/incidents'), (None, None)),
        ]
        for ((method, path), rval) in io_expected:
            self.assertEqual(rval, pdpyras.entity_wrappers(method, path))

    def test_infer_entity_wrapper(self):
        io_expected = [
            (('get', '/users'), 'users'),
            (('PoSt', '/users'), 'user'),
            (('PUT', '/service/{id}'), 'service'),
            (('PUT', '/incidents/{id}/alerts'), 'alerts'),
        ]
        for (method_path, expected_wrapper) in io_expected:
            self.assertEqual(
                expected_wrapper,
                pdpyras.infer_entity_wrapper(*method_path),
            )

    def test_unwrap(self):
        # Response has unexpected type, raise:
        r = Response(200, json.dumps([]))
        self.assertRaises(pdpyras.PDServerError, pdpyras.unwrap, r, 'foo')
        # Response has unexpected structure, raise:
        r = Response(200, json.dumps({'foo_1': {'bar':1}, 'foo_2': 'bar2'}))
        self.assertRaises(pdpyras.PDServerError, pdpyras.unwrap, r, 'foo')
        # Response has the expected structure, return the wrapped entity:
        foo_entity = {'type':'foo_reference', 'id': 'PFOOBAR'}
        r = Response(200, json.dumps({'foo': foo_entity}))
        self.assertEqual(foo_entity, pdpyras.unwrap(r, 'foo'))
        # Disabled entity wrapping (wrapper=None), return body as-is
        self.assertEqual({'foo': foo_entity}, pdpyras.unwrap(r, None))

class FunctionDecoratorsTest(unittest.TestCase):
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

    def test_wrapped_entities(self):
        do_http_things = MagicMock()
        response = MagicMock()
        do_http_things.return_value = response
        session = pdpyras.APISession('some_key')
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
            pdpyras.wrapped_entities(do_http_things)(session,
                '/services/PTHINGY'),
            {'name': 'value'}
        )
        reset_mocks()

        # OK response, bad JSON: raise exception.
        response.ok = True
        do_http_things.__name__ = 'rput' # just for instance
        response.json.side_effect = [ValueError('Bad JSON!')]
        self.assertRaises(pdpyras.PDClientError,
            pdpyras.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # OK response, but the response isn't what we expected: exception.
        do_http_things.reset_mock()
        response.reset_mock()
        response.json = MagicMock()
        response.ok = True
        do_http_things.return_value = response
        do_http_things.__name__ = 'rput' # just for instance
        response.json.return_value = {'nope': 'nopenope'}
        self.assertRaises(pdpyras.PDHTTPError,
            pdpyras.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # Not OK response, raise
        response.reset_mock()
        response.ok = False
        do_http_things.__name__ = 'rput' # just for instance
        self.assertRaises(pdpyras.PDClientError,
            pdpyras.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # GET /<index>: use a different envelope name
        response.ok = True
        users_array = [{"type":"user","email":"user@example.com",
            "summary":"User McUserson"}]
        response.json.return_value = {'users': users_array}
        do_http_things.__name__ = 'rget'
        dummy_session.url = 'https://api.pagerduty.com'
        self.assertEqual(users_array,
            pdpyras.wrapped_entities(do_http_things)(dummy_session, '/users',
                query='user'))
        reset_mocks()

        # Test request body JSON envelope stuff in post/put
        # Response body validation
        do_http_things.__name__ = 'rpost'
        user_payload = {'email':'user@example.com', 'name':'User McUserson'}
        self.assertRaises(
            pdpyras.PDClientError,
            pdpyras.wrapped_entities(do_http_things),
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
            pdpyras.wrapped_entities(do_http_things)(dummy_session, '/users',
                json=user_payload)
        )
        do_http_things.assert_called_with(dummy_session, '/users',
            json={'user':user_payload})

        reset_mocks()
        # Test auto-envelope functionality for multi-update
        incidents = [{'id':'PABC123'}, {'id':'PDEF456'}]
        do_http_things.__name__ = 'rput'
        response.ok = True
        updated_incidents = copy.deepcopy(incidents)
        response.json.return_value = {'incidents': updated_incidents}
        self.assertEqual(
            updated_incidents,
            pdpyras.wrapped_entities(do_http_things)(dummy_session,
                '/incidents', json=incidents)
        )
        # The final value of the json parameter passed to the method (which goes
        # straight to put) should be the plural resource name
        self.assertEqual(
            do_http_things.mock_calls[0][2]['json'],
            {'incidents': incidents}
        )

class HelperFunctionsTest(unittest.TestCase):

    def test_plural_deplural(self):
        # forward
        for r_name in ('escalation_policies', 'services', 'log_entries'):
            self.assertEqual(
                r_name,
                pdpyras.plural_name(pdpyras.singular_name(r_name))
            )
        # reverse
        for o_name in ('escalation_policy', 'service', 'log_entry'):
            self.assertEqual(
                o_name,
                pdpyras.singular_name(pdpyras.plural_name(o_name))
            )

    def test_successful_response(self):
        self.assertRaises(pdpyras.PDClientError, pdpyras.successful_response,
            Response(400, json.dumps({})))
        self.assertRaises(pdpyras.PDServerError, pdpyras.successful_response,
            Response(500, json.dumps({})))

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

    def test_oauth_headers(self):
        secret = 'randomly generated lol'
        for authtype in 'oauth2', 'bearer':
            sess = pdpyras.APISession(secret, auth_type=authtype)
            self.assertEqual(
                sess.headers['Authorization'],
                "Bearer "+secret
            )

    def test_print_debug(self):
        sess = pdpyras.APISession('token')
        log = Mock()
        log.setLevel = Mock()
        log.addHandler = Mock()
        sess.log = log
        # Enable:
        sess.print_debug = True
        log.setLevel.assert_called_once_with(logging.DEBUG)
        self.assertEqual(1, len(log.addHandler.call_args_list))
        self.assertTrue(isinstance(
            log.addHandler.call_args_list[0][0][0],
            logging.StreamHandler
        ))
        # Disable:
        log.setLevel.reset_mock()
        log.removeHandler = Mock()
        sess.print_debug = False
        log.setLevel.assert_called_once_with(logging.NOTSET)
        self.assertEqual(1, len(log.removeHandler.call_args_list))
        self.assertTrue(isinstance(
            log.removeHandler.call_args_list[0][0][0],
            logging.StreamHandler
        ))
        # Setter called via constructor:
        sess = pdpyras.APISession('token', debug=True)
        self.assertTrue(isinstance(sess._debugHandler, logging.StreamHandler))
        # Setter should be idempotent:
        sess.print_debug = False
        sess.print_debug = False
        self.assertFalse(hasattr(sess, '_debugHandler'))
        sess.print_debug = True
        sess.print_debug = True
        self.assertTrue(hasattr(sess, '_debugHandler'))

    @patch.object(pdpyras.APISession, 'iter_all')
    def test_find(self, iter_all):
        sess = pdpyras.APISession('token')
        iter_all.return_value = iter([
            {'type':'user', 'name': 'Someone Else', 'email':'some1@me.me.me', 'f':1},
            {'type':'user', 'name': 'Space Person', 'email':'some1@me.me ', 'f':2},
            {'type':'user', 'name': 'Someone Personson', 'email':'some1@me.me', 'f':3},
            {'type':'user', 'name': 'Numeric Fields', 'email': 'test@example.com', 'f':5}
        ])
        self.assertEqual(
            'Someone Personson',
            sess.find('users', 'some1@me.me', attribute='email')['name']
        )
        iter_all.assert_called_with('users', params={'query':'some1@me.me'})
        self.assertEqual(
            'Numeric Fields',
            sess.find('users', 5, attribute='f')['name']
        )

    @patch.object(pdpyras.APISession, 'iter_cursor')
    @patch.object(pdpyras.APISession, 'get')
    def test_iter_all(self, get, iter_cursor):
        sess = pdpyras.APISession('token')
        sess.log = MagicMock()

        # Test: user uses iter_all on an endpoint that supports cursor-based
        # pagination, short-circuit to iter_cursor
        path = '/audit/records'
        cpath = pdpyras.canonical_path('https://api.pagerduty.com', path)
        self.assertTrue(cpath in pdpyras.CURSOR_BASED_PAGINATION_PATHS)
        iter_cursor.return_value = []
        self.assertEqual([], list(sess.iter_all('/audit/records')))
        iter_cursor.assert_called_once_with('/audit/records', params=None,
            page_size=None, item_hook=None)

        # Test: user tries to use iter_all on a singular resource, raise error:
        self.assertRaises(
            pdpyras.URLError,
            lambda p: list(sess.iter_all(p)),
            'users/PABC123'
        )
        # Test: user tries to use iter_all on an endpoint that doesn't actually
        # support pagination, raise error:
        self.assertRaises(
            pdpyras.URLError,
            lambda p: list(sess.iter_all(p)),
            '/analytics/raw/incidents/Q3R8ZN19Z8K083/responses'
        )

        # Generate a dummy page. This deliberately returns results 10 at a time
        # and not the limit property in order to verify we are not using the
        # response properties but rather the count of results to increment
        # the limit:
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
        # Follow-up to #103: add more odd parameters to the URL
        weirdurl='https://api.pagerduty.com/users?number=1&filters[]=foo'
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


    @patch.object(pdpyras.APISession, 'get')
    def test_iter_cursor(self, get):
        sess = pdpyras.APISession('token')
        sess.log = MagicMock()
        # Generate a dummy response dict
        page = lambda wrapper, results, cursor: json.dumps({
            wrapper: results,
            'next_cursor': cursor
        })
        # Test: user tries to use iter_cursor where it won't work, raise:
        self.assertRaises(
            pdpyras.URLError,
            lambda p: list(sess.iter_cursor(p)),
            'incidents', # Maybe some glorious day, but not as of this writing
        )

        # Test: cursor parameter exchange, stop iteration when records run out,
        # etc. This isn't what the schema of the audit records API actually
        # looks like apart from the entity wrapper, but that doesn't matter for
        # the purpose of this test.
        get.side_effect = [
            Response(200, page('records', [1, 2, 3], 2)),
            Response(200, page('records', [4, 5, 6], 5)),
            Response(200, page('records', [7, 8, 9], None))
        ]
        self.assertEqual(
            list(sess.iter_cursor('/audit/records')),
            list(range(1,10))
        )
        # It should send the next_cursor body parameter from the second to
        # last response as the cursor query parameter in the final request
        self.assertEqual(get.mock_calls[-1][2]['params']['cursor'], 5)

    @patch.object(pdpyras.APISession, 'rput')
    @patch.object(pdpyras.APISession, 'rpost')
    @patch.object(pdpyras.APISession, 'iter_all')
    def test_persist(self, iterator, creator, updater):
        user = {
            "name": "User McUserson",
            "email": "user@organization.com",
            "type": "user"
        }
        # Do not create if the user exists already (default)
        iterator.return_value = iter([user])
        sess = pdpyras.APISession('apiKey')
        sess.persist('users', 'email', user)
        creator.assert_not_called()
        # Call session.rpost to create if the user does not exist
        iterator.return_value = iter([])
        sess.persist('users', 'email', user)
        creator.assert_called_with('users', json=user)
        # Call session.rput to update an existing user if update is True
        iterator.return_value = iter([user])
        new_user = dict(user)
        new_user.update({
            'job_title': 'Testing the app',
            'self': 'https://api.pagerduty.com/users/PCWKOPZ'
        })
        sess.persist('users', 'email', new_user, update=True)
        updater.assert_called_with(new_user, json=new_user)
        # Call session.rput to update but w/no change so no API PUT request:
        updater.reset_mock()
        existing_user = dict(new_user)
        iterator.return_value = iter([existing_user])
        sess.persist('users', 'email', new_user, update=True)
        updater.assert_not_called()

    def test_postprocess(self):
        logger = MagicMock()

        # Test call count and API time
        response = Response(201, json.dumps({'key':'value'}), method='POST',
            url='https://api.pagerduty.com/users/PCWKOPZ/contact_methods')
        sess = pdpyras.APISession('apikey')
        sess.postprocess(response)

        self.assertEqual(
            1,
            sess.api_call_counts['POST /users/{id}/contact_methods']
        )
        self.assertEqual(
            1.5,
            sess.api_time['POST /users/{id}/contact_methods']
        )
        response = Response(200, json.dumps({'key':'value'}), method='GET',
            url='https://api.pagerduty.com/users/PCWKOPZ')
        sess.postprocess(response)
        self.assertEqual(1, sess.api_call_counts['GET /users/{id}'])
        self.assertEqual(1.5, sess.api_time['GET /users/{id}'])

        # Test logging
        response = Response(500, json.dumps({'key': 'value'}), method='GET',
            url='https://api.pagerduty.com/users/PCWKOPZ/contact_methods')
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

            # Test GET with one array-type parameter not suffixed with []
            request.return_value = Response(200, json.dumps({'users': [user]}))
            user_query = {'query': 'user@example.com', 'team_ids':['PCWKOPZ']}
            modified_user_query = copy.deepcopy(user_query)
            modified_user_query['team_ids[]'] = user_query['team_ids']
            del(modified_user_query['team_ids'])
            r = sess.get('/users', params=user_query)
            request.assert_called_once_with(
                'GET', 'https://api.pagerduty.com/users',
                headers=headers_get, params=modified_user_query, stream=False,
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

            # Test retry logic:
            with patch.object(pdpyras.time, 'sleep') as sleep:
                # Test getting a connection error and succeeding the final time.
                returns = [
                    pdpyras.HTTPError("D'oh!")
                ]*sess.max_network_attempts
                returns.append(Response(200, json.dumps({'user': user})))
                request.side_effect = returns
                with patch.object(sess, 'cooldown_factor') as cdf:
                    cdf.return_value = 2.0
                    r = sess.get('/users/P123456')
                    self.assertEqual(sess.max_network_attempts+1,
                        request.call_count)
                    self.assertEqual(sess.max_network_attempts, sleep.call_count)
                    self.assertEqual(sess.max_network_attempts, cdf.call_count)
                    self.assertTrue(r.ok)
                request.reset_mock()
                sleep.reset_mock()

                # Now test handling a non-transient error when the client
                # library itself hits odd issues that it can't handle, i.e.
                # network, and that the raised exception includes context:
                raises = [pdpyras.RequestException("D'oh!")]*(
                    sess.max_network_attempts+1)
                request.side_effect = raises
                try:
                    sess.get('/users')
                    self.assertTrue(False, msg='Exception not raised after ' \
                        'retry maximum count reached')
                except pdpyras.PDClientError as e:
                    self.assertEqual(e.__cause__, raises[-1])
                except Exception as e:
                    self.assertTrue(False, msg='Raised exception not of the ' \
                        f"expected class; was {e.__class__}")
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
                with patch.object(sess, 'cooldown_factor') as cdf:
                    cdf.return_value = 2.0
                    r = sess.get('/users/P123456')
                    self.assertEqual(200, r.status_code)
                    self.assertEqual(2, cdf.call_count)
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
        # Same as above but with a custom timestamp:
        sess = pdpyras.ChangeEventsAPISession('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [ Response(202, '{"id":"abc123"}') ]
        with patch.object(sess, 'parent', new=parent):
            custom_timestamp = '2023-06-26T00:00:00Z'
            ddk = sess.submit(
                'testing 123',
                'triggered.from.pdpyras',
                custom_details={"this":"that"},
                links=[{'href':'https://http.cat/502.jpg'}],
                timestamp=custom_timestamp,
            )
            self.assertEqual(
                parent.request.call_args[1]['json']['payload']['timestamp'],
                custom_timestamp
            )

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

    def test_try_decoding(self):
        # Most requests, especially endpoints that follow standard patterns, will
        # respond with valid JSON:
        r = Response(200, json.dumps({
            'service': {
                'type': 'service_reference',
                'id': 'POOPBUG',
                'summary': 'A rare ID obfuscation'
            }
        }))
        self.assertEqual(list(pdpyras.try_decoding(r).keys()), ['service'])
        # Deletion requests, or PUT /teams/{t_id}/users/{u_id}, will respond with an
        # empty string; json.loads will error out but try_decoding should return None:
        r = Response(204, '')
        self.assertEqual(pdpyras.try_decoding(r), None)
        # Invalid JSON:
        r = Response(500, '''<html><head>
<title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
</body></html>''')
        self.assertRaises(pdpyras.PDServerError, pdpyras.try_decoding, r)

def main():
    ap=argparse.ArgumentParser()
    unittest.main()

if __name__ == '__main__':
    main()
