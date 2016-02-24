from eu_map import provinces, terrain_bmp, terrain_txt, definition

__all__ = ['color_map', 'terrain_overrides', 'province_terrain']

from memoize import pickled

@pickled
def _load_map():
    color_map = {}
    terrain = terrain_txt['terrain']

    for t in terrain:
        mapping = t[1]
        color_map[int(mapping['color'][0])] = mapping['type']

    return color_map

@pickled
def _load_terrain():
    result = {}
    
    # find all colors per province
    for x in xrange(terrain_bmp.size[0]):
        for y in xrange(terrain_bmp.size[1]):
            province_color = provinces.getpixel( (x, y) )
            province_key = definition[province_color]
            if province_key in _terrain_overrides_keys:
                continue

            terrain = terrain_bmp.getpixel( (x, y) )
            if terrain in (5, 8, 10, 11, 12, 13, 14, 15, 17, 18):
                continue

            terrain = color_map[terrain]

            try:
                province_map = result[province_key]
            except KeyError:
                result[province_key] = {}
                province_map = result[province_key]

            try:
                province_map[terrain] += 1
            except KeyError:
                province_map[terrain] = 1

    # find the most common color per province
    for province_key in result.keys():
        inverted = dict((v, k) for k, v in result[province_key].iteritems())
        result[province_key] = inverted[max(inverted)]

    return result

@pickled
def _load_terrain_overrides():
    result = {}

    categories = terrain_txt['categories']

    for k, v in categories.iteritems():
        if v is None:
            continue
        if 'terrain_override' not in v.keys():
            continue
        for province_id in v['terrain_override']:
            result[int(province_id)] = k

    # zurich (1869) is hills for some reason
    result[1869] = 'hills'
    
    return result


color_map = _load_map()
terrain_overrides = _load_terrain_overrides()
_terrain_overrides_keys = set(terrain_overrides.keys())
province_terrain = _load_terrain()
