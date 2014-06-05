"""
ProxyVor is a fast and simple "proxies" hunter & tester.

Homepage and documentation: http://proxyvor.org/

Copyright (c) 2014, diateam.
License: GPLv3 (see LICENSE for details)
"""
from __future__ import unicode_literals, with_statement
# -*- coding: utf-8 -*-

__author__ = 'diateam'
__version__ = '0.11.dev'
__license__ = 'GPLv3'

import json
import os
from bottle import route, run, request, abort, error, app
import uuid
import signal
from proxyvor import server, utils
import logging
import logging.config


signal.signal(signal.SIGINT, utils.signal_handler)
CONFIG_FILE = open('config.json')
CONFIG_DATA = None
try:
    with open('config.json') as config_file:
        try:
            CONFIG_DATA = json.load(CONFIG_FILE)
        except ValueError:
            print "Cannot parse config file"
            exit(1)
except IOError as io_error:
    print "IOError: {}".format(io_error)
    exit(1)

STORE_PATH = CONFIG_DATA.get('paths', {}).get('proxy_check')
HTTPS_CONFIG = CONFIG_DATA.get('https', {})
HTTPS_ENABLED = HTTPS_CONFIG.get('enabled', False)
CERTFILE = ""
KEYFILE = ""
PORT = CONFIG_DATA.get('port', 8080)
###############LOGGER config
LOGGER_CONFIG = CONFIG_DATA.get('logger')
if not LOGGER_CONFIG:
    print "You must specify a 'logger' key in the config file"
    exit(1)
logging.config.dictConfig(LOGGER_CONFIG)
LOGGER = logging.getLogger()


if HTTPS_ENABLED:
    try:
        with open(HTTPS_CONFIG.get('certfile', ''), 'r'), open(HTTPS_CONFIG.get('keyfile', ''), 'r'):
            CERTFILE = HTTPS_CONFIG.get('certfile', '')
            KEYFILE = HTTPS_CONFIG.get('keyfile', '')
    except IOError as io_error:
        LOGGER.warn("IOError: {}".format(io_error))


if not os.path.exists(STORE_PATH):
    os.makedirs(STORE_PATH)
TOKENS_DICT = {}


@error(404)
def error404(err):
    # pylint: disable=unused-argument
    """
    our own 404 page
    """
    LOGGER.warn(server.log_after_request())
    return 'Nothing here, sorry'


@error(405)
def error405(err):
    # pylint: disable=unused-argument
    """
    our own 405 page
    """
    LOGGER.warn(server.log_after_request())
    return 'Method not allowed'


@route('/')
def index():
    """
    basic index page
    """
    return "proxyvor-target"


@route('/<token>', method='GET')
def record_result(token="", real=False, proxy=False):
    """
    this is a route to call for recording a result
    if you call this one, the first result will be considered as the proxy one
    and the second one will be considered as the real one

    if token is incorrect(i.e: not in TOKENS_DICT, you'll get a 404)
    """
    if not token in TOKENS_DICT:
        abort(404)
    headers = {'http_headers': {}}
    headers['client_ip'] = request.remote_addr
    headers['client_remote_route'] = request.remote_route
    remote_addr = request.environ.get('REMOTE_ADDR')
    if remote_addr:
        headers['remote_addr'] = remote_addr
    for key in request.headers.keys():
        headers['http_headers'][key] = request.headers[key]
    json_string = ""
    try:
        json_string = json.dumps({'method': request.method, 'headers': headers},
                                 sort_keys=True, indent=4, separators=(',', ': '))
    except TypeError:
        LOGGER.warn("Can not dump token as json: {}".format(token))

    # The first GET will be recorded as proxy and the second as real
    # All others will be ignored
    if not real and not proxy:
        if len(TOKENS_DICT[token]) == 0:
            TOKENS_DICT[token]['proxy'] = headers
        elif len(TOKENS_DICT[token]) == 1:
            TOKENS_DICT[token]['real'] = headers
        else:
            pass
    elif real and not proxy:
        TOKENS_DICT[token]['real'] = headers
    elif proxy and not real:
        TOKENS_DICT[token]['proxy'] = headers
    else:
        pass

    return "<pre>%s</pre>" % json_string


@route('/r/<token>', method='GET')
def real_connection_record_result(token=""):
    """
    use this route for storing a real result
    """
    return record_result(token, real=True)


@route('/p/<token>', method='GET')
def proxified_connection_record_result(token=""):
    # pylint: disable=invalid-name
    """
    use this route for storing a proxy result
    """
    return record_result(token, proxy=True)


@route('/proxy_checks', method='GET')
@route('/proxy_checks/', method='GET')
def list_tokens():
    """
    use this route for listing all the tokens
    """
    return {"success": True, "tokens": TOKENS_DICT.keys()}


@route('/proxy_checks/<token>', method='GET')
def get_token_results(token=""):
    """
    use this route to get the results of a token
    """
    if token in TOKENS_DICT.keys():
        return TOKENS_DICT.get(token, {})
    else:
        abort(404)


@route('/proxy_checks/<token>', method='DELETE')
def delete_token(token=""):
    """
    use this route to delete a token
    """
    if token in TOKENS_DICT.keys():
        del TOKENS_DICT[token]
        try:
            os.remove(os.path.join(STORE_PATH, token))
        except OSError:
            pass
        return {"success": True}
    else:
        return {"success": False}


@route('/proxy_checks/create', method='PUT')
def proxy_check_new():
    """
    use this route to create a token
    """
    proxy_check_token = str(uuid.uuid4())
    # filepath = os.path.join(STORE_PATH, proxy_check_token)
    if not proxy_check_token in TOKENS_DICT.keys():
        TOKENS_DICT[proxy_check_token] = {}
        LOGGER.info('Created token: {0}'.format(proxy_check_token))
        return {"success": True, "token": proxy_check_token}
    else:
        return {"success": False, "token": ""}


if __name__ == '__main__':
    PROXYVOR_APP = server.ProxyvorApplication(app())

    try:
        TOKENS_DICT = utils.read_tokens_on_start(STORE_PATH)
        run(host='0.0.0.0',
            port=PORT,
            debug=True,
            server=server.ProxyvorCherryPyServer,
            app=PROXYVOR_APP,
            keyfile=KEYFILE,
            certfile=CERTFILE)
    except SystemExit:
        utils.save_on_disk(TOKENS_DICT, STORE_PATH)
