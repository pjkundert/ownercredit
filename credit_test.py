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
        "beer":		( "355ml",	"Pilsner",	"7-11"	    ),
        "bullets":	( "9mm",	"Springfield",	"Walmart"   ),
        }

    # What amount of wealth backs each unit of currency, and in what (constant) proportion?  As the
    # prices of these commodities change, the value of the unit of currency fluctuates.  How many
    # units of your currency does this basket of wealth represent?

    multiplier			= 100		# 100 BUX is:
    basket			= {
        # Commodity	Amount
        'beer':	         25,		# (cans)   A "suitcase" plus one for the road, eh!  Booya!
        'gas':	         50,		# (litres) Out to the cut line, and back...
        'bullets':      100,		# (rounds) Should be enough to bag that Elk!
        }

    # What are the current commodity prices (per unit, specified above)?  These don't really matter
    # individually or proportionally, but the value of 100.00 BUX is always able to purchase the
    # entire basket.  We don't need these yet (in order to establish the currency), but we'll see
    # later what they are used for.  We'll define them here, so you can see how the above basket of
    # commodities corresponds (at current prices) to 100.00 BUX:

    prices			= {
        # Commodity	 Price (represented per standard sales multiple, for ease of understanding)
        "gas":		  1.00 /   1,	# BUX1.00/ea
        "beer":		  6.00 /   6,	# BUX1.00/ea
        "bullets":	 25.00 / 100,	# BUX0.25/ea
        }

    # BUX, or & (the "antlers" symbol, of course!), are computed based on a the given commodities
    # basket, over a rolling average over 3 units of time, beginning at time 0.  We'll start with a
    # K of 0.5, and a damping feedback based on 3. x any inflation/deflationary error term:
    
    buck			= credit.currency( '&', 'BUX',
                                                   commodities, basket, multiplier,
                                                   K = 0.5, damping = 3.,
                                                   window = 3.,  now = 0 )

    assert buck.window == 3.
    assert near( buck.basket['beer'],   25 )
    assert buck.now()		== 0
    assert near( buck.inflation(),	1.00 )
    assert near( buck.K(), 		0.5 )


    buck.update( prices, 1 )
    assert near( buck.inflation(),	1.00 )	# No inflation...
    assert near( buck.K(), 		0.5 )	#   hence no change in K!

    # ... later on, back at the ranch ...
    
    # If beer falls in price, and gas rises by the same percentage...  Since beer has 1/2 the
    # weighting in BUX as gas, net inflation has occured.

    buck.update( {
        'gas': 		1.10 /   1,	# up   &5.00 /   50 litres
        'beer':		5.40 /   6,	# down &2.50 /   25 cans, woo-hoo!
        'bullets':     25.00 / 100,	# same &0.00 /  100 rounds
        }, 3 )			        #   == &7.50/&100.00 inflation

    # The & has inflated -- the price of the commodities backing it have gone up, the value of BUX
    # has gone down!

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
    assert near( buck.K(), 		0.40125)	# infl. same, but rate of change slows, K pops back a bit

    assert near( buck.credit( stuff ),	4.3736 )

    # Things go back to normal!  K should stay fixed (after 3 time periods, because we filter input
    # over a 'window' of 3. time units!), because it apparently set things right...  Not everything
    # back the same price, but basket now worth &100.00 again.

    buck.update( {
        'gas': 		0.99 /  1,	# &49.50 /   50 litres
        'beer':		6.12 /  6,	# &25.50 /   25 cans
        }, 5 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4558 )    

    assert near( buck.credit( stuff ),	5.0461 )

    buck.update( { }, 6 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4800 )    

    buck.update( { }, 7 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.5050 )

    buck.update( { }, 8 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4925 )

    buck.update( { }, 9 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4925 )

    buck.update( { }, 10 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4925 )

    assert near( buck.credit( stuff ),	5.4519 )

    # 
    # ############################################################################
    # 
    # Now, try the same test, but with time-weighted filtering over 3. time units,
    # beginning with an initial value of 1. for Inflation.
    # 

    buck			= credit.currency( '&', 'BUX',
                                                   commodities, basket, multiplier,
                                                   K = 0.5, damping = 3.0,
                                                   window = ( 3., 1. ),  now = 0 )

    assert buck.window == ( 3., 1. )
    assert near( buck.basket['beer'],   25 )
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
    assert near( buck.K(), 		0.5000 )	# K (will) spike down to compensate, after 
    #                               was 0.4506 above
    stuff			= { 'gas': 5, 'beer': 6 }
    assert near( buck.credit( stuff ),	5.4500 )	# Uh; how much can I get for this can o' gas and 6-pack?
    #                               was 4.9118 above
    # Same prices next time unit!   Inflation staying...
    ela = float( 4 ) - buck.now()
    assert near( ela, 			1 )

    buck.update( { }, 4 )
    assert buck.now()		== 4
    assert near( buck.inflation(),	1.0250 )
    assert near( buck.K(), 		0.4617 )	# infl. same, but rate of change slows, K pops back a bit
    #                               was 0.40125above
    assert near( buck.credit( stuff ),	5.03217 )
    #                               was 4.3736 above
    # Things go back to normal!  K should stay fixed (after 3 time periods, because we filter input
    # over a 'window' of 3.0 time units!), because it apparently set things right...  Not everything
    # back the same price, but basket now worth &100.00 again.

    buck.update( {
        'gas': 		0.99 /  1,	# &49.50 /   50 litres
        'beer':		6.12 /  6,	# &25.50 /   25 cans
        }, 5 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4350 )
    #                               was 0.4558 above
    assert near( buck.credit( stuff ),	4.8155 )
    #                               was 5.0461 above
    buck.update( { }, 6 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4458 )
    #                               was 0.4800 above
    buck.update( { }, 7 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4825 )
    #                               was 0.5050 above
    buck.update( { }, 8 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.5075 )
    #                               was 0.4925 above
    buck.update( { }, 9 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4950 )
    #                               was 0.4925 above
    buck.update( { }, 10 )
    assert near( buck.inflation(), 	1.00 )
    assert near( buck.K(), 		0.4950 )
    #                               was 0.4925 above
    assert near( buck.credit( stuff ),	5.4797 )
    #                               was 5.4519 above

    # We stabilize after timestamp 10, whereas the simple averaging
    # test above stabilizes after timestamp 9, due to the fact we
    # skipped a commodity basket sample at timestamp 2; Since the
    # time-weighted average includes the initial (uninflated) basket
    # sample at timestamp 1 with twice the weight (since it persisted
    # for 2 periods), the sensation of inflation was lessened in the
    # second time-weighted test, and hence K was driven down less
    # aggressively (to 0.4950, vs. further down to 0.4925 in the first
    # test).
    # 
