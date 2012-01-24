#!/usr/bin/env python

import ply.lex as lex
import ply.yacc as yacc
import logging

__all__=['nom']

tokens = (
        'LCURLY',
        'RCURLY',
        'ITEM',
        'SEPARATOR',
        'NEWLINE',
        )

precedence = (
        ('left', 'SEPARATOR'),
        ('left', 'NEWLINE'),
        )

t_LCURLY                    = r'\{'
t_RCURLY                    = r'\}'
t_SEPARATOR             = r'='
t_ITEM                      = r'[a-zA-Z0-9_\-\.]+|\'.+\'|\".+\"'
t_ignore                    = ' \t\r'
t_ignore_COMMENT    = r'\#.*'

def t_error(t):
    logging.error("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

lexer=lex.lex()

def p_item_separator_item(p):
    'expression : ITEM SEPARATOR ITEM'
    p[0]=[(p[1],p[3])]

def p_item_separator_curlies(p):
    'expression : ITEM SEPARATOR LCURLY RCURLY'
    p[0]=[(p[1],None)]

def p_item_separator_expression(p):
    'expression : ITEM SEPARATOR expression'
    p[0]=[(p[1],p[3])]

def p_curly_expression_curly(p):
    'expression : LCURLY expression RCURLY'
    p[0]=toDict(p[2])

def p_expression_newline_expression(p):
    'expression : expression NEWLINE expression'
    p[0]=p[1]+p[3]

def p_expression_expression(p):
    'expression : expression expression'
    p[0]=p[1]+p[2]

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
    return toDict(parser.parse(buf))

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
