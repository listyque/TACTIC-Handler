# -*- coding: utf8 -*-

# Requires python-ntlm (http://code.google.com/p/python-ntlm/) package
from thlib.side.ntlm import HTTPNtlmAuthHandler
try:
    import urllib2
    import xmlrpclib
    from cookielib import CookieJar
    from urllib2 import Request, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, ProxyHandler, HTTPCookieProcessor, build_opener, install_opener, urlopen
    from urllib import unquote, splittype, splithost
except:
    import urllib as urllib2
    import xmlrpc.client as xmlrpclib
    from http.cookiejar import CookieJar
    from urllib.parse import unquote
    from urllib.parse import splithost
    from urllib.request import Request, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, ProxyHandler, HTTPCookieProcessor, build_opener, install_opener, urlopen

import base64

from thlib.environment import env_server


useAuthOnProxy = True

httpAuthName = "admin"
httpAuthPassword = "admin"
serverTopLevelURL = "http://my.server.com"


class UrllibTransport(xmlrpclib.Transport, object):
    def __init__(self):
        super(self.__class__, self).__init__(None)
        self.proxy = env_server.get_proxy()
        self.proxy_user = self.proxy['login']
        self.proxy_pass = self.proxy['pass']
        self.proxy_server = self.proxy['server']
        self.proxy_enabled = self.proxy['enabled']

    def update_proxy(self, proxy_dict=None):
        if proxy_dict:
            self.proxy = proxy_dict
        else:
            self.proxy = env_server.get_proxy()
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
            type, r_type = splittype(self.proxyurl)
            phost, XXX = splithost(r_type)

            if '@' in phost:
                user_pass, phost = phost.split('@', 1)
                if ':' in user_pass:
                    self.proxy_user, self.proxy_pass = user_pass.split(':', 1)
                    puser_pass = base64.encodestring(
                        '%s:%s' % (unquote(self.proxy_user), unquote(self.proxy_pass))).strip()

            proxies = {'http': 'http://%s' % phost, 'https': None}

        host = unquote(host)
        address = "http://%s%s" % (host, handler)

        request = Request(address, request_body)
        # request.add_data(request_body)
        request.add_header('User-agent', self.user_agent)
        request.add_header("Content-Type", "text/xml")

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
            request.add_header('Proxy-authorization', 'Basic ' + puser_pass)

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

        install_opener(opener)

        response = urlopen(request, timeout=env_server.get_timeout())
        return self.parse_response(response)
