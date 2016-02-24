#!/usr/bin/env python

from glob import iglob
from os.path import join
import csv

from PIL import Image

from config import map_path
from nom import nom

def _load(fn):
    if fn.endswith('.bmp'):
        return Image.open(join(map_path, fn), 'r')

    data = None
    with open(join(map_path, fn), 'r') as f:
        data = f.read()
    return nom(data)

def _load_definition():
    definition = {}
    with open(join(map_path, 'definition.csv')) as f:
        reader = csv.reader(f, delimiter=';')
        reader.next()
        for row in reader:
            definition[(int(row[1]), int(row[2]), int(row[3]))] = int(row[0])
    return definition

positions = _load('positions.txt')
provinces = _load('provinces.bmp')
terrain_bmp = _load('terrain.bmp')
terrain_txt = _load('terrain.txt')
definition = _load_definition()
