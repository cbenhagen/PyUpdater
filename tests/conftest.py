# --------------------------------------------------------------------------
# Copyright (c) 2016 Digital Sapphire
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
# ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.
# --------------------------------------------------------------------------
import os
import tempfile
import threading

try:
    from http.server import SimpleHTTPRequestHandler as RequestHandler
except ImportError:
    from SimpleHTTPServer import SimpleHTTPRequestHandler as RequestHandler
try:
    import socketserver as socket_server
except:
    import SocketServer as socket_server

import pytest

from pyupdater import PyUpdater
from pyupdater.cli.options import make_parser
from pyupdater.client import Client
from pyupdater.key_handler.keys import Keys
from pyupdater.utils.config import Config
from pyupdater.utils.storage import Storage
from tconfig import TConfig


@pytest.fixture
def cleandir():
    newpath = tempfile.mkdtemp()
    os.chdir(newpath)


@pytest.fixture
def client():
    t_config = TConfig()
    t_config.DATA_DIR = os.getcwd()
    client = Client(t_config, refresh=True, test=True)
    client.FROZEN = True
    return client


@pytest.fixture
def create_keypack():
    keys = Keys(test=True)
    keys.make_keypack('test')


@pytest.fixture
def db():
    db = Storage()
    return db


@pytest.fixture
def loader():
    _CONFIG = {
        'APP_NAME': 'PyUpdater Test',
        'COMPANY_NAME': 'ACME',
        'UPDATE_PATCHES': True,
        }

    config = Config()
    config.update(_CONFIG)
    config.save_config()
    return config


@pytest.fixture
def parser():
    parser = make_parser()
    return parser


@pytest.fixture
def pyu():
    config = Config()
    test_config = TConfig()
    test_config.DATA_DIR = os.getcwd()
    config.from_object(test_config)
    pyu = PyUpdater(config)
    return pyu


@pytest.fixture
def simpleserver():
    class Server(object):
        def __init__(self):
            self._server = None

        def start(self, port=8000):
            socket_server.TCPServer.allow_reuse_address = True
            httpd = socket_server.TCPServer(("", port), RequestHandler)

            self._server = threading.Thread(target=httpd.serve_forever)
            self._server.daemon = True
            self._server.start()

        def stop(self):
            if self._server is not None:
                self._server.alive = False
                self._server = None
    return Server()
