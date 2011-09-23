#!/usr/bin/env python

"""
credit.currency -- Basic credit system currency computations

    Implements basic credit system functionality.

  o Creates a currency based on a basket of commodities
  o Computes inflation/deflation from current commodity prices
  o Increases/decreases credit to drive currency value (prices) back to normal
 
"""

# This file is part of Owner Credit
# 
# Owner Credit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# Owner Credit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Owner Credit.  If not, see <http://www.gnu.org/licenses/>.

__author__                      = "Perry Kundert"
__email__                       = "perry@kundert.ca"
__copyright__                   = "Copyright (c) 2006 Perry Kundert"
__license__                     = "GNU General Public License, Version 2 (or later)"

import math

# Local modules

import pid
import misc
import filtered

class currency( object ):
    """
    Implements a currency based on a basket of commodities, and computes multiplier K over time.

    Each unit of currency retains a specific value over time -- exactly sufficient to buy a specific
    basket of goods.  Since the intrinsic value (price) of these goods may vary over time, the value
    of the currency units will fluctuate with them.  Most currencies would strive to be backed by
    goods that are foundational to the economy in which the currency is traded, making this
    variation invisible to holders of the currency -- the currency will buy, today, exactly what it
    bought years ago, and (more importantly), it will buy exactly what holding the physical basket
    of commodities would buy!

    Therefore, to describe a currency, we specify that so many units of currency corresponds to so
    many units of each commodity.  Then, we adjust one parameters -- the credit ratio "K" -- to keep
    the current value of the currency (as measured by the market price of those commodities -- as
    close to the specified value as possible.

    Specifying 'window' a simple scalar value selects simple averaging of all inflation values
    within the given time window, with equal weighting (not time-weighted).  This is good if new
    commodity values (and hence inflation values) are supplied on a regular basis.  If not,
    specify 'window' as a ( interval, 1.0 ) tuple to select time-weighted averaging.  You will
    gain better average accuracy, at the expense of a slight delay in sensitivity.  You'll want to do
    this especially if you have momentary "spikes" in commodity values that last shorter than the 
    average amount commodity basket sample time.
    """
    def __init__(
        self,
        symbol,                                         # eg. '$'
        label,                                          # eg. 'USD'
        commodities             = None,                 # The definition of the backing commodities
        basket                  = None,                 # Reference basket, specifying amount of wealth
        multiplier              = 1.,                   # How many units of currency does 'basket' represent
        K                       = 0.5,                  # Initial credit/wealth ratio
        Lk                      = ( 0.1, 0.9 ),         # Allowed range of K (math.nan means no limit)
        damping                 = 3.0,                  # Amplify correction by factor (too much: oscillation)
        window                  = 7*24*60*60,           # Default to 1 week average to filter currency value
        now                     = None ):               # Initial time (default to seconds)
        """
        Establish the fundamentals and initial conditions of the currency.  It will always be
        valued based on the initial proportional relationship between the commodities.
        """
        if now is None:
            now                 = misc.timer()

        self.symbol             = symbol
        self.label              = label         
        self.commodities        = commodities or {}     # May be specified later, if desired
        self.basket             = basket or {}          #  ''
        self.multiplier         = multiplier

        # Remember the latest commodity prices and total basket cost; used for computing how much
        # credit can be issued for pledges of any commodities.
        self.price              = { }
        self.total              = 0.

        # Create the PID loop, and pre-load the integral to produce the initial K.  If there is 0
        # error (P term) and 0 error rate of change (D term), then only the I term influences the
        # output.  So, if the next update() supplies prices that show that the value of the currency
        # is 1.0, then the error term will be 0, P and D will remain 0, and I will not change, K
        # will remain at the current value.
        Kp                      = damping
        Ki                      = 0.1
        Kd                      = damping / 2.0
        Kpid                    = ( Kp, Ki, Kd )

        # Hard-limiting output (Lout) to Lk will actually automatically allow the pid.controller to
        # limit the integral too.  It will put an internal "soft" limit on output, because it is the
        # error Integral (sum of errors) tha produces the gross constant output value (the other
        # terms P and D are transient, and immediately cease influencing output when the error
        # disappears).  Then, it'll clamp the momentary "spikes" above/below the provided range Lk,
        # if error is extreme.
        if isinstance( window, misc.value ):
            # A user-supplied filtered value for filtering (moderating) inflation.  Good.
            process             = window
        elif isinstance( window, tuple ):
            print "ownercredit.credit -- upgrade 'window=%r' (weighted linear) keyword arg." % ( window, )
            process             = filtered.weighted_linear( window[0], value = 1.0, now = now )
        else:
            print "ownercredit.credit -- upgrade 'window=%r' (simple average) keyword arg." % ( window, )
            process             = filtered.averaged( window, value = 1.0, now = now )

        self.stabilizer = pid.controller( Kpid = Kpid,
                                          setpoint = 1.0,
                                          process = process,
                                          output = K, Lout = Lk,
                                          now = now )

        #                           time        infl.   K
        self.trend              = [ ( now,      1.0,    K ) ]


    # Returns the current (default) data, or a selected value of K,
    # the relative value of the currency relative to commodity basket
    # price, and last computed time.

    def data( self, which = -1 ):
        return self.trend[which]

    def now( self, which = -1 ):
        """
        The time of the last currency update.
        """
        return self.data( which )[0]

    def inflation( self, which = -1 ):
        """
        The latest inflation factor.
        """
        return self.data( which )[1]

    def K( self, which = -1 ):
        """
        The latest currency credit ratio "K"
        """
        return self.data( which )[2]

    def update(
        self,
        price                   = None,
        now                     = None ):
        """
        Adjust currency based on the changes in given basket of commodity prices (may be a subset of
        reference basket after the initial update), at the given time.  Currently simply implements
        a linear ratio of the 1-window rolling average price vs. the reference commodity basket
        price.

        You may invoke multiple call to update price(s) without computing inflation/'K' or advancing
        'self.now()', by supplying the current time value (eg. now=<currency>.now() ); it is illegal
        to try to move time backwards.  If you supply price updates in this way, the updated prices
        will be applied next time an update is performed with an updated 'now' value, but using the
        previous timestamp for the changed prices.  In other words, prices that have been updated
        using the last timestamp will be deemed to have been changed at the instant of the last
        update's timestamp; the prices supplied to the update will use the current timestamp.
        """
        if now is None:
            now                 = misc.timer()
        if now < self.now():
            raise Exception, "Attempt to update multiple times for previous time period"

        if self.price and now > self.now():
            # Time has advanced, and we have prices (we've been initialized).  If any prices had
            # been changed (due to updates that used the existing timestamp), compute and store an
            # inflation sample so that these price updates appear to have been in effect *since* the
            # last timestamp.
            total               = 0.
            for c,u in self.basket.items():
                total          += u * self.price[c]
            inf                 = total / self.multiplier
            if inf != self.inflation():
                #print "Updating inflation from % 7.2f to % 7.2f due to price changes for now=% 7.2f" % ( self.inflation(), inf, self.now())
                self.stabilizer.process.sample( value=inf, now=self.now() )

        # Update current prices from supplied dictionary, and compute inflation.  We must be
        # supplied a price list which contains all of our currency's commodity basket!  For each
        # item in the basket, get the current price, multiply by the number of units specified by
        # the basket, sum them up, and divide by the currency multiplier (the number of units of
        # currency the basket represents).  This will throw an exception if a commodity isn't
        # supplied (subsequent invocations will use previous price data, if not supplied)

        # Pick out and remember updated price(s), if any, for items in the currency's basket (ignore
        # any commodities not in the currency's basket).  If time has not advanced, this was just a
        # price update; perform no further updating.
        for c,u in self.basket.items():
            if price and c in price:
                self.price[c]   = price[c]

        if now <= self.now():
            return

        # Time has advanced.  Use latest prices to update currency price inflation.  We get the
        # total current price of the basket of commodities comprising the currency, and divide by
        # the basket-to-credit muliplier (now many units of credit are represented by the basket).
        # The result should be 1.0 (no inflation).
        self.total              = 0.
        for c,u in self.basket.items():
            self.total         += u * self.price[c]
        inf                     = self.total / self.multiplier

        # If the basket of commodities has dropped in price (deflation), the total price will have
        # dropped -- value / multiplier will be < 1.0 (driving K up).  If prices have gone up
        # (inflation), the price of the basket has increased, the value of the currency has dropped
        # -- value / multiplier value will be > 1.0 (driving K down).

        # Run the PID loop with current inflation to get an updated value for K.
        K                       = self.stabilizer.loop( 1.0, inf, now )
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

        value                   = 0.
        for c,u in basket.items():
            if c in self.basket.keys():
                value          += u * self.price[c]

        return value * self.K()


