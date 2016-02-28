from glob import iglob
from os.path import join, split, basename

from config import common_path
from nom import nom

__all__ = [ 'cultures', 'culture_map' ]

def _load_cultures():
    with open(join(common_path, '00_cultures.txt'), 'r') as f:
        return nom(f.read())

def _culture_map(cultures):
    culture_map = {}
    redundant_keys = set()

    for culture_group, stuff in cultures.iteritems():
        for key in stuff.keys():
            if key not in culture_map:
                culture_map[key] = culture_group
                continue

            redundant_keys.add(key)

    for key in redundant_keys:
        del culture_map[key]

    return culture_map

cultures = _load_cultures()
culture_map = _culture_map(cultures)
