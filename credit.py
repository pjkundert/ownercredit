#!/usr/bin/env python

"""
credit.money	-- Basic credit system (money) computations

    Implements basic credit system functionality.
"""

__author__ 			= "Perry Kundert (perry@kundert.ca)"
__version__ 			= "$Revision: 1.2 $"
__date__ 			= "$Date: 2006/05/10 16:51:11 $"
__copyright__			= "Copyright (c) 2006 Perry Kundert"
__license__			= "GNU General Public License, Version 3 (or later)"

import time
from math import *

# Local modules

import pid
from misc import *	# math.nan, etc.

class currency:
    """
    Implements a currency based on a basket of commodities, and computes K over time.

    Each unit of currency retains a specific value over time -- exactly sufficient to buy a specific
    basket of goods.  Since the intrinsic value of these goods may vary over time, the value of the
    currency will fluctuate with them.  However, most currencies would strive to be backed by goods
    that are foundational to the economy in which the currency is traded, making this variation
    invisible to holders of the currency -- the currency will buy, today, exactly what it bought
    years ago, and (more importantly), it will buy exactly what holding the physical basket of
    commodities would buy!

    Therefore, to describe a currency, we specify that so many units of currency corresponds to so
    many units of each commodity.  Then, we adjust one parameters -- the credit ratio "K" -- to keep
    the current value of the currency (as measured by the market price of those commodities -- as
    close to the specified value as possible.
    
    """

    def __init__(
        self,
        symbol,						# eg. '$'
        label,						# eg. 'USD'
        commodities 		= { },			# The definition of the backing commodities
        basket			= { },			# Reference basket, specifying # Units and Proportion of value
        multiplier		= 1,			# How many units of currency does 'basket' represent
        K			= 0.5,			# Initial credit/wealth ratio
        Lk			= ( 0.0, math.nan ),	# Allowed range of K (math.nan means no limit)
        damping			= 3.0,			# Amplify corrective movement by this factor (too much: oscillation)
        window			= 7*24*60*60,		# Default to 1 week sliding average to filter currency value
        now			= time.time() ):	# Initial time (default to seconds)

        """ Establish the fundamentals and initial conditions of the currency.  It will always be
        valued based on the initial proportional relationship between the commodities. """

        self.symbol		= symbol
        self.label		= label		
        self.commodities	= commodities.copy()
        self.basket		= basket.copy()
        self.multiplier		= multiplier
        self.window		= window

        # Remember the latest commodity prices and total basket cost; used for computing how much
        # credit can be issued for pledges of any commodities.
        
        self.price		= { }
        self.total		= 0.

        # Create the PID loop, and pre-load the integral to produce the initial K.  If there is 0
        # error (P term) and 0 error rate of change (D term), then only the I term influences the
        # output.  So, if the next update() supplies prices that show that the value of the currency
        # is 1.0, then the error term will be 0, P and D will remain 0, and I will not change, K
        # will remain at the current value.

        #			    P        I        D
        Kpid			= ( damping, 0.1,     damping / 2. )

        self.stabilizer		= pid.pid( Kpid = Kpid,
                                           Finp = window, Lout = Lk,
                                           now = now )
        self.stabilizer.I	= K / self.stabilizer.Kpid[1]

        #                           time	value	K
        self.trend		= [ ( now,	1.0,	K ) ]


    # Returns the current (default) data, or a selected value of K,
    # the relative value of the currency relative to commodity basket
    # price, and last computed time.

    def data( self, which = -1 ):
        return self.trend[which]

    def now( self, which = -1 ):
        return self.data( which )[0]

    def inflation( self, which = -1 ):
        return self.data( which )[1]

    def K( self, which = -1 ):
        return self.data( which )[2]


    def update(
        self,
        price			= { },
        now 			= time.time() ):

        """
        update( price )
        
        Adjust currency based on the changes in given basket of commodity prices (may be a
        subset of reference basket), at the given time.  Currently simply implements a linear ratio
        of the 1-window rolling average price vs. the reference commodity basket price.

        You may invoke multiple call to update without computing 'K' or advancing 'self.now()', by
        supplying the argument now <= self.now()
        """

        if not ( now > self.now()):
            raise Exception, "Attempt to update multiple times for same (or previous) time period"

        # Update current prices from supplied dictionary, and compute inflation.  We must be
        # supplied a price list which contains all of our currency's commodity basket!  For each
        # item in the basket, get the current price, multiply by the number of units specified by
        # the basket, sum them up, and divide by the currency multiplier (the number of units of
        # currency the basket represents).  This will throw an exception if a commodity isn't
        # supplied (subsequent invocations will use previous price data, if not supplied)

        # Pick out and remember any updated price for any item in the currency's basket
        for c,u in self.basket.items():
            if c in price.keys():
                self.price[c]	= price[c]

        # Use latest prices (perhaps from prior updates) to update currency inflation
        self.total		= 0.
        for c,u in self.basket.items():
            self.total	       += u * self.price[c]
        inf			= self.total / self.multiplier

        # If the basket of commodities has dropped in price (deflation), the total price will have
        # dropped -- value / multiplier will be < 1.0 (driving K up).  If prices have gone up
        # (inflation), the price of the basket has increased, the value of the currency has dropped
        # -- value / multiplier value will be > 1.0 (driving K down).

        # Run the PID loop with current inflation to get an updated value for K.
        K			= self.stabilizer.loop( 1.0, inf, now )
        self.trend.append( ( now, inf, K ) )

    def credit( self, basket ):
        """
        credit( basket ) --> amount
    
        Credit available for pledged basket of { 'commodity': units, ... }.  

        Return how much credit the given basket of commodities is worth.  Only the commodities
        represented in the currencies basket are considered, and we must have a price for them
        (ie. after first update(...)).  The amount of credit is based on the latest commodity price,
        and the computed credit factor K.

        Units of each commodity are valued at the latest trading price reported for the commodity.
        Amount of credit issued is value * K.

        We keep no track of the "pledged" commodities; we only report the amount of credit it would
        be worth.

        
        """

        value			= 0.
        for c,u in basket.items():
            if c in self.basket.keys():
                value	       += u * self.price[c]

        return value * self.K()


