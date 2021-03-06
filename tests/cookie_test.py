#encoding: utf-8

import sys
import unittest

import hmac
try:
    from hashlib import sha1
except ImportError:
    import sha as sha1

from pyroutes.http.cookies import *
from pyroutes import settings

if sys.version_info >= (3,):
    from imp import reload

TEST_KEY = u'asdfnaj2308sydfahli37flas36al9gaiufw'.encode('ascii')
TEST_VALUE = u'foobar'.encode('ascii')

class TestRequestCookieHandler(unittest.TestCase):

    def setUp(self):
        settings.SECRET_KEY = TEST_KEY
        self.env = {'HTTP_COOKIE': (
                'foo=bar;foo_hash=%s;bar=foo;baz=b;baz_hash=b' %
                hmac.HMAC(settings.SECRET_KEY, TEST_VALUE, sha1).hexdigest()
                )}
        self.cookie_request_handler = RequestCookieHandler(self.env)

    def test_init(self):
        cookie_request_handler = RequestCookieHandler(self.env)
        self.assertTrue(cookie_request_handler._raw_cookies)
        cookie_request_handler = RequestCookieHandler(None)
        self.assertFalse(cookie_request_handler._raw_cookies)

    def test_get_cookie(self):
        self.assertEqual(self.cookie_request_handler.get_cookie('foo'), 'bar')

    def test_get_cookie_without_hash(self):
        self.assertRaises(CookieHashMissing, self.cookie_request_handler.get_cookie, 'bar')

    def test_get_cookie_with_invalid_hash(self):
        self.assertRaises(CookieHashInvalid, self.cookie_request_handler.get_cookie, 'baz')

    def test_get_not_existing_cookie(self):
        self.assertEqual(self.cookie_request_handler.get_cookie('test'), None)

    def test_get_unsigned_cookie(self):
        self.assertEqual(self.cookie_request_handler.get_unsigned_cookie('foo'), 'bar')

    def test_get_non_existing_unsigned_cookie(self):
        self.assertEqual(self.cookie_request_handler.get_unsigned_cookie('test'), None)

    def test_get_cookie_without_key_setting(self):
        reload(settings)
        self.assertRaises(CookieKeyMissing, self.cookie_request_handler.get_cookie, 'foo')
        settings.SECRET_KEY = TEST_KEY

class TestResponseCookieHandler(unittest.TestCase):

    def setUp(self):
        settings.SECRET_KEY = TEST_KEY
        settings.SITE_ROOT = ''
        self.cookies = ResponseCookieHandler()

    def test_add_cookie(self):
        self.cookies.add_cookie('foo', 'bar')
        cookie_hash = hmac.HMAC(settings.SECRET_KEY, TEST_VALUE, sha1).hexdigest()
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; path=/'))
        self.assertEqual(self.cookies.cookie_headers[1], ('Set-Cookie', 'foo_hash=%s; path=/' % cookie_hash))

    def test_add_unsigned_cookie(self):
        self.cookies.add_unsigned_cookie('foo', 'bar')
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; path=/'))

    def test_add_cookie_without_path(self):
        self.cookies.add_unsigned_cookie('foo', 'bar', path=False)
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar'))

    def test_add_cookie_default_path(self):
        settings.SITE_ROOT = '/baz/'
        self.cookies.add_unsigned_cookie('foo', 'bar')
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; path=/baz/'))
        settings.SITE_ROOT = ''

    def test_add_cookie_without_nondefault_path(self):
        self.cookies.add_unsigned_cookie('foo', 'bar', path='/foo')
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; path=/foo'))

    def test_add_cookie_with_expires(self):
        import datetime
        exp = datetime.datetime(2000,1,1,1,1,1)
        exp_string = exp.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        self.cookies.add_cookie('foo', 'bar', exp)
        cookie_hash = hmac.HMAC(settings.SECRET_KEY, TEST_VALUE, sha1).hexdigest()
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; expires=%s; path=/' % exp_string))
        self.assertEqual(self.cookies.cookie_headers[1], ('Set-Cookie', 'foo_hash=%s; expires=%s; path=/' % (cookie_hash, exp_string)))

    def test_add_unsigned_cookie_with_expires(self):
        import datetime
        exp = datetime.datetime(2000,1,1,1,1,1)
        exp_string = exp.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        self.cookies.add_unsigned_cookie('foo', 'bar', exp)
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=bar; expires=%s; path=/' % exp_string))
    def test_del_cookie(self):
        self.cookies.del_cookie('foo')
        self.assertEqual(self.cookies.cookie_headers[0], ('Set-Cookie', 'foo=null; expires=Thu, 01-Jan-1970 00:00:01 GMT'))
        self.assertEqual(self.cookies.cookie_headers[1], ('Set-Cookie', 'foo_hash=null; expires=Thu, 01-Jan-1970 00:00:01 GMT'))

    def test_no_SECRET_KEY(self):
        key = settings.SECRET_KEY
        handler = ResponseCookieHandler()
        settings.SECRET_KEY = None
        self.assertRaises(CookieKeyMissing, handler.add_cookie, 'foo', 'bar')
        settings.SECRET_KEY = key
