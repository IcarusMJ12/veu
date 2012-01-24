import re
from datetime import datetime
from copy import deepcopy

__all__ = ['Country','Province','Countries','Provinces','the_beginning']

date_format = '%Y.%m.%d'
re_date_format = re.compile(r'^[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}$')
the_beginning=datetime(1,1,1)

class TimedDict(object):
    def __init__(self, d):
        self._d={the_beginning: deepcopy(d)}
        for key in self._d[the_beginning].keys():
            if re_date_format.match(key):
                v=self._d[the_beginning].pop(key)
                key=datetime.strptime(key,date_format)
                self._d[key]=v
            elif key.startswith('add_'):
                v=self._d[the_beginning].pop(key)
                key=key[4:]
                self._d[the_beginning][key]=set(v)
        self._keys=sorted(self._d.keys())
    
    @property
    def keys(self):
        return self._keys
    
    def __getitem__(self, key):
        if not isinstance(key, datetime):
            key=datetime.strptime(key, date_format)
        ret = deepcopy(self._d[the_beginning])
        for step in self._keys:
            if key<step:
                break
            d=self._d[step]
            for k,v in d.items():
                if k.startswith('add_'):
                    try:
                        ret[k[4:]].update(v)
                    except KeyError:
                        ret[k[4:]]=set(v)
                elif k.startswith('remove_'):
                    ret[k[7:]].difference_update(v)
                else:
                    ret[k]=deepcopy(v)
        return ret

class Country(TimedDict):
    def __init__(self, d, name, code):
        super(Country, self).__init__(d)
        self._d[the_beginning]['name']=name.title()
        self._d[the_beginning]['code']=code.upper()

        def filterOwnedProvinces(date, provinces):
            provinces_snapshot=[province[date] for province in provinces.values()]
            return [province for province in provinces_snapshot if province['owner']==self[date]['code']]
        
        def fetchStats(date, keywords, provinces=None):
            country_snapshot=self[date]
            if provinces is not None:
                for province in provinces:
                    for key, value in province.items():
                        try:
                            value=int(value)
                        except ValueError:
                            continue
                        try:
                            country_snapshot[key]+=value
                        except KeyError:
                            country_snapshot[key]=value
            result=[country_snapshot[keyword] for keyword in keywords]
    
class Province(TimedDict):
    def __init__(self, d, name, code):
        super(Province, self).__init__(d)
        self._d[the_beginning]['name']=name.title()
        self._d[the_beginning]['code']=int(code)

class Areas(dict):
    def __init__(self):
        self._codes_by_name={}
        super(Areas, self).__init__()
    
    def addItem(self, item):
        code=item[the_beginning]['code']
        self._codes_by_name[item[the_beginning]['name']]=code
        self[code]=item
    
    def __getitem__(self, key):
        try:
            return super(Areas, self).__getitem__(key)
        except KeyError:
            return super(Areas, self).__getitem__(self._codes_by_name[key])

class Countries(Areas):
    def addCountry(self, country):
        self.addItem(country)

class Provinces(Areas):
    def addProvince(self, province):
        self.addItem(province)
