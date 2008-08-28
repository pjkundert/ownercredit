#!/usr/bin/env python

"""
hex.dump
hex.load

    Classic 3 column hex dump and load functions.

        >>> print dump( "This is a test\nof hex.dump" )
           0: 5468 6973 2069 7320 6120 7465 7374 0a6f    This is a test.o
          16: 6620 6865 7864 756d 70                     f dump
"""

__author__ 				= "Perry Kundert (perry.kundert@enbridge.com)"
__version__ 				= "$Revision: 1.1 $"
__date__ 				= "$Date: 2006/05/10 14:41:17 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "Enbridge Pipelines Inc."

import re
import unittest

dumptrans 				= ''.join( [ x > 31 and x < 127 and x != 92 and chr( x ) or '.' for x in range(256)])
def dump( src, length = 16 ):
    N					= 0
    result				= ''
    while src:
        lead,src 			= src[:length],src[length:]
        hexl				= [ "%02x" % ord( x ) for x in lead ]
        hexs				= ''
        while hexl:
            pair,hexl			= hexl[:2],hexl[2:]
            hexs		       += ' ' + ''.join( pair )
        result 			       += "%6d:%-*s    %s\n" % ( N, length*2*5/4, hexs, lead.translate( dumptrans ))
        N			       += length
    return result


def load( src ):
    """
    Loads a string from a hex.dump, bracketed by spaces,
    digits and a non-hex char on front, multiple spaces on back
    """
    lines				= src.split( '\n' )
    result				= ''
    #          ' \t   0: 0800 20b1 fb6b 0012 d903 c510 0800 4500    .. ..k........E.'
    # matches           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #          ' \t   0: 080020b1fb6b00                             .. ..k.
    # matches           ^^^^^^^^^^^^^^^
    pat					= re.compile( r"""
      ^(?: \s | \d | \# )*?:		# A colon terminated leader like: #    123: (non-greedy)
      ( (?: \s? [0-9A-Za-z]{2} )+ )	# Any number of pairs of hex digits optionally separated by one space
      \s\s+				# Followed by 2 or more spaces (and anything else, but we dont' care)
      """, re.VERBOSE )
    for l in lines:
        if l:
            # l : ' \t   0: 0800 20b1 fb6b 0012 d903 c510 0800 4500    .. ..k........E.'
            m				= pat.match( l )
            if m and m.group( 1 ):
                # group: 080020b1...
                # print l, " ==> ", m.group( 1 )
                group			= ''.join( m.group( 1 ).split() )
                while group:
                    hex,group		= group[:2],group[2:]
                    result	       += chr( int( hex, 16 ))
    return result

# 
# Unit Tests		--  Run if file is executed.
# 
class TestLoad( unittest.TestCase ):
    def setUp( self ):
        pass

    def testSimple( self ):
        orig = """All good boys deserve fudge!\nBut some good boys deserve more!!\0"""
        d = dump( orig )
        self.assertEqual( d, """\
     0: 416c 6c20 676f 6f64 2062 6f79 7320 6465    All good boys de
    16: 7365 7276 6520 6675 6467 6521 0a42 7574    serve fudge!.But
    32: 2073 6f6d 6520 676f 6f64 2062 6f79 7320     some good boys 
    48: 6465 7365 7276 6520 6d6f 7265 2121 00      deserve more!!.
""" )
        copy = load( d )
        self.assertEqual( copy, orig )

# 9:11:52.81  epscada1 --> mametvista1 UDP:  Length = 13 
# 	   0: 0000 0c07 ac01 0800 20b1 fb6b 0800 4500    ........ ..k..E.
# 	  16: 0021 a0ef 4000 ff11 7b8a 0a41 4050 a18d    .!..@...{..A@P..
# 	  32: 7333 87df 0401 000d d59e 0f00 0003 30   s3............0


if __name__ == "__main__":
    unittest.main()
