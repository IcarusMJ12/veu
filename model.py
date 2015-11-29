# Copyright (c) 2012 Igor Kaplounenko
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a
# copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from nom import nom
import glob
from os import path as os_path
from os.path import basename, splitext

from timed_dict import TimedDict

__all__ = ['Country', 'Province', 'Countries', 'Provinces', 'EUData']

class Country(TimedDict):

    def __init__(self, d, name, code):
        super(Country, self).__init__(d)
        self._d[THE_BEGINNING]['name'] = name.title()
        self._d[THE_BEGINNING]['code'] = code.upper()

        def filterOwnedProvinces(date, provinces):
            provinces_snapshot = [province[date]
                                  for province in provinces.values()]
            return [province for province in provinces_snapshot if province['owner'] == self[date]['code']]

        def fetchStats(date, keywords, provinces=None):
            country_snapshot = self[date]
            if provinces is not None:
                for province in provinces:
                    for key, value in province.items():
                        try:
                            value = int(value)
                        except ValueError:
                            continue
                        try:
                            country_snapshot[key] += value
                        except KeyError:
                            country_snapshot[key] = value
            result = [country_snapshot[keyword] for keyword in keywords]


class Province(TimedDict):

    def __init__(self, d, name, code):
        super(Province, self).__init__(d)
        self._d[THE_BEGINNING]['name'] = name.title()
        self._d[THE_BEGINNING]['code'] = int(code)


class Areas(dict):

    def __init__(self):
        self._codes_by_name = {}
        super(Areas, self).__init__()

    def addItem(self, item):
        code = item[THE_BEGINNING]['code']
        self._codes_by_name[item[THE_BEGINNING]['name']] = code
        self[code] = item

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


class EUData(object):

    def __init__(self, eu3_data_path):
        path = eu3_data_path
        self.path = path
        self.provinces = Provinces()
        self.countries = Countries()
        self._loadProvinces()
        self._loadCountries()

    def _areaFiles(self, relative_path):
        for filename in glob.iglob(os_path.join(self.path, relative_path)):
            with open(filename, 'r') as f:
                code_and_name = basename(filename).split('-')
                code = code_and_name[0].strip()
                name = splitext('-'.join(code_and_name[1:]).strip())[0]
                yield f, code, name

    def _loadProvinces(self):
        for f, code, name in self._areaFiles('history/provinces/*.txt'):
            self.provinces.addProvince(Province(nom(f.read()), name, code))

    def _loadCountries(self):
        for f, code, name in self._areaFiles('history/countries/*.txt'):
            self.countries.addCountry(Country(nom(f.read()), name, code))
