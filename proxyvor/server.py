"""
server configuration
"""
from bottle import request, response, ServerAdapter

from cherrypy.wsgiserver import CherryPyWSGIServer
from cherrypy.wsgiserver.ssl_pyopenssl import pyOpenSSLAdapter
# import cherrypy
import OpenSSL.SSL as ssl
import logging

LOGGER = logging.getLogger()


def log_after_request():
    """
    log the request on stdout
    """
    try:
        length = response.content_length
    except ValueError:
        try:
            length = len(response.body)
        except TypeError:
            length = '???'
    to_log = '{ip} - "{method} {uri} {protocol}" {status} {length}'.format(
        ip=request.environ.get('REMOTE_ADDR'),
        #time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        method=request.environ.get('REQUEST_METHOD'),
        uri=request.environ.get('REQUEST_URI'),
        protocol=request.environ.get('SERVER_PROTOCOL'),
        status=response.status_code,
        length=length,
    )
    LOGGER.debug(to_log)
    return to_log


class ProxyvorApplication(object):
    # pylint: disable=too-few-public-methods
    """
    our wsgi application, it is very basic.
    It allows us to have the same console log when usig cherrypy server than when
    using the default one
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, host):
        # call bottle and store the return value
        ret_val = self.app(environ, host)

        # log the request
        log_after_request()

        # return bottle's return value
        return ret_val


class ProxyvorCherryPyServer(ServerAdapter):
    # pylint: disable=too-few-public-methods
    """
    our own server, derived from the cherrypy one
    we do this in order to have full control on ssl configuration
    """
    def run(self, handler):
        self.options['bind_addr'] = (self.host, self.port)
        self.options['wsgi_app'] = handler

        certfile = self.options.get('certfile')
        if certfile or 'certfile' in self.options:
            del self.options['certfile']
        keyfile = self.options.get('keyfile')
        if keyfile or 'keyfile' in self.options:
            del self.options['keyfile']

        server = CherryPyWSGIServer(**self.options)
        if keyfile and certfile:
            LOGGER.info("Start using HTTPS")
            server.ssl_adapter = pyOpenSSLAdapter(certfile, keyfile, None)
            context = ssl.Context(ssl.SSLv23_METHOD)
            context.set_cipher_list('HIGH')
            context.use_privatekey_file(keyfile)
            context.use_certificate_file(certfile)
            server.ssl_adapter.context = context
        else:
            LOGGER.info("Start using HTTP")

        try:
            server.start()
        finally:
            server.stop()
