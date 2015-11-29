#!/usr/bin/env python

import glob
from os import path
from decimal import Decimal
from PIL import Image

from nom import nom
from config import base_path, common_path

class Countries(object):
    COST_PER_DEV = 0.5
    EXTRA_COSTS = {
        'sound_toll': 20,
        'bosphorous_sound_toll': 10,
        'center_of_trade': 15,
        'estuary': 10,
    }
    HRE_CAPITAL_COST = 20
    HRE_CAPITAL_MULT = 1.2
    TERRAIN_MULTIPLIERS = {
        'glacier': 0.75,
        'farmlands': 1.1,
        'forest': 0.9,
        'hills': 0.85,
        'woods': 0.9,
        'mountain': 0.75,
        'grasslands': 1.0,
        'jungle': 0.8,
        'marsh': 0.85,
        'desert': 0.8,
        'coastal_desert': 0.9,
        'coastline': 0.95,
        'drylands': 0.95,
        'highlands': 0.9,
        'savannah': 0.95,
        'steppe': 0.95,
    }
    GOLD_MULTIPLIER = 3
    GOVT_COSTS = {
        'despotic_monarchy': 0,
        'feudal_monarchy': 0,
        'merchant_republic': 40,
        'oligarchic_republic': 0,
        'noble_republic': 10,
        'theocracy': 0,
        'steppe_horde': 0,
        'tribal_despotism': 0,
        'tribal_kingdom': 0,
        'tribal_federation': 0,
        'tribal_democracy': 0,
        'native_council': 0,
        'elective_monarchy': 10,
        'ambrosian_republic': 10,
        'dutch_republic': 40,
        'iqta': 10,
        'daiymo': 0,
        'shogunate': 50,
    }

    TECH_GROUPS = {
        'europe': 'western',
        'africa':  'muslim',
        'asia': 'muslim',
        'north_america': 'mesoamerican',
        'south_america': 'south_american',
        'oceania': 'south_american',
    }

    @staticmethod
    def _get_ruler_cost(self, a, d, m, age):
        return (a + d + m - 6) * 60/age

    @staticmethod
    def _get_heir_cost(self, a, d, m, age):
        return (a + d + m - 6) * 60/(age + 15)

    def __init__(self):
        self._terrain_image = Image.open(
            path.join(base_path, 'map/terrain.bmp'), 'r'
        )
        self._terrain = {}
        self._capitals = {}
        self._owners = {}
        self._province_base_costs = {}

        self._load_terrain()
        self._load_countries()
        self._load_provinces()

    def _load_terrain(self):
        TEST_TERRAIN = {
            # Lolland
            1983: 'coastline',
            # Western Isles
            253: 'coastline',
            # Girona
            212: 'grasslands',
            # Zurich
            1869: 'hills',
            # Savoie
            205: 'mountain',
        }

        data = None
        color_map = {}

        with open(path.join(base_path, 'map/terrain.txt'), 'r') as f:
            data = f.read()
        data = nom(data)
        terrain = data['terrain']
        categories = data['categories']
        with open(path.join(base_path, 'map/positions.txt'), 'r') as f:
            data = f.read()
        positions = nom(data)

        for t in terrain:
            mapping = t[1]
            color_map[int(mapping['color'][0])] = mapping['type']
        
        height = self._terrain_image.size[1]
        for k, v in positions.iteritems():
            # standing unit location -- may be wrong
            x, y = float(v['position'][2]), float(v['position'][3]) 
            try:
                self._terrain[int(k)] = color_map[
                    self._terrain_image.getpixel( (x, height - y) )
                ]
            except IndexError:
                pass
            if int(k) in TEST_TERRAIN.keys():
                print k, TEST_TERRAIN[int(k)],
                for i in (0, 2, 4, 10):
                    x, y = float(v['position'][i]), float(v['position'][i+1]) 
                    print color_map[self._terrain_image.getpixel((x, height - y))],
                print ''

        for k, v in categories.iteritems():
            if v is None:
                continue
            if 'terrain_override' not in v.keys():
                continue
            for province_id in v['terrain_override']:
                self._terrain[int(province_id)] = k

    def _load_countries(self):
        for fn in glob.iglob(path.join(base_path, 'history/countries/*.txt')):
            data = None
            with open(fn, 'r') as f:
                data = f.read()
            self._load_country(fn, nom(data))

    def _load_country(self, fn, data):
        tag = fn.split('-')[0].strip()
        try:
            self._capitals[tag] = data['capital']
        except KeyError:
            pass

    def _load_provinces(self):
        for fn in glob.iglob(path.join(base_path, 'history/provinces/*.txt')):
            data = None
            with open(fn, 'r') as f:
                data = f.read()
            self._load_province(fn, nom(data))

    def _load_province(self, fn, data):
        if 'owner' not in data.keys():
            return
        owner = data['owner']
        fn = path.split(fn)[1]
        province_id = int(fn.split('-')[0].strip())
        try:
            self._owners[owner].append(province_id)
        except KeyError:
            self._owners[owner] = [province_id,]
        try:
            cost = (
                int(data['base_tax']) +
                int(data['base_production']) +
                int(data['base_manpower'])
            ) * 0.5 * self.TERRAIN_MULTIPLIERS[self._terrain[province_id]]
        except KeyError:
            print owner, fn, self._terrain[province_id]
            cost = 0
        if data['trade_goods'] == 'gold':
            cost += self.GOLD_MULTIPLIER * int(data['base_production'])
        if 'extra_cost' in data.keys():
            cost += int(data['extra_cost'])
        self._province_base_costs[province_id] = cost

