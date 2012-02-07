#!/usr/bin/env python
#Copyright (c) 2012 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from PIL import Image, ImageFilter, ImageOps
import pygame
import logging
import types
import re
import glob
from os.path import basename, splitext
import getpass

from nom import nom
from model import *

MAP_FILE="/map/provinces.bmp"
MAP_SCALE=8
SETUP_LOG_FILE="/logs/setup.log"
RE_LOG_POSITION=re.compile(r'Bounding Box of ([0-9]+) => \(([0-9]+),([0-9]+)\) - \(([0-9]+),([0-9]+)\)')
DEFAULT_FONTS='andalemono,bitstreamverasansmono,lucidaconsole'
DEFAULT_PATH='/Users/'+getpass.getuser()+'/Library/Application Support/Steam/SteamApps/common/europa universalis iii - complete/Data/'
TEXT_COLOR=(255,255,255)

def units(population, base_tax):
    return min(0.99+float(population)/100000, 2)+float(base_tax)/20

class Map(object):
    def __init__(self, image, logger):
        self._logger=logger
        self._provinces=image
        self._edges=None
        self._countries=None
        self._scale=1
    
    def upscale(self, amount):
        self._logger.info("upscaling...")
        assert(isinstance(amount, int))
        if amount>1:
            new_size=(self._provinces.size[0]*amount, self._provinces.size[1]*amount)
            self._provinces=self._provinces.resize(new_size,Image.NEAREST)
            self._scale*=amount
        self._logger.info("done")
    
    def _isEdge(self, pixmap, x, y):
        for a in xrange(-1,2):
            for b in xrange(-1,2):
                if pixmap[x+a,y+b]!=pixmap[x,y]:
                    return True
        return False

    def findEdges(self):
        self._logger.info("finding edges...")
        image=self._provinces.filter(ImageFilter.FIND_EDGES)
        image=image.convert('L')
        image=image.point(lambda p: 0 if p==0 else 255)
        alpha=ImageOps.invert(image)
        image=ImageOps.colorize(image, (255,255,255), (0,0,0)).convert('RGBA')
        image.putalpha(alpha)
        self._edges=image
        self._logger.info("done")

    def getEdges(self):
        if not self._edges:
            self.findEdges()
        return self._edges

    def getShadedMap(self, color_map=None, default=None):
        result=self._provinces
        if color_map:
            result=result.copy()
            data=result.load()
            for x in xrange(result.size[0]):
                for y in xrange(result.size[1]):
                    try:
                        data[x, y]=color_map[data[x,y]]
                    except KeyError:
                        if default:
                            data[x,y]=default
        edges=self.getEdges()
        return Image.composite(result, edges, edges)

    def getProvinces(self):
        return self._provinces

def _loadPositionsFromLog(self):
    self._logger.debug("parsing out positions...")
    with open(self.setup_log_path, 'r') as f:
        for line in f:
            coordinates=RE_LOG_POSITION.search(line)
            if coordinates:
                coordinates=coordinates.groups()
                self.positions[int(coordinates[0])]=[int(c) for c in coordinates[1:]]

