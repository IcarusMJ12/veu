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
LINE = '-' * 79
DOUBLE_LINE = '=' * 79

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
    def _get_ruler_cost(a, d, m, age):
        return (a + d + m - 6) * 60/age

    @staticmethod
    def _get_heir_cost(a, d, m, age):
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

    def _base_cost(self, province_id):
        data = provinces[province_id]

        return (
            int(data['base_tax']) +
            int(data['base_production']) +
            int(data['base_manpower'])
        ) * 0.5 * self.TERRAIN_MULTIPLIERS[self._terrain[province_id]]

    def _extra_cost(self, province_id):
        cost = 0
        data = provinces[province_id]
        if data['trade_goods'] == 'gold':
            cost += self.GOLD_MULTIPLIER * int(data['base_production'])
        if 'extra_cost' in data.keys():
            cost += int(data['extra_cost'])

        return cost

    def _load_provinces(self):
        for province_id in provinces.keys():
            self._load_province(province_id)

    def _load_province(self, province_id):
        data = provinces[province_id]

        if 'owner' not in data.keys():
            return

        owner = data['owner']
        try:
            self._owners[owner].append(province_id)
        except KeyError:
            self._owners[owner] = [ province_id ]
        self._province_base_costs[province_id] = self._base_cost(province_id)

    def _is_hre(self, owner):
        try:
            capital = provinces[int(countries[owner]['capital'])]
            return (capital['hre'] == 'yes')
        except KeyError:
            return False

    def owners(self):
        return self._owners.keys()

    def stats_for_owner(self, owner):
        results = { 'total': 0, 'provinces': [] }

        # HRE
        hre_mult = 1.0
        if self._is_hre(owner):
            results['total'] += 20
            hre_mult = self.HRE_CAPITAL_MULT

        for province_id in self._owners[owner]:
            cost = self._province_base_costs[province_id] * hre_mult
            cost += self._extra_cost(province_id)
            results['provinces'].append( (province_id, cost) )
            results['total'] += cost

        return results

    def print_stats_per_province(self):
        inverted = {}
        for k, v in self._province_base_costs.iteritems():
            v += self._extra_cost(k)
            try:
                inverted[v].append(k)
            except KeyError:
                inverted[v] = [k]

        print "Assuming a non-HRE capital."
        for cost in sorted(inverted.keys()):
            for province_id in inverted[cost]:
                print cost, province_id
    
    def print_stats(self):
        costs = {}

        for owner, provs in self._owners.iteritems():
            cost = 0
            hre_mult = 1.0 if not self._is_hre(owner) else self.HRE_CAPITAL_MULT
            for province_id in provs:
                cost += self._province_base_costs[province_id] * hre_mult
                cost += self._extra_cost(province_id)
            try:
                costs[cost].append(owner)
            except KeyError:
                costs[cost] = [owner]

        for cost in sorted(costs.keys()):
            print cost, ','.join(costs[cost])

    def print_stats_for_owner(self, owner):
        stats = self.stats_for_owner(owner)
        for province_id, cost in stats['provinces']:
            print province_id, cost
        print LINE
        print 'Total', stats['total']

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

    def stats_for_ideas(self, ideas):
        result = {
            'total': 0, 'ideas': [], 'ideas_count': 0,
            'values_missing': False, 'values_exceed_max': False
        }

        for slot in IDEA_SLOTS:
            for k, v in ideas[slot]:
                level, cost = self.get_level_and_cost(slot, k, v)
                result['ideas'].append( (slot, k, v, level, cost) )
                result['total'] += cost
                result['ideas_count'] += 1
                if level < 0:
                    result['values_missing'] = True
                elif level > custom_ideas[k]['max_level']:
                    result['values_exceed_max'] = True

        return result

    def print_legend(self):
        print "Legend:"
        print "\t> Has more than 10 ideas."
        print "\t+ At least one idea past maximum allowed level."
        print "\t* Has an illegal idea that is not defined."
        print ""

    @staticmethod
    def get_flags(stats):
        flags = ''
        if stats['values_exceed_max']:
            flags += '+'
        if stats['values_missing']:
            flags += '*'
        if stats['ideas_count'] > 10:
            flags += '>'
        return flags

    def print_stats_for_tag(self, tag):
        name, ideas = get_ideas_for_tag(tag)
        stats = self.stats_for_ideas(ideas)

        self.print_legend()
        print name, 'ideas:'
        for slot, k, v, level, cost in stats['ideas']:
            print IDEA_COSTS_FMT.format(slot, k, v, level, cost)
        print LINE
        print "Total: %.2f %s" % (stats['total'], self.get_flags(stats))

    def print_stats(self):
        costs = {}
        for tag, ideas in national_ideas.iteritems():
            stats = self.stats_for_ideas(ideas)
            if stats['values_exceed_max']:
                tag += '+'
            if stats['values_missing']:
                tag += '*'
            if stats['ideas_count'] > 10:
                tag += '>'
            total = stats['total']
            if total not in costs:
                costs[total] = [tag,]
            else:
                costs[total].append(tag)

        self.print_legend()
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
            i.print_stats_for_tag(tag)
        if i and c:
            print DOUBLE_LINE, '\n'
        if c:
            c.print_stats_for_owner(tag)

    else:
        if not c:
            i.print_stats()
        elif not i:
            c.print_stats()
        else:
            totals = {}
            for owner in c.owners():
                ideas_stats = i.stats_for_ideas(get_ideas_for_tag(owner)[1])
                cost = c.stats_for_owner(owner)['total']
                cost += ideas_stats['total']
                flags = i.get_flags(ideas_stats)
                try:
                    totals[cost].append(owner + flags)
                except KeyError:
                    totals[cost] = [ owner + flags ]
            for key in sorted(totals.keys()):
                print key, ', '.join(totals[key])

if __name__ == '__main__':
    main()
