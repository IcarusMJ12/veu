#!/usr/bin/env python
"""
Prints out valuable country stats in a tab-delimited format.
"""

from nom import nom
from os.path import basename, splitext, join
from glob import glob
from model import EUData

if __name__ == '__main__':
    import argparse
    from sys import exit, stdout
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('basepath', help='Path to the Europa Universalis III\'s Data directory.')
    args = parser.parse_args()
    eu_data = EUData(args.basepath)
    provinces = {}
    for province in eu_data.provinces.values():
        try:
            owner = province['']['owner']
            if owner in provinces:
                provinces[owner].append(province[''])
            else:
                provinces[owner] = [province['']]
        except KeyError:
            pass
    labels = ('government','aristocracy_plutocracy','centralization_decentralization','innovative_narrowminded','mercantilism_freetrade','offensive_defensive','land_naval','quality_quantity','serfdom_freesubjects','technology_group','primary_culture','add_accepted_culture','religion')
    extra_labels = ('provinces',)
    province_labels = ('base_tax', 'citysize')

    stdout.write('tag'+'\t'+'name')
    for label in labels:
        stdout.write('\t'+label)
    for label in extra_labels:
        stdout.write('\t'+label)
    for label in province_labels:
        stdout.write('\t'+label)
    stdout.write('\n')
    keys = eu_data.countries.keys()
    keys.sort()
    for key in keys:
        if key not in provinces:
            continue
        data = eu_data.countries[key]['']
        stdout.write(key+'\t'+data['name'])
        for label in labels:
            try:
                value = data[label]
                if isinstance(value, list):
                    stdout.write('\t'+','.join(value))
                else:
                    stdout.write('\t'+str(data[label]))
            except KeyError:
                stdout.write('\t')
        stdout.write('\t'+str(len(provinces[key])))
        for label in province_labels:
            stdout.write('\t'+str(sum([int(province[label]) for province in provinces[key]])))
        stdout.write('\n')
