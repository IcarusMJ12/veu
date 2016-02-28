#!/usr/bin/env python

from glob import iglob
from os.path import join
from decimal import Decimal

from config import common_path
from nom import nom

__all__ = [
    'custom_ideas',
    'national_ideas',
    'get_idea_cost',
    'IDEA_COST_PROGRESSION',
    'IDEA_SLOTS',
]

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
DEFAULT_MAX_LEVEL = 4
# starting, then 7, then 1 last bonus
IDEA_COST_PROGRESSION = ( 2.0, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0, 1.0, 1.0, )
IDEA_SLOTS = range(1,9)

def _load_custom_ideas():
    result = {}
    
    for fn in iglob(join(common_path, 'custom_ideas/*.txt')):
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
                    result[effect_name] = {
                        'category': category,
                        'magnitude': Decimal(v),
                        'max_level': DEFAULT_MAX_LEVEL,
                    }
                    continue
                if k.startswith('level_cost_'):
                    result[effect_name][int(k[-1])] = int(v)
                    continue
                if k == 'max_level':
                    result[effect_name]['max_level'] = int(v)

    return result

_saved_ideas = {}
def _process_national_ideas(ideas):
    slot = [1,]
    result = dict([(i, []) for i in IDEA_SLOTS])

    def _slot_ideas(items):
        result[slot[0]] = tuple([ (k, v) for k, v in items ])
        slot[0] += 1

    # misc fields
    if 'trigger' in ideas.keys():
        result['trigger'] = ideas['trigger']
    if 'free' in ideas.keys():
        result['free'] = ideas['free']
        
    # starting ideas
    _slot_ideas(ideas['start'].items())

    # the 7 unlockable ideas
    for idea_name in ideas.keys():
        if idea_name in ('start', 'bonus', 'trigger', 'free',):
            continue
        boni = ideas[idea_name]
        if boni is None:
            boni = _saved_ideas[idea_name]
        else:
            _saved_ideas[idea_name] = boni
        _slot_ideas(boni.items())
    
    # bonus idea(s)
    _slot_ideas(ideas['bonus'].items())

    return result
    
ideas_by_tag = {}
def _load_national_ideas():
    def tagify(key, val):
        if len(val) > 1:
            print val
            #TODO
            return

        if 'tag' in val.keys():
            tags = val['tag']
            if isinstance(tags, list):
                for tag in tags:
                    ideas_by_tag[tag.lower()] = key
            else:
                ideas_by_tag[tags.lower()] = key
        if 'primary_culture' in val.keys():
            cultures = val['primary_culture']
            if isinstance(cultures, list):
                for culture in cultures:
                    ideas_by_tag[culture] = key
            else:
                ideas_by_tag[cultures] = key
        if 'OR' in val.keys():
            tagify(key, val['OR'])

    result = {}

    for fn in iglob(join(common_path, 'ideas/*.txt')):
        if fn.endswith('basic_ideas.txt'):
            continue
        data = None
        with open(fn, 'r') as f:
            data = nom(f.read())
        for k, v in data.iteritems():
            key = k[:k.find('_')].lower()
            ideas = _process_national_ideas(v)
            result[key] = ideas
            if 'trigger' in ideas.keys():
                tagify(key, ideas['trigger'])

    return result

custom_ideas = _load_custom_ideas()
national_ideas = _load_national_ideas()
missing_ideas = {
    'adm_tech_cost_modifier': { 2: 3, 'magnitude':  -0.05 },
    'caravan_power': { 2: 3, 'magnitude': 0.1 },
    'church_power_modifier': { 2: 3, 'magnitude': 0.05 },
    'devotion': { 2: 3, 'magnitude': 0.5 },
    'envoy_travel_time': { 2: 3, 'magnitude': -0.25 },
    'fabricate_claims_time': { 2: 3, 'magnitude': -0.2 },
    'free_leader_pool': { 2: 3, 'magnitude': 1 },
    'garrison_size': { 2: 3, 'magnitude': 0.1 },
    'global_foreign_trade_power': { 2: 3, 'magnitude': 0.1 },
    'global_heretic_missionary_strength': { 2: 3, 'magnitude': 0.01 },
    'global_own_trade_power': { 2: 3, 'magnitude': 0.1 },
    'global_regiment_cost': { 2: 5, 'magnitude': -0.1 }, # 5
    'global_ship_cost': { 2: 5, 'magnitude':  -0.05 }, # 5
    'global_trade_goods_size_modifier': { 2: 3, 'magnitude': 0.05 },
    'improve_relation_modifier': { 2: 3, 'magnitude':  0.15 },
    'justify_trade_conflict_time' : { 2: 3, 'magnitude':  -0.1 },
    'land_attrition': { 2: 3, 'magnitude': -0.1 },
    'loot_amount': { 2: 3, 'magnitude': 0.10 },
    'mil_tech_cost_modifier': { 2: 3, 'magnitude': -0.05 },
    'naval_attrition': { 2: 3, 'magnitude':  -0.10 },
    'papal_influence': { 2: 3, 'magnitude':  1 },
    'rebel_support_efficiency': { 2: 3, 'magnitude': 0.20 },
    'recover_army_morale_speed': { 2: 3, 'magnitude':  0.025 },
    'relations_decay_of_me': { 2: 3, 'magnitude':  0.15 },
    'trade_range_modifier': { 2: 3, 'magnitude':  0.10 },
    'unjustified_demands': { 2: 3, 'magnitude':  -0.25 },
}

# we perform linear interpolation when returning results because we are
# trying to be less-than-generous
def get_idea_cost(idea, level):
    defaults = IDEA_COST_DEFAULTS[idea[2] if 2 in idea else 5]
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

if __name__ == '__main__':
    print 'custom ideas:'
    for k, v in custom_ideas.iteritems():
        print '\t', k, ':', v
    print 'national ideas:'
    for k, v in national_ideas.iteritems():
        print '\t', k, ':', v