class Ideas(object):
    IDEA_COST_DEFAULTS = {
        3: {
            0: -3, 1: 0, 2: 3, 3: 9, 4: 18, 5: 30,
            6: 45, 7: 63, 8: 84, 9: 108, 10: 135,
        },
        5: {
            0: -5, 1: 0, 2: 5, 3: 15, 4: 30, 5: 50,
            6: 75, 7: 105, 8: 140, 9: 180, 10: 225,
        },
        15: {
            0: -15, 1: 0, 2: 15, 3: 50, 4: 105,
        },
        18: {
            0: 0, 1: 3, 2: 18, 3: 45, 4: 84,
        },
        30: {
            0: 0, 1: 5, 2: 30, 3: 75,
        },
        50: {
            0: 0, 1: 15, 2: 50, 3: 105,
        },
        140: {
            0: 0, 1: 30, 2: 140, 3: 330,
        },
    }
    # starting, then 7, then 1 last bonus
    IDEA_COST_PROGRESSION = ( 2.0, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 1.0, 1.0, )

    # we perform linear interpolation when returning results because we are
    # trying to be less-than-generous
    def get_cost(self, idea, level):
        defaults = self.IDEA_COST_DEFAULTS[idea[2] if 2 in idea else 5]
        int_level = int(level)
        try:
            cost = idea[int_level]
        except KeyError:
            cost = defaults[int_level]
        if int_level == level:
            return cost
        try:
            next_cost = idea[int_level + 1]
        except KeyError:
            next_cost = defaults[int_level + 1]
        return cost + (next_cost - cost) * (level - int_level)

    def __init__(self):
        self.idea_costs = {}
        self.country_costs = {}
        self._saved_ideas = {}

        self._load_idea_costs()
        self._load_country_costs()

    def _load_idea_costs(self):
        for fn in glob.iglob(path.join(common_path, 'custom_ideas/*.txt')):
            data = None
            category = None
            with open(fn, 'r') as f:
                data = nom(f.read())
            data = data.itervalues().next()
            for idea_name, values in data.iteritems():
                effect_name = None
                if idea_name == 'category':
                    category = values
                    continue
                assert category
                for k, v in values.iteritems():
                    if effect_name is None:
                        effect_name = k
                        self.idea_costs[effect_name] = {
                            'category': category,
                            'magnitude': Decimal(v),
                        }
                        continue
                    if k.startswith('level_cost_'):
                        self.idea_costs[effect_name][int(k[-1])] = int(v)
        
    def _load_country_costs(self):
        for fn in glob.iglob(path.join(common_path, 'ideas/*.txt')):
            if fn.endswith('basic_ideas.txt'):
                continue
            with open(fn, 'r') as f:
                data = nom(f.read())
                for k, v in data.iteritems():
                    self.country_costs[k[:k.find('_')].lower()] = self._load_ideas(v)

    def _load_ideas(self, ideas):
        result = []
        
        slot = 1
        for k, v in ideas['start'].iteritems():
            result.append(self._process_idea(slot, k, v))
        for idea_name in ideas.keys():
            if idea_name in ('start', 'bonus', 'trigger', 'free',):
                continue
            boni = ideas[idea_name]
            if boni is None:
                boni = self._saved_ideas[idea_name]
            else:
                self._saved_ideas[idea_name] = boni
            slot += 1
            for k, v in boni.iteritems():
                result.append(self._process_idea(slot, k, v))
        slot += 1
        for k, v in ideas['bonus'].iteritems():
            result.append(self._process_idea(slot, k, v))

        return result

    def _process_idea(self, slot, k, v):
        multiplier = self.IDEA_COST_PROGRESSION[slot - 1]
        try:
            idea = self.idea_costs[k]
        except KeyError:
            return (slot, k, v, -1, 0)
        level = Decimal(v) / idea['magnitude']
        cost = float(self.get_cost(idea, level)) * multiplier
        return (slot, k, v, level, cost)

    def dump(self, tag):
        total = 0
        for (slot, k, v, level, cost) in self.country_costs[tag]:
            print "%i: %s %s(%.2f) %.2f" % (slot, k, v, level, cost)
            total += cost
        print "-------------------"
        print "Total: %.2f" % total

    def stats(self):
        costs = {}
        for tag in self.country_costs.keys():
            total = 0
            values_missing = ''
            for (_, _, _, level, cost) in self.country_costs[tag]:
                total += cost
                if level < 0:
                    values_missing = '*'
            tag += values_missing
            if total not in costs:
                costs[total] = [tag,]
            else:
                costs[total].append(tag)
        for total in sorted(costs.keys()):
            print total, costs[total][0] if (len(costs[total]) == 1) else costs[total]

def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Prints idea costs for a tag or idea cost stats if not specified."
    )
    p.add_argument('--dryrun', '-n', action='store_true', help="dry run")
    p.add_argument('tag', nargs='?', help="tag or group name")
    options = p.parse_args()

    i = Ideas()
    c = Countries()
    if options.dryrun:
        return
    if options.tag != None:
        i.dump(options.tag.lower())
    else:
        i.stats()

if __name__ == '__main__':
    main()