###################################################################################################
#
# The following are only used for testing (if the file is executed directly)
# 

def draw( win, y, x, s ):
    """ Clip and plot, inverting y """
    rows, cols			= win.getmaxyx()
    ix				=  int( x )
    iy				= -int( y ) + rows - 1
    if iy >= 0 and iy < rows:
        if ix >= 0 and ix < cols:
            win.addstr( iy, ix, s )
            
def xform( win, trans, ry, rx, s  ):
    y				= ry * trans[0][1]	# Sy
    x				= rx * trans[1][1]	# Sx
    y			       -= trans[0][2]		# Zy
    x			       -= trans[1][2]		# Zx
    if y < 0 or x < 0:
        # The string is in the margins of the graph
        return
    draw( win, y + trans[0][0], x + trans[1][0], s )	# Oy, Ox

def plot( win, Py, Px, trend ):
    rows, cols			= win.getmaxyx()

    # Compute fixed offset, scale and zero point
    Ox				= 10.
    Oy				=  5.
    Sx				= ( cols - Ox ) / ( Px[1] - Px[0] )
    Sy				= ( rows - Oy ) / ( Py[1] - Py[0] )
    Zx				= Px[0] * Sx
    Zy				= Py[0] * Sx

    trans			= ( ( Oy, Sy, Zy ), ( Ox, Sx, Zx ) )
    
    #draw( win, 0, 0, "Ox:% 7.2f, Sx:% 7.2f, Px:% 7.2f-% 7.2f, Zx:% 7.2f" % ( Ox, Sx, Px[0], Px[1], Zx ))
    #draw( win, 1, 0, "Oy:% 7.2f, Sy:% 7.2f, Py:% 7.2f-% 7.2f, Zy:% 7.2f" % ( Oy, Sy, Py[0], Py[1], Zy ))

    for x in range( int( Px[0] ), int( Px[1] ) + 1 ):
        if x >    0: draw( win, Oy - 4,      Ox + x * Sx - Zx, str( x /    1 % 10 ) )
        if x >   10: draw( win, Oy - 3,      Ox + x * Sx - Zx, str( x /   10 % 10 ) )
        if x >  100: draw( win, Oy - 2,      Ox + x * Sx - Zx, str( x /  100 % 10 ) )
        if x > 1000: draw( win, Oy - 1,      Ox + x * Sx - Zx, str( x / 1000 % 10 ) )
    for y in range( int( Py[0] ), int( Py[1] ) + 1 ):
        draw( win, Oy + y * Sy - Zy, Ox - 5,   "%4d" % ( y ) )
        for x in range( int( Px[0] ), int( Px[1] ) + 1 ):
            xform( win, trans, y, x, '.' )

    data = {}
    for x,data in trend:
        for k,y in data.items():
            xform( win, trans, y, x, k[0] )

    # Legends and current values
    for k,y in data.items():
        draw( win, Oy + y * Sy - Zy,     Ox - 10, k )
        draw( win, Oy + y * Sy - Zy + 1, Ox - 10, "% 7.4f" % ( y ) )

