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

# Local modules

import pid
from misc import *

class currency:
    """
    Implements a currency based on a basket of commodities, and computes K over time.
    """

    def __init__(
        self,
        symbol,					# eg. '$'
        label,					# eg. 'USD'
        commodities 		= { },		# The definition of the backing commodities
        basket			= { },		# Reference basket, specifying # Units and Proportion of value
        prices			= { },		# Initial commodity prices
        K			= 0.5,		# Initial credit/wealth ratio
        damping			= 2.0,		# Amplify corrective movement by this factor
        window			= 7*24*60*60,	# Default to 1 week sliding average
        now			= time.time() ):# Initial time (default to seconds)

        """ Establish the fundamentals and initial conditions of the currency.  It will always be
        valued based on the initial proportional relationship between the commodities. """

        self.symbol		= symbol
        self.commodities	= commodities	
        self.reference		= basket

        self.window		= window
        self.epoch		= now

        # Set the initial total value of the currency relative to the
        # basket, and initialize current commodity prices and rolling
        # average, remembering when K and rolling average value was
        # last computed.
        self.price		= self.reference.copy()
        #                           time	value	average	K
        self.trend		= [ ( now,	1.0,	1.0,	K ) ]


    # Returns the current (default) data, or a selected value of K,
    # the relative value of the currency relative to commodity basket
    # price, and last computed time.

    def data( self, which = -1 ):
        return self.trend[which]

    def now( self, which = -1 ):
        return self.data( which )[0]

    def val( self, which = -1 ):
        return self.data( which )[1]

    def avg( self, which = -1 ):
        return self.data( which )[2]

    def K( self, which = -1 ):
        return self.data( which )[3]



    def update(
        self,
        basket			= { },
        now 			= time.time() ):

        """ Adjust currency based on the changes in given basket of commodity prices (may be a
        subset of reference basket), at the given time.  Currently simply implements a linear ratio
        of the 1-window rolling average price vs. the reference commodity basket price.

        You may invoke multiple call to update without computing 'K' or advancing 'self.now()', by
        supplying the argument now <= self.now() """

        # Update current prices from supplied dictionary.  Only use things from the basket
        # which are already in our currency's commodity basket!
        for k,v in basket.items():
            if k in self.price.keys():
                self.price[k]	= v

        if now > self.now():
            # Time has elapsed; updated the value/K trend
            elapsed		= float( now ) - self.now()
            replaced		= elapsed / self.window

            val			= sum( self.reference.values() ) / sum( self.price.values() )

            avg			= max( 0.0, 1.0 - replaced ) * self.avg()
            avg		       += min( 1.0,       replaced ) * val

            K		       	= self.K() - ( avg - val ) * 2

            self.trend.append( ( now, val, avg, K ) )


# The following are only used for testing (if the file is executed directly)

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
    for k,y in data.items():
        draw( win, Oy + y * Sy - Zy, Ox - 10, k )

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
    reserve			= pid.pid( Kpid, Fset, Finp, Li, Lout, now )
    start			= reserve.now


    # GAL -- # -- Galactic Credits
    # Establish the current market prices for commodities

    commodities			= {
        # Commodity	Units	 -of-	Quality	  -at-	Market
        "metal":	( "1t",		"Alloys",	"Market Warpgate"	),
        "energy":	( "1pj", 	"Crystals"	"Market Warpgate"	),
        "arrays":	( "1pf",	"Flops",	"Market Warpgate"	),
        }

    basket			= {
        # Commodity	Price	
        "metal":	  1.00 /   1,	# GAL1.00
        "energy":	  2.00 /   1,	# GAL2.00
        "arrays":	  4.00 /   1,	# GAL4.00
        }

    price			= basket.copy();			# Initial commodity prices

    K				= 0.5
    damping			= 2.0
    window			= 3.0
    gal				= currency( '#', 'GAL', commodities, basket,
                                            K = K, damping = damping,
                                            window = window, now = now )

    # Track the asset price and currency K, value and avg
    trend			= [ ]


    last			= time.time()
    while 1:
        message( win, "Quit [qy/n]?, Timewarp:% 7.2f [W/w], Increment:% 7.2f, Filter setp.:% 7.2f[S/s], value:% 7.2f[V/v]"
                 % ( timewarp, increment, reserve.set.interval, reserve.inp.interval ),
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
                reserve.set.interval += .1
            if chr( input ) == 's':
                reserve.set.interval  = max( 0.1, reserve.set.interval - .1 )

            if chr( input ) == 'V':
                reserve.inp.interval += .1
            if chr( input ) == 'v':
                reserve.inp.interval  = max( 0.1, reserve.set.interval - .1 )

            if chr( input ) == 'W':
                timewarp       += .1
            if chr( input ) == 'w':
                timewarp        = max( 0.1, timewarp - .1 )

            if chr( input ) == 'j':
                goal	        = max(    0, goal - 1. )
            if chr( input ) == 'k':
                goal	        = min( rows, goal + 1. )

            # Adjust Kp
            if chr( input ) == 'P':
                reserve.Kpid	= ( reserve.Kpid[0] + .1, reserve.Kpid[1], reserve.Kpid[2] )
            if chr( input ) == 'p':
                reserve.Kpid	= ( reserve.Kpid[0] - .1, reserve.Kpid[1], reserve.Kpid[2] )

            # Adjust Ki
            if chr( input ) == 'I':
                reserve.Kpid	= ( reserve.Kpid[0], reserve.Kpid[1] + .1, reserve.Kpid[2] )
            if chr( input ) == 'i':
                reserve.Kpid	= ( reserve.Kpid[0], reserve.Kpid[1] - .1, reserve.Kpid[2] )

            # Adjust Kd
            if chr( input ) == 'D':
                reserve.Kpid	= ( reserve.Kpid[0], reserve.Kpid[1], reserve.Kpid[2] + .1 )
            if chr( input ) == 'd':
                reserve.Kpid	= ( reserve.Kpid[0], reserve.Kpid[1], reserve.Kpid[2] - .1 )

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
                       reserve.Kpid[0],
                       reserve.Kpid[1],
                       reserve.I,
                       reserve.Kpid[2],
                       reserve.D ),
                 row = 1 )

        message( win,
                 "now:% 7.2f, K:% 7.2f" % ( gal.now(), gal.K() ),
                 row = 2 )
        
        if ( now > gal.now() ):

            # Time has advanced!  Update the galactic credit with the current commodit prices
            gal.update( price, now )

            data		= price.copy()
            data['K']		= gal.K()
            data['Val']		= gal.val()
            data['Avg']		= gal.avg()

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

