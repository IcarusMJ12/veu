from glob import iglob
from os.path import join, split, basename

from eu4.config import common_path
from lib.nom import nom

__all__ = [ 'cultures', 'culture_map' ]

def _load(*args):
    with open(join(common_path, *args), 'r') as f:
        return nom(f.read())

def _reverse_map(dictionary):
    result = {}
    redundant_keys = set()

    for group, stuff in dictionary.iteritems():
        for key in stuff.keys():
            if key not in result:
                result[key] = group
                continue

            redundant_keys.add(key)

    for key in redundant_keys:
        del result[key]

    return result

cultures = _load('cultures', '00_cultures.txt')
culture_map = _reverse_map(cultures)
religions = _load('religions', '00_religion.txt')
religion_map = _reverse_map(religions)
governments = _load('governments', '00_governments.txt')
