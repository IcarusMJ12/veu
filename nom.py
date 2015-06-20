#!/usr/bin/env python
# Copyright (c) 2012-2015 Igor Kaplounenko
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a
# copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to
# Creative Commons, 444 Castro Street, Suite 900, Mountain View,
# California, 94041, USA.

from collections import OrderedDict

import ply.lex as lex
import ply.yacc as yacc

__all__ = ['nom', 'PlyException']


class PlyException(Exception):
    pass

tokens = (
    'LCURLY',
    'RCURLY',
    'ITEM',
    'SEPARATOR',
)

t_LCURLY = r'\{'
t_RCURLY = r'\}'
t_SEPARATOR = r'='
t_ITEM = r'\'.+\'|\".+\"|[^ \t\r\n\{\}\=\#]+'
t_ignore = ' \t\r\n'
t_ignore_COMMENT = r'\#.*'


def t_error(t):
    raise PlyException("Illegal character '%s'" % t.value[0])

lexer = lex.lex()


def p_result(p):
    'result : nothing'
    p[0] = None


def p_result_keyvalues(p):
    'result : keyvalues'
    p[0] = p[1]


def p_keyvalues_keyvalues(p):
    'keyvalues : keyvalues keyvalues'
    p[0] = p[1] + p[2]


def p_nothing(p):
    'nothing :'
    pass


def p_key_value(p):
    'keyvalues : key value'
    p[0] = [(p[1], p[2])]


def p_value_value(p):
    'values : value value'
    p[0] = [p[1], p[2]]


def p_value_values(p):
    'values : values value'
    p[0] = p[1] + [p[2]]


def p_curly_curly(p):
    'value : LCURLY RCURLY'
    p[0] = None


def p_curly_values_curly(p):
    'value : LCURLY values RCURLY'
    p[0] = tuple(p[2])


def p_curly_value_curly(p):
    'value : LCURLY value RCURLY'
    p[0] = (p[2],)


def p_curly_keyvalues_curly(p):
    'value : LCURLY keyvalues RCURLY'
    p[0] = toDict(p[2])


def p_item_separator(p):
    'key : ITEM SEPARATOR'
    p[0] = p[1]


def p_item(p):
    'value : ITEM'
    p[0] = p[1]


def p_error(p):
    raise PlyException("Error parsing '%s'." % p)

parser = yacc.yacc()


def toDict(l):
    if not l:
        l = OrderedDict()
    d = OrderedDict()
    for key, value in l:
        if key not in d and not key.startswith('add_') and not key.startswith('remove_'):
            d[key] = value
        else:
            try:
                d[key].append(value)
            except AttributeError:
                d[key] = [d[key], value]
            except KeyError:
                d[key] = [value]
    return d


def nom(buf, debug=False):
    return toDict(parser.parse(buf, debug=debug))

def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Consumes EU3 text data and generates a dictionary from it.")
    p.add_argument('file', nargs=1, help="file to parse")
    p.add_argument(
        '--debug', '-d', action='store_true', help="print debugging messages")
    p.add_argument(
        '--silent', '-s', action='store_true', help="do not print nom output")
    p.add_argument(
        '--verbose', '-v', action='store_true', help="be more verbose")
    options = p.parse_args()
    if options.verbose:
        print options.file[0]
    with open(options.file[0], 'rb') as f:
        buf = f.read()
        try:
            result = nom(buf, True if options.debug else False)
            if not options.silent:
                print result
        except PlyException as e:
            print str(e)

if __name__ == '__main__':
    main()
