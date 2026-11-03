# -*- coding: utf8 -*-

# Requires python-ntlm (http://code.google.com/p/python-ntlm/) package
from thlib.side.ntlm import HTTPNtlmAuthHandler
try:
    import urllib2
    import xmlrpclib
    from cookielib import CookieJar
    from urllib2 import Request, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, ProxyHandler, HTTPCookieProcessor, build_opener
    from urllib import unquote
    from urlparse import urlsplit
except:
    import urllib as urllib2
    import xmlrpc.client as xmlrpclib
    from http.cookiejar import CookieJar
    from urllib.parse import unquote, urlsplit
    from urllib.request import Request, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, ProxyHandler, HTTPCookieProcessor, build_opener

import base64

from thlib.environment import env_server


useAuthOnProxy = True

httpAuthName = "admin"
httpAuthPassword = "admin"
serverTopLevelURL = "http://my.server.com"


class UrllibTransport(xmlrpclib.Transport, object):
    def __init__(self):
        super(self.__class__, self).__init__(None)
        self.proxy = self._normalize_proxy(env_server.get_proxy())
        self.proxy_user = self.proxy['login']
        self.proxy_pass = self.proxy['pass']
        self.proxy_server = self.proxy['server']
        self.proxy_enabled = self.proxy['enabled']
        self._opener = None
        self._opener_key = None

    @staticmethod
    def _normalize_proxy(proxy_dict=None):
        values = dict(proxy_dict) if isinstance(proxy_dict, dict) else {}
        server = str(values.get('server') or '')
        return {
            'login': str(values.get('login') or ''),
            'pass': str(values.get('pass') or ''),
            'server': server,
            'enabled': bool(values.get('enabled') and server),
        }

    def update_proxy(self, proxy_dict=None):
        self.proxy = self._normalize_proxy(
            proxy_dict if proxy_dict is not None
            else env_server.get_proxy()
        )
        self.proxy_user = self.proxy['login']
        self.proxy_pass = self.proxy['pass']
        self.proxy_server = self.proxy['server']
        self.proxy_enabled = self.proxy['enabled']
        if not self.proxy_enabled:
            self.proxyurl = None

    def disable_proxy(self):
        self.proxy_enabled = False

    def enable_proxy(self):
        self.proxy_enabled = True

    def parse_response(self, response):
        # read response data from httpresponse, and parse it

        # Check for new http response object, else it is a file object
        if hasattr(response, 'getheader'):
            if response.getheader("Content-Encoding", "") == "gzip":
                stream = xmlrpclib.GzipDecodedResponse(response)
            else:
                stream = response
        else:
            stream = response

        p, u = self.getparser()

        while 1:
            data = stream.read(1024)
            if not data:
                break
            if self.verbose:
                print("body:", repr(data))
            p.feed(data)

        if stream is not response:
            stream.close()
        p.close()

        return u.close()

    def request(self, host, handler, request_body, verbose=0):
        self.verbose = verbose
        address = "http://%s%s" % (unquote(host), handler)
        request = Request(address, request_body)
        request.add_header('User-agent', self.user_agent)
        request.add_header("Content-Type", "text/xml")
        response = self.open(request, timeout=env_server.get_timeout())
        try:
            return self.parse_response(response)
        finally:
            response.close()

    def open(self, request, timeout=None):
        """Open RPC or repository requests with this transport's proxy settings."""
        if not isinstance(request, Request):
            request = Request(request)
        address = urlsplit(request.get_full_url())
        if self.proxy_enabled:
            if self.proxy_server.startswith('http://'):
                proxy_server = self.proxy_server[7:]
            else:
                proxy_server = self.proxy_server
            if useAuthOnProxy:
                self.proxyurl = 'http://{0}:{1}@{2}'.format(self.proxy_user, self.proxy_pass, proxy_server)
            else:
                self.proxyurl = proxy_server
        else:
            self.proxyurl = None

        puser_pass = None

        if self.proxyurl is not None:
            proxy_address = self.proxyurl if '://' in self.proxyurl else 'http://' + self.proxyurl
            phost = urlsplit(proxy_address).netloc

            if '@' in phost:
                user_pass, phost = phost.split('@', 1)
                if ':' in user_pass:
                    self.proxy_user, self.proxy_pass = user_pass.split(':', 1)
                    raw_user_pass = '%s:%s' % (unquote(self.proxy_user), unquote(self.proxy_pass))
                    puser_pass = base64.b64encode(raw_user_pass.encode('utf-8')).decode('ascii')

            proxies = {'http': 'http://%s' % phost, 'https': 'http://%s' % phost}

        key = (address.scheme, address.netloc, self.proxy_enabled,
               self.proxy_server, self.proxy_user, self.proxy_pass,
               useAuthOnProxy, httpAuthName, httpAuthPassword, serverTopLevelURL)
        if puser_pass:
            request.add_header('Proxy-authorization', 'Basic ' + puser_pass)
        if self._opener_key != key:
            # HTTP Auth
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            top_level_url = serverTopLevelURL
            password_mgr.add_password(None,
                                      top_level_url,
                                      httpAuthName,
                                      httpAuthPassword)
            handler = HTTPBasicAuthHandler(password_mgr)

            # Cookies
            cj = CookieJar()

            if puser_pass:
                # NTLM
                passman = HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, serverTopLevelURL, self.proxy_user, self.proxy_pass)

                authNTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)

                proxy_support = ProxyHandler(proxies)

                opener = build_opener(handler, proxy_support,
                                              HTTPCookieProcessor(cj),
                                              authNTLM)
            elif self.proxyurl:
                # Proxy without auth
                proxy_support = ProxyHandler(proxies)
                opener = build_opener(proxy_support,
                                              handler,
                                              HTTPCookieProcessor(cj))
            else:
                # Direct connection
                proxy_support = ProxyHandler({})
                opener = build_opener(proxy_support,
                                              handler,
                                              HTTPCookieProcessor(cj))

            self._opener = opener
            self._opener_key = key
        if timeout is None:
            timeout = env_server.get_timeout()
        return self._opener.open(request, timeout=timeout)
