#!/usr/bin/env bash
convert provinces.bmp -edge 1 -colorspace Gray -contrast-stretch 90x90% -fill green -opaque white provinces_1.bmp
