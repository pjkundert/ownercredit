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
from misc import near

def test_near():
    assert     near( 0.5, 0.500001 )
    assert     near( 0.5, 0.50001 )
    assert not near( 0.5, 0.5001 )

    assert     near( 100.5, 100.51 )
    assert not near( 100.5, 100.51, 1.0e-5 )
    assert     near( 100.5, 100.501, 1.0e-5 )


def test_money_create_1():
    
    # What commodities back the currency, and how are they measured and priced?  These commodities
    # are priced in standard Units of a specific quality, delivered at a certain market.  (These are
    # not used right now, so the values you provide are not checked).
    
    commodities			= {
        # Commodity	 Units	 -of-	Quality	  -at-	Market
        "gas":		( "l",		"Unleaded"	"Exxon"	    ),
        "beer":		( "355ml",	"Pilsener",	"7-11"	    ),
        "bullets":	( "9mm",	"Springfield",	"Walmart"   ),
        }

    # What wealth backs each unit of currency, and in what (constant) proportion?  As the prices of
    # these commodities change, the value of the unit of currency fluctuates.  How many units of
    # your currency does this basket of wealth represent?

    multiplier			= 100		# 100 BUX is:
    basket			= {
        # Commodity	Amount	Proportion
        'beer':	       25,		# One for the road, eh!
        'gas':	       50,		# Out to the hunt, and back...
        'bullets':    100,		# Should be enough to bag that Elk!
        }

    # What are the current commodity prices (per unit, specified above)?  These don't really matter
    # individually or proportionally, but the value of 100.00 BUX is always able to purchase the
    # entire basket.  We don't need them, in order to establish the currency, but we'll see later
    # what they are used for.  We'll define them here, so you can see how the basket of commodities
    # corresponds to 100.00 BUX:

    prices			= {
        # Commodity	Price	
        "gas":		  1.00 /   1,	# BUX1.00/ea
        "beer":		  6.00 /   6,	# BUX1.00/ea
        "bullets":	 25.00 / 100,	# BUX0.25/ea
        }

    # BUX, or & (the "antlers" symbol, of course!), are computed based on a the given commodities
    # back, over a rolling average over 3 units of time, beginning at 0.  We'll start with a K of
    # 0.5, and a damping feedback based on 3.0 x any inflation/deflationary error term:
    
    buck			= credit.currency( '&', 'BUX',
                                                   commodities, basket, multiplier,
                                                   K = 0.5, damping = 3.0,
                                                   window = 3.,  now = 0 )

    assert buck.window == 3.
    assert near( buck.basket['beer'],   25 ) # a "suitcase" plus one can of beer is included in the BUX commodity basket; Booya!
    assert buck.now()		== 0
    assert near( buck.inflation(),	1.00 )
    assert near( buck.K(), 		0.5 )


    buck.update( prices, 1 )
    assert near( buck.inflation(),	1.00 )	# No inflation...
    assert near( buck.K(), 		0.5 )	#   hence no change in K!

    # ... later on, back at the ranch ...
    
    # If beer falls in price, and gas rises by the same percentage...
    # Since beer has 1/2 the weighting in BUX as gas, net inflation
    # has occured.

    buck.update( {
        'gas': 		1.10 /   1,	# up   &5.00 /   50 litres
        'beer':		5.40 /   6,	# down &2.50 /   25 cans, woo-hoo!
        'bullets':     25.00 / 100,	# same &0.00 /  100 rounds
        }, 3 )			        #   == &7.50/&100.00 inflation

    # The & has inflated -- the price of the commodities backing it
    # have gone up, the value of BUX has gone down!

    assert buck.now()		== 3
    assert near( buck.total,	      102.50   )
    assert near( buck.inflation(),	1.0250 )
    assert near( buck.K(), 		0.4506 )	# K spikes down to compensate

    stuff			= { 'gas': 5, 'beer': 6 }
    assert near( buck.credit( stuff ),	4.9118 )	# Uh; how much can I get for this can o' gas and 6-pack?

    # Same prices next time unit!   Inflation staying...
    ela = float( 4 ) - buck.now()
    assert near( ela, 			1 )

    buck.update( { }, 4 )
    assert buck.now()		== 4
    assert near( buck.inflation(),	1.0250 )
    assert near( buck.K(), 		0.4396 )	# infl. same, but rate of change slows, K pops back a bit
    assert near( buck.credit( stuff ),	4.7915 )

    # Things go back to normal!  K should stay fixed (after 3 time periods, because we filter
    # input!), because it apparently set things right...  Not everything back the same
    # price, but basket now worth &100.00 again.

    buck.update( {
        'gas': 		0.99 /  1,	# &49.50 /   50 litres
        'beer':		6.12 /  6,	# &25.50 /   25 cans
        }, 5 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4442 )    
    assert near( buck.credit( stuff ),	4.9169 )

    buck.update( { }, 6 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4617 )    

    buck.update( { }, 7 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4829 )

    buck.update( { }, 8 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.5017 )

    buck.update( { }, 9 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4923 )

    buck.update( { }, 10 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4923 )
    assert near( buck.credit( stuff ),	5.4497 )

