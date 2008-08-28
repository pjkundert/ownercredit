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



class currency:
    """
    Implements a currency based on a basket of commodities, and computes K over time.
    """

    def __init__(
        self,
        symbol,					# eg. '$'
        label,					# eg. 'USD'
        commodities 		= { },		# The definition of the backing commodities
        basket			= { },		# Reference basket, with proportional values
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
        #                                     time	value	average	K
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

        # Update current prices from supplied dictionary
        for k, v in basket.items():
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
