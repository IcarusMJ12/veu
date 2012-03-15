#!/usr/bin/env python
#Copyright (c) 2012 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import logging

class Map(object):
    def __init__(self, image, cache=None, scale=1, loglevel=logging.INFO):
        self._logger=logging.getLogger(name=self.__class__.__name__)
        self._logger.setLevel(loglevel)
        self._provinces=image
        self._edges=None
        self._countries=None
        self._scale=scale
        self._cache=cache
        provinces_cache_path=self._cache+'provinces'+str(self._scale)+'.png'
        edges_cache_path=self._cache+'edges'+str(self._scale)+'.png'
        if self._cache!=None:
            if not exists(self._cache):
                makedirs(self._cache)
            try:
                self._provinces=Image.open(provinces_cache_path)
                self._edges=Image.open(edges_cache_path)
                self._logger.info("not resizing or finding edges -- reading from cache instead")
            except IOError:
                self._logger.info("cache appears to be empty")
                self._upscale()
                self._findEdges()
                self._provinces.save(provinces_cache_path)
                self._edges.save(edges_cache_path)
        else:
            self._upscale()
            self._findEdges()
    
    def _upscale(self):
        self._logger.info("upscaling...")
        assert(isinstance(self._scale, int))
        if self._scale>1:
            new_size=(self._provinces.size[0]*self._scale, self._provinces.size[1]*self._scale)
            self._logger.info('\tresizing...')
            self._provinces=self._provinces.resize(new_size,Image.NEAREST)
            if 'weave' not in globals():
                self._logger.warn('\tscipy.weave was not imported; expect ugly-looking maps due to lack of smoothing')
            else:
                self._logger.info('\tsmoothing...')
                r=self._scale/2
                s=array(self._provinces)
                x, y = s.shape[:2]
                d=s.copy()
                with open('smoothing.c','r') as f:
                    smoothing_code=f.read()
                weave.inline(smoothing_code, ['s','d','x','y','r'], type_converters=weave.converters.blitz)
                self._provinces=Image.fromarray(d)
    
    def _findEdges(self):
        self._logger.info("finding edges...")
        image=self._provinces.filter(ImageFilter.FIND_EDGES)
        image=image.convert('L')
        image=image.point(lambda p: 0 if p==0 else 255)
        alpha=ImageOps.invert(image)
        image=ImageOps.colorize(image, (255,255,255), (0,0,0)).convert('RGBA')
        image.putalpha(alpha)
        self._edges=image

    def getShadedMap(self, color_map=None, default=None):
        result=self._provinces
        if color_map:
            self._logger.info("recoloring...")
            result=result.copy()
            data=result.load()
            for x in xrange(result.size[0]):
                for y in xrange(result.size[1]):
                    try:
                        data[x, y]=color_map[data[x,y]]
                    except KeyError:
                        if default:
                            data[x,y]=default
        return Image.composite(result, self._edges, self._edges)