###################################################################################################
#
# The following are only used for testing (if the file is executed directly)
# 

           

def draw( win, y, x, s ):
    """ Clip and plot, inverting y """
    rows, cols                  = win.getmaxyx()
    ix                          =  int( x )
    iy                          = -int( y ) + rows - 1
    if iy >= 0 and iy < rows:
        if ix >= 0 and ix < cols:
            win.addstr( iy, ix, s )
            
def xform( win, trans, ry, rx, s  ):
    y                           = ry * trans[0][1]      # Sy
    x                           = rx * trans[1][1]      # Sx
    y                          -= trans[0][2]           # Zy
    x                          -= trans[1][2]           # Zx
    if y < 0 or x < 0:
        # The string is in the margins of the graph
        return
    draw( win, y + trans[0][0], x + trans[1][0], s )    # Oy, Ox

def plot( win, rows, cols, Py, Px, trend ):

   # 1/2 of screen; Compute graph fixed offset, scale and zero point
    Ox                          = 10.
    Oy                          =  5.
    Sx                          = ( cols - Ox ) / ( Px[1] - Px[0] )
    Sy                          = ( rows - Oy ) / ( Py[1] - Py[0] )
    Zx                          = Px[0] * Sx
    Zy                          = Py[0] * Sx

    trans                       = ( ( Oy, Sy, Zy ), ( Ox, Sx, Zx ) )
    
    # Draw the graph grid
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

    # Plot the data, avoiding over-writing by shifting to the right, if necessary.
    data = {} # (last data item in trend, or empty)
    for x,data in trend:
        for k,y in data.items():
            xform( win, trans, y, x, k[0] )

    # Legends and current values
    used = {}
    for k,y in data.items():
        dy                      = int( Oy + y * Sy - Zy )
        while dy in used: dy   += 1
        used[dy]                = True
        draw( win, dy,     Ox - 10, "%s% 6.3f" % ( k[0], y ) )

