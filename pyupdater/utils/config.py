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
from __future__ import unicode_literals

import logging
import os

from pyupdater import settings
from pyupdater.utils.exceptions import ConfigError
from pyupdater.utils.storage import Storage

log = logging.getLogger(__name__)


class Config(dict):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        # Make the first level values accessible by dot access
        # config = Config(my_name='JMSwag')
        # config.my_name
        self.__dict__ = self

        # Load default values into config dict
        self.__postinit__()

        # Used to configure this object for different uses
        # Use 1: The client will use this config to load the ClientConfig
        #              object in client_config.py
        # Use 2: Used to load the repo config a pass to the PackageHander &
        #             Uploader during initialization
        self.load_config = kwargs.get('load_config', False)
        self.client = kwargs.get('client', False)

        # We must be in a repo. Initialize the database!
        if self.client is False:
            self.db = Storage()
            # Load the repo configuration.
            if self.load_config is True:
                self._load_config()
        else:
            self.db = None

    def __postinit__(self):
        config_template = {
            # If left None "PyUpdater App" will be used
            'APP_NAME': settings.GENERIC_APP_NAME,

            # path to place client config
            'CLIENT_CONFIG_PATH': settings.DEFAULT_CLIENT_CONFIG,

            # Company/Your name
            'COMPANY_NAME': settings.GENERIC_APP_NAME,

            'PLUGIN_CONFIGS': {},

            # Support for patch updates
            'UPDATE_PATCHES': True,

            # Max retries for downloads
            'MAX_DOWNLOAD_RETRIES': 3,
            }
        self.update(config_template)

    def from_object(self, obj):
        """Updates the values from ClientConfig

        Args:

            obj (instance): ClientConfig instance with attributes to
                                    retrieve updates

        """
        if self.client is False:
            raise ConfigError('This object is not configured for client use')

        # We only car about "yelling" attributes
        for key in dir(obj):
            # :)
            if key.isupper():
                self[key] = getattr(obj, key)

    def _load_config(self):
        """Loads config from database (json file)

            Returns (obj): Config object
        """
        # Safe guard to keep from accessing a database that doesn't exist
        if self.db is None:
            raise ConfigError('This object is configured with no file access')

        config_data = self.db.load(settings.CONFIG_DB_KEY_APP_CONFIG)
        if config_data is None:
            config_data = {}

        for k, v in config_data.items():
            self[k] = v
        self.DATA_DIR = os.getcwd()

    def save_config(self):
        """Saves config file to pyupdater database

        Args:

            obj (obj): config object
        """
        # Safe guard to keep from accessing a database that doesn't exist
        if self.db is None:
            raise ConfigError('This object is configured with no file access')

        log.info('Saving Config')
        out = {}
        for k, v in self.items():
            if k.isupper():
                out[k] = v
        self.db.save(settings.CONFIG_DB_KEY_APP_CONFIG, out)
        log.info('Config saved')
        self._write_config_py()
        log.info('Wrote client config')

    def _write_config_py(self):
        """Writes client config to client_config.py

        """
        if self.db is None:
            keypack_data = None
        else:
            keypack_data = self.db.load(settings.CONFIG_DB_KEY_KEYPACK)

        if keypack_data is None:
            public_key = None
        else:
            public_key = keypack_data['client']['offline_public']

        filename = os.path.join(os.getcwd(), *self.CLIENT_CONFIG_PATH)
        attr_str_format = "\t{} = '{}'\n"
        attr_format = "\t{} = {}\n"

        log.debug('Writing client_config.py')
        with open(filename, 'w') as f:
            f.write('class ClientConfig(object):\n')
            if hasattr(self, 'APP_NAME'):
                log.debug('Adding APP_NAME to client_config.py')
                f.write(attr_str_format.format('APP_NAME', self.APP_NAME))
            if hasattr(self, 'COMPANY_NAME'):
                log.debug('Adding COMPANY_NAME to client_config.py')
                f.write(attr_str_format.format('COMPANY_NAME',
                                               self.COMPANY_NAME))
            if hasattr(self, 'UPDATE_URLS'):
                log.debug('Adding UPDATE_URLS to client_config.py')
                f.write(attr_format.format('UPDATE_URLS', self.UPDATE_URLS))
            if hasattr(self, 'PUBLIC_KEY'):
                log.debug('Adding PUBLIC_KEY to client_config.py')
                f.write(attr_str_format.format('PUBLIC_KEY', public_key))
            if hasattr(self, 'MAX_DOWNLOAD_RETRIES'):
                log.debug('Adding MAX_DOWNLOAD_RETRIES to client_config.py')
                f.write(attr_format.format('MAX_DOWNLOAD_RETRIES',
                                           self.MAX_DOWNLOAD_RETRIES))