def message( window, text, row = 23 ):
    window.move( row, 0 )
    window.clrtoeol()
    window.addstr( row, 5, text )

def ui( win, title = "Test" ):
    # Simulate a credit system, with buyers that tend to bid higher when credit is
    # loose, and bid lower when credit is tight.

    rows, cols			= win.getmaxyx()

    timewarp			= 3.0					# Slow down real-time by this factor
    increment			= 1.0					# Process no time change increments smaller than this

    Finp			= 0.					# Filter input?
    Fset			= 1.0					#   or setpoint?

    Kpid			= (    2.0,      1.0,      2.0   )	# PID loop tuning
    Lout			= ( math.nan, math.nan )		# No -'vethrust available, limit +'ve? Causes integral wind-up and overshoot
    Li				= ( math.nan, math.nan )
    Ly				= ( math.nan, math.nan )		# Lauch pad height

    now				= 0.0


    # GAL -- # -- Galactic Credits
    # Establish the current market prices for commodities

    commodities			= {
        # Commodity	Units	 -of-	Quality	  -at-	Market
        "metal":	( "1t",		"Alloys",	"Market Warpgate"	),
        "energy":	( "1pj", 	"Crystals"	"Market Warpgate"	),
        "arrays":	( "1pf",	"Flops",	"Market Warpgate"	),
        }
    multiplier			= 1
    basket			= {
        # Commodity	Amount
        "metal":	  1. / 7 / 3,
        "energy":	  2. / 7 / 3,
        "arrays":	  4. / 7 / 3,
        }

    price			= {
        # Commodity	Price	
        "metal":	  1.00 /   1,	# GAL1.00
        "energy":	  2.00 /   1,	# GAL2.00
        "arrays":	  4.00 /   1,	# GAL4.00
        }


    K				= 0.5
    damping			= 2.0
    window			= 3.0
    gal				= currency( '#', 'GAL',
                                            commodities, basket, multiplier,
                                            K = K, damping = damping,
                                            window = window,
                                            now = now )

    start			= gal.now()

    # Track the asset price and currency K, value and avg
    trend			= [ ]


    last			= time.time()
    while 1:
        message( win, "Quit [qy/n]?, Timewarp:% 7.2f [W/w], Increment:% 7.2f, Filter setp.:% 7.2f[S/s], value:% 7.2f[V/v]"
                 % ( timewarp, increment, gal.stabilizer.set.interval, gal.stabilizer.inp.interval ),
                 row = 0 )
        win.refresh()
        input			= win.getch()

        # New frame of animateion
        win.clear()

        # Compute time advance, after time warp.  Advance now only by increments.
        real			= time.time()
        delta			= ( real - last ) / timewarp
        steps			= int( delta / increment )
        if steps > 0:
            last	       += steps * increment * timewarp
            now		       += steps * increment

        rows, cols		= win.getmaxyx()

        if input >= 0 and input <= 255:
            if chr( input ) == 'y' or chr( input ) == 'q':
                break

            if chr( input ) == 'S':
                gal.stabilizer.set.interval += .1
            if chr( input ) == 's':
                gal.stabilizer.set.interval  = max( 0.1, gal.stabilizer.set.interval - .1 )

            if chr( input ) == 'V':
                gal.stabilizer.inp.interval += .1
            if chr( input ) == 'v':
                gal.stabilizer.inp.interval  = max( 0.1, gal.stabilizer.set.interval - .1 )

            if chr( input ) == 'W':
                timewarp       += .1
            if chr( input ) == 'w':
                timewarp        = max( 0.1, timewarp - .1 )

            # Adjust Kp
            if chr( input ) == 'P':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0] + .1, gal.stabilizer.Kpid[1], gal.stabilizer.Kpid[2] )
            if chr( input ) == 'p':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0] - .1, gal.stabilizer.Kpid[1], gal.stabilizer.Kpid[2] )

            # Adjust Ki
            if chr( input ) == 'I':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0], gal.stabilizer.Kpid[1] + .1, gal.stabilizer.Kpid[2] )
            if chr( input ) == 'i':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0], gal.stabilizer.Kpid[1] - .1, gal.stabilizer.Kpid[2] )

            # Adjust Kd
            if chr( input ) == 'D':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0], gal.stabilizer.Kpid[1], gal.stabilizer.Kpid[2] + .1 )
            if chr( input ) == 'd':
                gal.stabilizer.Kpid	= ( gal.stabilizer.Kpid[0], gal.stabilizer.Kpid[1], gal.stabilizer.Kpid[2] - .1 )

            if chr( input ) == 'E':
                price['energy']	+= .01
            if chr( input ) == 'e':
                price['energy']	 = max( 0.0, price['energy'] - .01 )
            if chr( input ) == 'M':
                price['metal']	+= .01
            if chr( input ) == 'm':
                price['metal']	 = max( 0.0, price['metal'] - .01 )
            if chr( input ) == 'A':
                price['arrays']	+= .01
            if chr( input ) == 'a':
                price['arrays']	 = max( 0.0, price['arrays'] - .01 )


        message( win,
                 "T%+7.2f: ([P/p]: % 8.4f [I/i]: % 8.4f/% 8.4f [D/d]: %8.4f/% 8.4f)"
                   % ( now - start,
                       gal.stabilizer.Kpid[0],
                       gal.stabilizer.Kpid[1],
                       gal.stabilizer.I,
                       gal.stabilizer.Kpid[2],
                       gal.stabilizer.D ),
                 row = 1 )

        message( win,
                 "now:% 7.2f, K:% 7.2f" % ( gal.now(), gal.K() ),
                 row = 2 )
        message( win,
                 "In/decrease commodity values; [Aa]rrays, [Ee]nergy, [Mm]etal; see K change, 'til Inflation restored to 0.0000",
                 row = 3 )
        if ( now > gal.now() ):

            # Time has advanced!  Update the galactic credit with the current commodit prices
            gal.update( price, now )

            data		= price.copy()
            data['K']		= gal.K()
            data['Inflation']	= gal.inflation()

            trend.append(  ( now, data ))

        #     win, Y,           X,           [ ( x, { 'Y1': y, 'Y2': y ... } ) ]
        plot( win, ( 0., 5.0 ), ( max( 0., now - 20 ), max( 20, now )), trend )

if __name__=='__main__':
    import curses, traceback
    try:        # Initialize curses
        stdscr=curses.initscr()
        curses.noecho() ; curses.cbreak(); curses.halfdelay( 1 )
        stdscr.keypad(1)
        ui( stdscr, title="Rocket" )        # Enter the mainloop
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()                 # Terminate curses
    except:
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception

