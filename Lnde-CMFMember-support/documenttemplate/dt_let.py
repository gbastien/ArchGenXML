##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""The Let tag was contributed to Zope by and is copyright, 1999
   Phillip J. Eby.  Permission has been granted to release the Let tag
   under the Zope Public License.


   Let name=value...

   The 'let' tag is used to bind variables to values within a block.

   The text enclosed in the let tag is rendered using information
   from the given variables or expressions.

   For example::

     <dtml-let foofunc="foo()" my_bar=bar>
       foo() = <dtml-var foofunc>,
       bar = <dtml-var my_bar>
     </dtml-let>

   Notice that both 'name' and 'expr' style attributes may be used to
   specify data.  'name' style attributes (e.g. my_bar=bar) will be
   rendered as they are for var/with/in/etc.  Quoted attributes will
   be treated as Python expressions.

   Variables are processed in sequence, so later assignments can
   reference and/or overwrite the results of previous assignments,
   as desired.

$Id: dt_let.py,v 1.2 2004/07/27 18:08:51 zworkb Exp $
"""
from dt_util import render_blocks, Eval, ParseError

from types import StringType
import re

class Let:
    blockContinuations = ()
    name = 'let'

    def __init__(self, context, blocks):
        tname, args, section = blocks[0]
        self.__name__ = args
        self.section = section.blocks
        self.args = args = parse_let_params(args)

        for i in range(len(args)):
            name,expr = args[i]
            if expr[:1] == '"' and expr[-1:] == '"' and len(expr) > 1:
                # expr shorthand
                expr = expr[1:-1]
                try:
                    args[i] = name, Eval(context, expr).eval
                except SyntaxError, v:
                    m,(huh,l,c,src) = v
                    raise ParseError, (
                        '<strong>Expression (Python) Syntax error</strong>:'
                        '\n<pre>\n%s\n</pre>\n' % v[0],
                        'let')


    def render(self, md):
        d = {}
        md._push(d)
        try:
            for name,expr in self.args:
                if isinstance(expr, StringType):
                    d[name] = md[expr]
                else:
                    d[name] = expr(md)
            return render_blocks(self.section, md)
        finally:
            md._pop(1)


    __call__ = render



def parse_let_params(text,
            result=None,
            tag='let',
            parmre=re.compile('([\000- ]*([^\000- ="]+)=([^\000- ="]+))'),
            qparmre=re.compile('([\000- ]*([^\000- ="]+)="([^"]*)")'),
            **parms):

    result = result or []

    mo = parmre.match(text)
    mo1 = qparmre.match(text)

    if mo is not None:
        name = mo.group(2)
        value = mo.group(3)
        l = len(mo.group(1))
    elif mo1 is not None:
        name = mo1.group(2)
        value = '"%s"' % mo1.group(3)
        l = len(mo1.group(1))
    else:
        if not text or not text.strip():
            return result
        raise ParseError, ('invalid parameter: "%s"' % text, tag)

    result.append((name,value))

    text = text[l:].strip()
    if text:
        return apply(parse_let_params, (text, result,tag), parms)
    else:
        return result