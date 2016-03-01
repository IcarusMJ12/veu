#!/usr/bin/env python

from decimal import Decimal

from eu4.eu_map import terrain_txt
from eu4.terrain import province_terrain, terrain_overrides
from eu4.history import countries, provinces

from eu4.ideas import (
    custom_ideas,
    missing_ideas,
    national_ideas,
    get_idea_cost,
    get_ideas_for_tag,
    IDEA_COST_PROGRESSION,
    IDEA_SLOTS,
)

IDEA_COSTS_FMT = "{!s}: {:>36} {:>6}({:6.2f}) {:>6.2f}"

class Countries(object):
    COST_PER_DEV = 0.5
    # actually provided by Paradox in game files, so no need for this anymore
    #EXTRA_COSTS = {
    #    'sound_toll': 20,
    #    'bosphorous_sound_toll': 10,
    #    'center_of_trade': 15,
    #    'estuary': 10,
    #}
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
        self._terrain = {}
        self._capitals = {}
        self._owners = {}
        self._province_base_costs = {}

        self._load_terrain()
        self._load_capitals()
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
            # Corfu
            142: 'coastline',
        }

        for k, v in province_terrain.iteritems():
            self._terrain[k] = v
        for k, v in terrain_overrides.iteritems():
            self._terrain[k] = v

        for k in TEST_TERRAIN.keys():
            assert(TEST_TERRAIN[k] == self._terrain[k])

    def _load_capitals(self):
        for tag, data in countries.iteritems():
            try:
                self._capitals[tag] = data['capital']
            except KeyError:
                pass

    def _load_provinces(self):
        for province_id, data in provinces.iteritems():
            self._load_province(province_id, data)

    def _load_province(self, province_id, data):
        if 'owner' not in data.keys():
            return
        owner = data['owner']
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

    def stats_per_province(self):
        inverted = {}
        for k, v in self._province_base_costs.iteritems():
            try:
                inverted[v].append(k)
            except KeyError:
                inverted[v] = [k]
        for cost in sorted(inverted.keys()):
            for province_id in inverted[cost]:
                print cost, province_id
    
    def stats(self):
        costs = {}

        for owner, provs in self._owners.iteritems():
            cost = 0
            for province_id in provs:
                cost += self._province_base_costs[province_id]
            try:
                costs[cost].append(owner)
            except KeyError:
                costs[cost] = [owner]

        for cost in sorted(costs.keys()):
            print cost, ','.join(costs[cost])

    def stats_for_owner(self, owner):
        # TODO: HRE
        total = 0
        for province_id in self._owners[owner]:
            cost = self._province_base_costs[province_id]
            print province_id, cost
            total += cost
        print '----------------'
        print 'Total', total

class Ideas(object):
    @staticmethod
    def get_level_and_cost(slot, bonus, magnitude):
        multiplier = IDEA_COST_PROGRESSION[slot]
        was_missing = True
        try:
            idea = custom_ideas[bonus]
            was_missing = False
        except KeyError:
            try: 
                idea = missing_ideas[bonus]
            except KeyError:
                return (-1, 0)
        level = Decimal(magnitude) / Decimal(idea['magnitude'])
        cost = float(get_idea_cost(idea, level)) * multiplier
        return (level if not was_missing else -1, cost)

    def stats_for_owner(self, tag):
        total = 0
        ideas = get_ideas_for_tag(tag)

        for slot in IDEA_SLOTS:
            for k, v in ideas[slot]:
                level, cost = self.get_level_and_cost(slot, k, v)
                print IDEA_COSTS_FMT.format(slot, k, v, level, cost)
                total += cost
        print "-------------------"
        print "Total: %.2f" % total

    def stats(self):
        print "Legend:"
        print "\t> Has more than 10 ideas."
        print "\t+ At least one idea past maximum allowed level."
        print "\t* Has an illegal idea that is not defined."
        print ""

        costs = {}
        for tag, ideas in national_ideas.iteritems():
            total = 0
            ideas_count = 0
            values_missing = ''
            values_exceed_max = ''
            for slot in IDEA_SLOTS:
                for k, v in ideas[slot]:
                    level, cost = self.get_level_and_cost(slot, k, v)
                    total += cost
                    ideas_count += 1
                    if level < 0:
                        values_missing = '*'
                    elif level > custom_ideas[k]['max_level']:
                        values_exceed_max = '+'
            tag += values_exceed_max + values_missing
            if ideas_count > 10:
                tag += '>'
            if total not in costs:
                costs[total] = [tag,]
            else:
                costs[total].append(tag)
        for total in sorted(costs.keys()):
            print "%.2f %s" % (total, ' '.join(costs[total]))

def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Prints costs for a tag or idea cost stats if not specified."
    )
    p.add_argument('--dryrun', '-n', action='store_true', help="dry run")
    p.add_argument('--ideas', '-i', action='store_true', help="idea costs only")
    p.add_argument('--provinces', '-p', action='store_true', help="province costs only")
    p.add_argument('tag', nargs='?', help="tag or group name")
    options = p.parse_args()

    i = None
    if not options.provinces:
        i = Ideas()

    c = None
    if not options.ideas:
        c = Countries()

    if options.dryrun:
        return

    if options.tag != None:
        tag = options.tag.lower()
        if i:
            i.stats_for_owner(tag)
        if i and c:
            print '======================\n'
        if c:
            c.stats_for_owner(tag)

    else:
        if i:
            i.stats()
        print '---------'
        if c:
            c.stats()

if __name__ == '__main__':
    main()
