#!/usr/bin/env python

"""
Implements tests for the credit module.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision: 1.2 $"
__date__ 				= "$Date: 2006/05/10 16:51:11 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

# local modules
import credit

def near( a, b, significance = 1.0e-4 ):
    return abs( a - b ) <= significance * ( a and a or b )

def test_near():
    assert not near( 0.5, 0.5001 )
    assert     near( 0.5, 0.500001 )
    assert     near( 0.5, 0.50001 )

def test_money_create_1():
    commodities				= {
        # Commodity	Units	 -of-	Quality	  -at-	Market
        "beer":		( "355ml",	"Pilsener",	"7-11"	    ),
        "bullets":	( "9mm",	"Springfield",	"Walmart"   ),
        "gas":		( "1l", 	"Unleaded"	"Esso"	    ),
        }

    basket				= {
        # Commodity	Price	
        "gas":		  1.0 /   1,	# BUX1.00
        "beer":		  6.0 /  12,	# BUX0.50
        "bullets":	 25.0 / 100,	# BUX0.25
        }

    # BUX are computed based on a the given commodities back, over a
    # rolling average over 5 units of time, beginning at 0
    buck				= credit.currency( 'BUX', commodities, basket, 0.5, 5, 0 )

    assert buck.K 			== 0.5
    assert buck.reference['beer'] 	== 0.5
    assert buck.initial 		== 1.75
    
    # If beer falls in price, and gas rises...
    buck.update( {
        'beer':		6.60 / 12,
        'gas': 		1.15 /  1,
        }, 3 )

    assert buck.reference['beer'] 	== 0.50
    assert near( buck.price['beer'],	0.55 )

    assert buck.average			== 1.2
    
