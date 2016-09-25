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
from __future__ import print_function, unicode_literals
import io
import json
import logging
import os

try:
    from UserDict import DictMixin as dictmixin
except ImportError:
    from collections import MutableMapping as dictmixin


import six

from pyupdater import settings

log = logging.getLogger(__name__)


class JSONStore(dictmixin):

    def __init__(self, path, json_kw=None):
        """Create a JSONStore object backed by the file at `path`.
        If a dict is passed in as `json_kw`, it will be used as keyword
        arguments to the json module.
        """
        self.path = path
        self.json_kw = json_kw or {}

        self._data = {}

        self._synced_json_kw = None
        self._needs_sync = False
        self._data_from_disk_loaded = False

    def _load_data_from_disk(self):
        self._data_from_disk_loaded = True
        try:
            # load the whole store
            with io.open(self.path, 'r', encoding='utf-8') as fp:
                self.update(json.load(fp))
        except Exception as err:
            log.warning(err)
            log.debug(err, exc_info=True)

    def __str__(self):
        return str(self._data)

    def __getitem__(self, key):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        return self._data[key]

    def __setitem__(self, key, value):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        self._data[key] = value
        self._needs_sync = True

    def __delitem__(self, key):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        del self._data[key]
        self._needs_sync = True

    def __len__(self):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        return len(self._data)

    def __iter__(self):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        i = []
        for k, v in self._data.items():
            i.append((k, v))
        return iter(i)

    def _sanatize(self, data):
        _data = {}
        for k, v in data.items():
            if hasattr(v, '__call__') is True:
                continue
            if isinstance(v, JSONStore) is True:
                continue
            if k in ['__weakref__', '__module__', '__dict__', '__doc__']:
                continue
            _data[k] = v
        return _data

    def copy(self):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        return self._data.copy()

    def keys(self):
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()
        return self._data.keys()

    def sync(self, json_kw=None, force=False):
        """Atomically write the entire store to disk if it's changed.
        If a dict is passed in as `json_kw`, it will be used as keyword
        arguments to the json module.
        If force is set True, a new file will be written even if the store
        hasn't changed since last sync.
        """
        if self._data_from_disk_loaded is False:
            self._load_data_from_disk()

        json_kw = json_kw or self.json_kw
        if self._synced_json_kw != json_kw:
            self._needs_sync = True

        if not (self._needs_sync or force):
            return False

        data = self._sanatize(self._data)
        with io.open(self.path, 'w', encoding='utf-8') as json_file:
            data = json.dumps(data, ensure_ascii=False, indent=2)
            if six.PY2:
                # unicode(data) auto-decodes data to unicode if str
                data = unicode(data)
            json_file.write(data)

        self._synced_json_kw = json_kw
        self._needs_sync = False
        return True


# Used by KeyHandler, PackageHandler & Config to
# store data in a json file
class Storage(object):

    def __init__(self, refresh=True):
        """Loads & saves config file to file-system.

            Args:

                config_dir (str): Path to directory where config will be stored
        """
        self.config_dir = os.path.join(os.getcwd(),
                                       settings.CONFIG_DATA_FOLDER)
        if not os.path.exists(self.config_dir):
            log.info('Creating config dir')
            os.mkdir(self.config_dir)
        log.debug('Config Dir: %s', self.config_dir)
        self.filename = os.path.join(self.config_dir,
                                     settings.CONFIG_FILE_USER)
        log.debug('Config DB: %s', self.filename)
        self.db = JSONStore(self.filename)
        self._loaded_db = False
        if refresh is True:
            self._loaded_db = True
            self._load_db()

    def __getattr__(self, name):
        return self.__class__.__dict__.get(name)

    def __setattr__(self, name, value):
        setattr(self.__class__, name, value)

    def __delattr__(self, name):
        raise AttributeError('Cannot delete attributes!')

    def __getitem__(self, name):
        try:
            return self.__class__.__dict__[name]
        except KeyError:
            return self.__dict__[name]

    def __setitem__(self, name, value):
        setattr(Storage, name, value)

    def _load_db(self):
        "Loads database into memory."
        for k, v in self.db:
            setattr(Storage, k, v)

    def save(self, key, value):
        """Saves key & value to database

        Args:

            key (str): used to retrieve value from database

            value (obj): python object to store in database

        """
        if self._loaded_db is False:
            self._load_db()

        setattr(Storage, key, value)
        for k, v in Storage.__dict__.items():
            self.db[k] = v
        log.debug('Syncing db to filesystem')
        self.db.sync()

    def load(self, key):
        """Loads value for given key

            Args:

                key (str): The key associated with the value you want
                form the database.

            Returns:

                Object if exists or else None
        """
        if self._loaded_db is False:
            self._load_db()

        return self.__class__.__dict__.get(key)
