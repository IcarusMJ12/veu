#!/usr/bin/env python
#Copyright (c) 2012 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from PIL import Image, ImageFilter, ImageOps
import pygame
import logging
import types
import re
import glob
from os.path import basename
import getpass

from nom import nom
from model import *

MAP_FILE="/map/provinces.bmp"
MAP_SCALE=4
POSITIONS_FILE="/map/positions.txt"
SETUP_LOG_FILE="/logs/setup.log"
RE_LOG_POSITION=re.compile(r'Bounding Box of ([0-9]+) => \(([0-9]+),([0-9]+)\) - \(([0-9]+),([0-9]+)\)')
DEFAULT_FONTS='andalemono,bitstreamverasansmono,lucidaconsole'
DEFAULT_PATH='/Users/'+getpass.getuser()+'/Library/Application Support/Steam/SteamApps/common/europa universalis iii - complete/Data/'

class Map(object):
    def __init__(self, image, logger):
        self._logger=logger
        self._image=image
        self._scale=1
    
    def upscale(self, amount):
        self._logger.info("upscaling...")
        assert(isinstance(amount, int))
        new_size=(self._image.size[0]*amount, self._image.size[1]*amount)
        self._image=self._image.resize(new_size,Image.NEAREST)
        self._scale*=amount
        self._logger.info("done")
    
    def _isEdge(self, pixmap, x, y):
        for a in xrange(-1,2):
            for b in xrange(-1,2):
                if pixmap[x+a,y+b]!=pixmap[x,y]:
                    return True
        return False

    def findEdges(self, color=(0,255,0)):
        self._logger.info("finding edges...")
        image=self._image.filter(ImageFilter.FIND_EDGES)
        image=image.convert('L')
        image=image.point(lambda p: 0 if p==0 else 255)
        image=ImageOps.colorize(image, (0,0,0), color)
        image=image.filter(ImageFilter.SMOOTH_MORE)
        self._image=image
        self._logger.info("done")

    def getImage(self):
        return self._image

def _loadPositionsFromDef(self):
    self._logger.debug("nomming positions...")
    with open(self.positions_path,'r') as f:
        positions=nom(f.read())
        for key, value in positions.items():
            self._logger.debug('placing\t'+str(key))
            pos=None
            try:
                pos=value['text_position']
            except KeyError:
                try:
                    pos=value['city']
                except KeyError:
                    self._logger.error(str(key)+':'+str(value)+' lacks text_position and city')
            if pos:
                self.positions[int(key)]=(int(float(pos['x'])),int(float(pos['y'])))

def _loadPositionsFromLog(self):
    self._logger.debug("parsing out positions...")
    with open(self.setup_log_path, 'r') as f:
        for line in f:
            coordinates=RE_LOG_POSITION.search(line)
            if coordinates:
                coordinates=coordinates.groups()
                self.positions[int(coordinates[0])]=((int(coordinates[1])+int(coordinates[3]))/2,(int(coordinates[2])+int(coordinates[4]))/2)

class Veu(object):
    def __init__(self, eu3_data_path, logger):
        path=eu3_data_path
        self.path=path
        self._logger=logger

        self.map_path=path+MAP_FILE
        self._map_size=None

        self.positions_path=path+POSITIONS_FILE
        self.setup_log_path=path+SETUP_LOG_FILE
        self.positions={}
        #self._loadPositions=types.MethodType(_loadPositionsFromDef, self, Veu)
        self._loadPositions=types.MethodType(_loadPositionsFromLog, self, Veu)

        self.provinces=Provinces()
        self.countries=Countries()

        self.font=DEFAULT_FONTS
    
    def setMap(self, map_override):
        self.map_path=map_override

    def setFont(self, font):
        self.font=font
    
    def _loadMapSize(self):
        if not self._map_size:
            i=Image.open(self.map_path)
            self._logger.debug('map size: '+str(i.size))
            self._map_size=(i.size[0]*MAP_SCALE, i.size[1]*MAP_SCALE)
        return self._map_size

    def _areaFiles(self, relative_path):
        for filename in glob.iglob(self.path+relative_path):
            self._logger.debug('nomming '+filename+'...')
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
        m=Map(Image.open(self.map_path), self._logger)
        m.upscale(MAP_SCALE)
        m.findEdges()
        image=m.getImage()
        map_size=image.size
        #map_size=self._loadMapSize()
        raw_screen=pygame.Surface(map_size)
        screen=pygame.display.set_mode(map_size)
        bg=pygame.image.frombuffer(image.tostring('raw','RGB',0,1),map_size,'RGB').convert()
        #bg=pygame.image.load(self.map_path).convert()
        #scale=MAP_SCALE
        #while scale>1 and scale%2==0:
        #   bg=pygame.transform.scale2x(bg)
        #   scale/=2
        #if scale!=1:
        #   raise Exception("map scale must be a power of 2")
        raw_screen.blit(bg,(0,0))
        raw_screen=pygame.transform.flip(raw_screen,False,True)
        screen.blit(raw_screen,(0,0))
        pygame.display.update()

        #render text
        #font=pygame.font.SysFont(pygame.font.get_default_font(),12)
        font=pygame.font.SysFont(self.font,12)
        height=font.get_height()
        if not len(self.positions):
            self._loadPositions()
        if not len(self.provinces):
            self._loadProvinces()
        for key, value in self.positions.items():
            self._logger.debug('placing\t'+str(key))
            loc=(MAP_SCALE*int(float(value[0])),map_size[1]-MAP_SCALE*int(float(value[1]))-height)
            try:
                province=self.provinces[key][date]
                text=font.render(province['base_tax']+'/'+province['manpower'],False,(255,255,255))
                screen.blit(text,loc)
                text=font.render(province['owner'],False,(255,255,255))
                screen.blit(text,(loc[0],loc[1]-height))
            except KeyError as e:
                self._logger.warn(str(e)+' for '+str(key))
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
    parser.add_argument('--path','-p',nargs=1,help="path to EU3's data directory (containing history and map directories)")
    parser.add_argument('--verbose','-v',action='store_true',help="print debugging messages")
    parser.add_argument('--output','-o',nargs=1,help="save resultant image here [png extension recommended]")
    parser.add_argument('--map','-m',nargs=1,help="override default map image to draw upon")
    parser.add_argument('--date','-d',nargs=1,help="select date other than starting")
    parser.add_argument('--font','-f',nargs=1,help="use this system font instead")
    options=parser.parse_args()
    loglevel=logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=loglevel)
    path = options.path[0] if options.path else DEFAULT_PATH
    veu=Veu(path, logging)
    if options.map:
        logging.debug(str(options.map))
        veu.setMap(options.map[0])
    if options.font:
        veu.setFont=options.font[0]
    veu.showMap(options.output[0] if options.output else None, options.date[0] if options.date else the_beginning)