class Veu(object):
    def __init__(self, eu3_data_path, logger):
        path=eu3_data_path
        self.path=path
        self._logger=logger

        self.map_path=path+MAP_FILE
        self._map_size=None

        self.setup_log_path=path+SETUP_LOG_FILE
        self.positions={}
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
                name=splitext('-'.join(code_and_name[1:]).strip())[0]
                yield f, code, name

    def _loadProvinces(self):
        for f, code, name in self._areaFiles('history/provinces/*.txt'):
            self.provinces.addProvince(Province(nom(f.read()),name,code))
    
    def _loadCountries(self):
        for f, code, name in self._areaFiles('history/countries/*.txt'):
            self.countries.addCountry(Country(nom(f.read()),name,code))
    
    def _loadProvinceColors(self):
        self._logger.info("reading province colors...")
        self.province_colors={}
        with open(self.path+'map/definition.csv') as f:
            f.readline()
            for line in f:
                elements=line.split(';')
                self.province_colors[int(elements[0])]=tuple([int(e) for e in elements[1:4]]+[255])
        #self._logger.debug('province_colors: '+str(self.province_colors))
    
    def _loadCountryColors(self):
        self._logger.info("reading country colors...")
        self.country_colors={}
        name_code_map={}
        with open(self.path+'common/countries.txt', 'r') as f:
            for line in f:
                values=line.split('=')
                if len(values)<2:
                    continue
                code, filename = values
                name=splitext(basename(filename))[0].lower()
                name_code_map[name.strip()]=code.strip()
        self._logger.debug('name_code_map: '+str(name_code_map))
        for filename in glob.iglob(self.path+'common/countries/*.txt'):
            self._logger.debug("nomming "+filename+'...')
            with open(filename, 'r') as f:
                d=nom(f.read())
                try:
                    self.country_colors[name_code_map[splitext(basename(filename))[0].lower()]]=tuple([int(channel) for channel in d['color']])
                except KeyError as e:
                    self._logger.error(filename+': '+str(e)+' '+str(d))

    def showMap(self, destination=None, date=the_beginning):
        pygame.display.init()
        pygame.display.set_caption('veu running...')
        pygame.display.set_mode((200,1))
        pygame.font.init()

        #colors for the political map
        if not len(self.positions):
            self._loadPositions()
        if not len(self.provinces):
            self._loadProvinces()
        self._loadCountryColors()
        self._loadProvinceColors()
        color_map={}
        for province in self.provinces.values():
            province=province[date]
            try:
                color_map[self.province_colors[province['code']]]=self.country_colors[province['owner']]
            except KeyError:
                if 'base_tax' in province:
                    color_map[self.province_colors[province['code']]]=(20,20,20,255)
                else:
                    color_map[self.province_colors[province['code']]]=(0,0,255,255)

        #render map
        m=Map(Image.open(self.map_path).convert('RGBA'), self._logger)
        m.upscale(MAP_SCALE)
        image=m.getShadedMap(color_map)
        map_size=image.size
        screen=pygame.Surface(map_size)
        bg=pygame.image.frombuffer(image.tostring('raw','RGBA',0,1),map_size,'RGBA').convert()
        screen.blit(bg,(0,0))
        screen=pygame.transform.flip(screen,False,True)

        #render text
        font_small=pygame.font.SysFont(self.font,8, True)
        font_medium=pygame.font.SysFont(self.font,12, True)
        font_large=pygame.font.SysFont(self.font,16, True)
        size_small, size_medium, size_large = font_small.size('%'), font_medium.size('%'), font_large.size('%')
        for key, value in self.positions.items():
            self._logger.debug('placing\t'+str(key))
            x1, y1, x2, y2 = MAP_SCALE*value[0], map_size[1]-MAP_SCALE*value[1], MAP_SCALE*value[2], map_size[1]-MAP_SCALE*value[3]
            x_mid, y_mid = (x1+x2)/2, (y1+y2)/2
            max_size = ((x2-x1)/9, (y1-y2)/2)
            font=font_small
            size=size_small
            if max_size[0]>size_large[0] and max_size[1]>size_large[1]:
                font=font_large
                size=size_large
            elif max_size[0]>size_medium[0] and max_size[1]>size_medium[1]:
                font=font_medium
                size=size_medium
            try:
                province=self.provinces[key][date]
                if 'citysize' in province.keys():
                    text=font.render(province['base_tax']+'/'+province['manpower']+'/'+str(units(province['citysize'],province['base_tax']))[0:4],True,TEXT_COLOR)
                else:
                    text=font.render(province['base_tax']+'/'+province['manpower']+'/-',True,TEXT_COLOR)
                screen.blit(text,(x_mid-text.get_width()/2, y_mid))
                text=font.render(province['owner'],True,TEXT_COLOR)
                screen.blit(text,(x_mid-text.get_width()/2,y_mid-size[1]))
            except KeyError as e:
                self._logger.debug(str(e)+' for '+str(key))

        #save image if destination
        if destination:
            pygame.image.save(screen, destination)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description="Show EU3 province data on a map.")
    parser.add_argument('action',nargs=1,help="action to take", choices=("map","stats"))
    parser.add_argument('--path','-p',nargs=1,help="path to EU3's data directory (containing history and map directories)")
    parser.add_argument('--verbose','-v',action='store_true',help="print debugging messages")
    parser.add_argument('--output','-o',nargs=1,help="save resultant image here [png extension recommended]")
    parser.add_argument('--map','-m',nargs=1,help="override default map image to draw upon")
    parser.add_argument('--date','-d',nargs=1,help="select date other than starting")
    parser.add_argument('--font','-f',nargs=1,help="use this system font instead")
    parser.add_argument('--scale','-s',nargs=1,help="scale up the map (defaults to "+str(MAP_SCALE)+")")
    options=parser.parse_args()
    loglevel=logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=loglevel)
    path = options.path[0] if options.path else DEFAULT_PATH
    veu=Veu(path, logging)
    if options.scale:
        MAP_SCALE=int(options.scale[0])
    if options.map:
        logging.debug(str(options.map))
        veu.setMap(options.map[0])
    if options.font:
        veu.setFont=options.font[0]
    if options.action[0]=='map':
        if not options.output:
            logging.critical("Output image must be specified!")
            exit(1)
        else:
            veu.showMap(options.output[0] if options.output else None, options.date[0] if options.date else the_beginning)
    elif options.action[0]=='stats':
        logging.info("Not implemented.")
