from glob import iglob
from os.path import join, split, basename

from config import history_path
from nom import nom
from memoize import pickled

__all__ = [ 'countries', 'provinces' ]

@pickled
def _load_countries():
    countries = {}

    for fn in iglob(join(history_path, 'countries/*.txt')):
        data = None
        with open(fn, 'r') as f:
            data = nom(f.read())
            tag = basename(fn.split('-')[0].strip().lower())
            countries[tag] = data

    return countries

@pickled
def _load_provinces():
    provinces = {}

    for fn in iglob(join(history_path, 'provinces/*.txt')):
        data = None
        with open(fn, 'r') as f:
            data = nom(f.read())
        if 'owner' in data.keys():
            data['owner'] = data['owner'].lower()
        fn = split(fn)[1]
        province_id = int(basename(fn.split('-')[0].strip().split(' ')[0].strip()))
        provinces[province_id] = data

    return provinces

countries = _load_countries()
provinces = _load_provinces()
