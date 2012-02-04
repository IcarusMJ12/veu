#!/usr/bin/env python
#Copyright (c) 2012 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import ply.lex as lex
import ply.yacc as yacc
import logging

__all__=['nom']

tokens = (
        'LCURLY',
        'RCURLY',
        'ITEM',
        'SEPARATOR',
        )

"""
precedence = (
        ('left', 'SEPARATOR'),
        )
"""

t_LCURLY                    = r'\{'
t_RCURLY                    = r'\}'
t_SEPARATOR             = r'='
t_ITEM                      = r'[a-zA-Z0-9_\-\.]+|\'.+\'|\".+\"'
t_ignore                    = ' \t\r\n'
t_ignore_COMMENT    = r'\#.*'

def t_error(t):
    logging.error("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer=lex.lex()

def p_keyvalue_keyvalue(p):
    'keyvalues : keyvalue keyvalue'
    p[0]=p[1]+p[2]

def p_keyvalues_keyvalue(p):
    'keyvalues : keyvalues keyvalue'
    p[0]=p[1]+p[2]

def p_key_value(p):
    'keyvalue : key value'
    p[0]=[(p[1],p[2])]

def p_value_value(p):
    'values : value value'
    p[0]=[p[1], p[2]]

def p_value_values(p):
    'values : values value'
    p[0]=p[1]+[p[2]]

def p_curly_curly(p):
    'value : LCURLY RCURLY'
    p[0]=None

def p_curly_values_curly(p):
    'value : LCURLY values RCURLY'
    p[0]=tuple(p[2])

def p_curly_keyvalues_curly(p):
    'value : LCURLY keyvalues RCURLY'
    p[0]=toDict(p[2])

def p_curly_keyvalue_curly(p):
    'value : LCURLY keyvalue RCURLY'
    p[0]=toDict(p[2])

def p_item_separator(p):
    'key : ITEM SEPARATOR'
    p[0]=p[1]

def p_item(p):
    'value : ITEM'
    p[0]=p[1]

def p_error(p):
    logging.error("Error parsing '%s'." % p)

parser=yacc.yacc()

def toDict(l):
    if not l:
        l={}
    d={}
    for key, value in l:
        if key not in d and not key.startswith('add_') and not key.startswith('remove_'):
            d[key]=value
        else:
            try:
                d[key].append(value)
            except AttributeError:
                d[key]=[d[key],value]
            except KeyError:
                d[key]=[value]
    return d

def nom(buf):
    if len(buf.strip()):
        return toDict(parser.parse(buf, debug=True))
    else:
        return {}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description="Consumes EU3 text data and generates a dictionary from it.")
    p.add_argument('file',nargs=1,help="file to parse")
    p.add_argument('--verbose','-v',action='store_true',help="print debugging messages")
    options=p.parse_args()
    loglevel=logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=loglevel)
    with open(options.file[0],'rb') as f:
        buf=f.read()
        print nom(buf)