def message( window, text, row = 23 ):
    window.move( row, 0 )
    window.clrtoeol()
    window.addstr( row, 5, text )

def ui( win, title = "Test" ):
    # Display trends for a credit system based on several commodities

    timewarp                    = 3.0                                   # Slow down real-time by this factor
    increment                   = 1.0                                   # Process no time change increments smaller than this

    Finp                        = 0.                                    # Filter input?
    Fset                        = 1.0                                   #   or setpoint?

    Kpid                        = (    2.0,      1.0,      2.0   )      # PID loop tuning
    Lk                          = (    0.1,      0.9   )                # Limit K to practical values (no zero or infinite credit)
#    Lk                         = ( math.nan, math.nan )
    Li                          = ( math.nan, math.nan )                # Avoid integral wind-up if prices don't respond
#    Li                         = ( math.nan, math.nan )

    now                         = 0.0


    # GAL -- # -- Galactic Credits
    # Establish the current market prices for commodities

    commodities                 = {
        # Commodity     Units    -of-   Quality   -at-  Market
        "metal":        ( "1t",         "Alloys",       "Market Warpgate"       ),
        "energy":       ( "1pj",        "Crystals"      "Market Warpgate"       ),
        "arrays":       ( "1pf",        "Flops",        "Market Warpgate"       ),
        }
    multiplier                  = 1
    basket                      = {
        # Commodity     Amount
        "metal":          1. / 7 / 3,
        "energy":         2. / 7 / 3,
        "arrays":         4. / 7 / 3,
        }

    price                       = {
        # Commodity     Price   
        "metal":          1.00 /   1,   # GAL1.00
        "energy":         2.00 /   1,   # GAL2.00
        "arrays":         4.00 /   1,   # GAL4.00
        }


    K                           = 0.5
    damping                     = 2.0
    gal                         = currency( '#', 'GAL',
                                            commodities, basket, multiplier,
                                            K=K, Lk=Lk, damping=damping,
                                            window=filtered.weighted_linear( 3.0, value=1.0, now=now ),
                                            now=now )

    start                       = gal.now()

    # Track the asset price and currency K, value and avg
    trend                       = [ ]


    last                        = misc.timer()
    while 1:
        message( win, "Quit [qy/n]?, Timewarp:% 7.2f [W/w], Increment:% 7.2f, Filter Interval:% 7.2f[V/v]"
                 % ( timewarp, increment, gal.stabilizer.process.interval ),
                 row = 0 )
        win.refresh()
        input                   = win.getch()

        # New frame of animation
        win.clear()

        # Compute time advance, after time warp.  Advance now only by increments.
        real                    = misc.timer()
        delta                   = ( real - last ) / timewarp
        steps                   = int( delta / increment )
        if steps > 0:
            last               += steps * increment * timewarp
            now                += steps * increment

        if input >= 0 and input <= 255:
            if chr( input ) == 'y' or chr( input ) == 'q':
                break

            if chr( input ) == 'V':
                gal.stabilizer.process.interval += .1
            if chr( input ) == 'v':
                gal.stabilizer.process.interval  = max( 0.1, gal.stabilizer.process.interval - .1 )

            if chr( input ) == 'W':
                timewarp       += .1
            if chr( input ) == 'w':
                timewarp        = max( 0.1, timewarp - .1 )

            if chr( input ) == 'P':
                gal.stabilizer.Kp      += .1
            if chr( input ) == 'p':
                gal.stabilizer.Kp       = max( 0., gal.stabilizer.Kp - .1 )

            if chr( input ) == 'I':
                gal.stabilizer.Ki      += .1
            if chr( input ) == 'i':
                gal.stabilizer.Ki       = max( 0., gal.stabilizer.Ki - .1 )

            if chr( input ) == 'D':
                gal.stabilizer.Kd      += .1
            if chr( input ) == 'd':
                gal.stabilizer.Kd      = max( 0., gal.stabilizer.Kd - .1 )

            if chr( input ) == 'E':
                price['energy'] += .01
            if chr( input ) == 'e':
                price['energy']  = max( 0.0, price['energy'] - .01 )
            if chr( input ) == 'M':
                price['metal']  += .01
            if chr( input ) == 'm':
                price['metal']   = max( 0.0, price['metal'] - .01 )
            if chr( input ) == 'A':
                price['arrays'] += .01
            if chr( input ) == 'a':
                price['arrays']  = max( 0.0, price['arrays'] - .01 )

        if now > gal.now():
            # Time has advanced!  Update the galactic credit with the current commodity prices
            gal.update( price, now=now )

            data                = price.copy()
            data['K']           = gal.K()
            data['Inflation']   = gal.inflation()

            trend.append( ( now, data ) )
        else:
            # Still same time period; just update current prices (in case they changed)
            gal.update( price, now=now )

        #     win, Y,           X,           [ ( x, { 'Y1': y, 'Y2': y ... } ) ]
        rows, cols                  = win.getmaxyx()
        plot( win, rows, cols/2, ( 0., 5.0 ), ( max( 0., now - 20 ), max( 20, now )), trend )

        message( win,
                 "T%+7.2f: ([P/p]: % 8.4f/% 8.4f [I/i]: % 8.4f/% 8.4f [D/d]: %8.4f/% 8.4f)"
                   % ( now - start,
                       gal.stabilizer.Kp if hasattr( gal.stabilizer, "Kp" ) else gal.stabilizer.Kpid[0],
                       gal.stabilizer.P,
                       gal.stabilizer.Ki if hasattr( gal.stabilizer, "Ki" ) else gal.stabilizer.Kpid[1],
                       gal.stabilizer.I,
                       gal.stabilizer.Kd if hasattr( gal.stabilizer, "Kd" ) else gal.stabilizer.Kpid[2],
                       gal.stabilizer.D ),
                 row = 1 )

        message( win,
                 "now:% 7.2f, Inflation: % 7.2f, K:% 7.2f, " % ( gal.now(), gal.inflation(), gal.K() ),
                 row = 2 )
        message( win,
                 "In/decrease commodity values; [Aa]rrays, [Ee]nergy, [Mm]etal; see K change, 'til Inflation restored to 1.0000",
                 row = 3 )

if __name__=='__main__':
    import curses, traceback
    try:        # Initialize curses
        stdscr=curses.initscr()
        curses.noecho() ; curses.cbreak(); curses.halfdelay( 1 )
        stdscr.keypad(1)
        ui( stdscr, title="Credit" )    # Enter the mainloop
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()                 # Terminate curses
    except:
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception

