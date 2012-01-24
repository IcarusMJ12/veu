#!/usr/bin/env bash
#Run me if you have ImageMagick installed and want to generate a black-and-green map from the colorful default map.  You need to copy provinces.bmp from EU3's Data/map directory here first.
convert provinces.bmp -edge 1 -colorspace Gray -contrast-stretch 90x90% -fill green -opaque white provinces_1.bmp
