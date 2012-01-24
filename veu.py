#!/usr/bin/env python

from PIL import Image
import pygame
import logging
import types
import re
import glob
from os.path import basename

from nom import nom
from model import *

MAP_FILE="/map/provinces.bmp"
MAP_SCALE=4
POSITIONS_FILE="/map/positions.txt"
SETUP_LOG_FILE="/logs/setup.log"
RE_LOG_POSITION=re.compile(r'Bounding Box of ([0-9]+) => \(([0-9]+),([0-9]+)\) - \(([0-9]+),([0-9]+)\)')

def _loadPositionsFromDef(self):
    self.logger.debug("nomming positions...")
    with open(self.positions_path,'r') as f:
        positions=nom(f.read())
        for key, value in positions.items():
            self.logger.debug('placing\t'+str(key))
            pos=None
            try:
                pos=value['text_position']
            except KeyError:
                try:
                    pos=value['city']
                except KeyError:
                    self.logger.error(str(key)+':'+str(value)+' lacks text_position and city')
            if pos:
                self.positions[int(key)]=(int(float(pos['x'])),int(float(pos['y'])))

def _loadPositionsFromLog(self):
    self.logger.debug("parsing out positions...")
    with open(self.setup_log_path, 'r') as f:
        for line in f:
            coordinates=RE_LOG_POSITION.search(line)
            if coordinates:
                coordinates=coordinates.groups()
                self.positions[int(coordinates[0])]=((int(coordinates[1])+int(coordinates[3]))/2,(int(coordinates[2])+int(coordinates[4]))/2)

class Veu(object):
    def __init__(self, eu3_data_path, logger, map_override=None):
        path=eu3_data_path
        self.path=path
        self.logger=logger
        if map_override:
            self.map_path=map_override
        else:
            self.map_path=path+MAP_FILE
        self.positions_path=path+POSITIONS_FILE
        self.setup_log_path=path+SETUP_LOG_FILE

        self.positions={}
        self._map_size=None
        #self._loadPositions=types.MethodType(_loadPositionsFromDef, self, Veu)
        self._loadPositions=types.MethodType(_loadPositionsFromLog, self, Veu)

        self.provinces=Provinces()
        self.countries=Countries()
    
    def _loadMapSize(self):
        if not self._map_size:
            i=Image.open(self.map_path)
            self.logger.debug('map size: '+str(i.size))
            self._map_size=(i.size[0]*MAP_SCALE, i.size[1]*MAP_SCALE)
        return self._map_size

    def _areaFiles(self, relative_path):
        for filename in glob.iglob(self.path+relative_path):
            self.logger.debug('nomming '+filename+'...')
            with open(filename, 'r') as f:
                code_and_name=basename(filename).split('-')
                code=code_and_name[0].strip()
                name='-'.join(code_and_name[1:]).strip()
                yield f, code, name

    def _loadProvinces(self):
        for f, code, name in self._areaFiles('history/provinces/*.txt'):
            self.provinces.addProvince(Province(nom(f.read()),name,code))
    
    def _loadCountries(self):
        for f, code, name in self._areaFiles('history/countries/*.txt'):
            self.countries.addCountry(Country(nom(f.read()),name,code))

    def showMap(self, destination=None, date=the_beginning):
        pygame.display.init()
        pygame.font.init()

        #render map
        map_size=self._loadMapSize()
        raw_screen=pygame.Surface(map_size)
        screen=pygame.display.set_mode(map_size)
        bg=pygame.image.load(self.map_path).convert()
        scale=MAP_SCALE
        while scale>1 and scale%2==0:
            bg=pygame.transform.scale2x(bg)
            scale/=2
        if scale!=1:
            raise Exception("map scale must be a power of 2")
        raw_screen.blit(bg,(0,0))
        raw_screen=pygame.transform.flip(raw_screen,False,True)
        screen.blit(raw_screen,(0,0))
        pygame.display.update()

        #render text
        #font=pygame.font.SysFont(pygame.font.get_default_font(),12)
        font=pygame.font.SysFont('andalemono',12)
        height=font.get_height()
        if not len(self.positions):
            self._loadPositions()
        if not len(self.provinces):
            self._loadProvinces()
        for key, value in self.positions.items():
            self.logger.debug('placing\t'+str(key))
            loc=(MAP_SCALE*int(float(value[0])),map_size[1]-MAP_SCALE*int(float(value[1]))-height)
            try:
                province=self.provinces[key][date]
                text=font.render(province['base_tax']+'/'+province['manpower'],False,(255,255,255))
                screen.blit(text,loc)
                text=font.render(province['owner'],False,(255,255,255))
                screen.blit(text,(loc[0],loc[1]-height))
            except KeyError as e:
                self.logger.warn(str(e)+' for '+str(key))
        pygame.display.update()

        #save image if destination
        if destination:
            pygame.image.save(screen, destination)

        #wait to quit
        while True:
            event=pygame.event.wait()
            if event.type==pygame.QUIT:
                break
        pygame.display.quit()

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description="Show EU3 province data on a map.")
    parser.add_argument('path',nargs=1,help="path to EU3's data directory (containing history and map directories)")
    parser.add_argument('--verbose','-v',action='store_true',help="print debugging messages")
    parser.add_argument('--output','-o',nargs=1,help="save resultant image here")
    parser.add_argument('--map','-m',nargs=1,help="override default map image to draw upon")
    parser.add_argument('--date','-d',nargs=1,help="select date other than starting")
    options=parser.parse_args()
    loglevel=logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=loglevel)
    veu=Veu(options.path[0] if options.path else None, logging, options.map[0] if options.map else None)
    veu.showMap(options.output[0], options.date[0] if options.date else the_beginning)
