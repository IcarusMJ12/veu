from datetime import datetime
from copy import deepcopy
import re

date_format = '%Y.%m.%d'
re_date_format = re.compile(r'^[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}$')
THE_BEGINNING = datetime(1, 1, 1)
DEFAULT_DATE = datetime(1399, 10, 14)

class TimedDict(object):
    def __init__(self, d):
        self._d = {THE_BEGINNING: deepcopy(d)}
        for key in self._d[THE_BEGINNING].keys():
            if re_date_format.match(key):
                v = self._d[THE_BEGINNING].pop(key)
                if isinstance(v, list):
                    new_v = {}
                    for item in v:
                        new_v.update(item)
                    v = new_v
                key = datetime.strptime(key, date_format)
                self._d[key] = v
            elif key.startswith('add_'):
                v = self._d[THE_BEGINNING].pop(key)
                key = key[4:]
                self._d[THE_BEGINNING][key] = set(v)
        self._keys = sorted(self._d.keys())

    @property
    def keys(self):
        return self._keys

    def __getitem__(self, key):
        if key == '':
            key = DEFAULT_DATE
        if not isinstance(key, datetime):
            key = datetime.strptime(key, date_format)
        ret = deepcopy(self._d[THE_BEGINNING])
        for step in self._keys:
            if key < step:
                break
            d = self._d[step]
            for k, v in d.items():
                if k.startswith('add_'):
                    try:
                        ret[k[4:]].update(v)
                    except KeyError:
                        ret[k[4:]] = set(v)
                elif k.startswith('remove_'):
                    ret[k[7:]].difference_update(v)
                else:
                    ret[k] = deepcopy(v)
        return ret
