#!/usr/bin/env python

"""
credit.money	-- Basic credit system (money) computations

    Implements basic credit system functionality.
"""

__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__ 				= "$Revision: 1.2 $"
__date__ 				= "$Date: 2006/05/10 16:51:11 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

import time
import copy

# Local modules


def value( basket = { } ):
    """ Compute the total value of a basket of commodities """
    sum					= 0
    for k, v in basket.items():
        sum			       += v
    return sum

class currency:
    """
    Implements a currency based on a basket of commodities, and computes K over time.
    """

    def __init__(
        self,
        symbol,						# eg.  '$'
        commodities 			= { },		# The definition of the backing commodities
        basket				= { },		# Reference basket, with proportional values
        K				= 0.5,		# Initial credit/wealth ratio
        window				= 7*24*60*60,	# Default to 1 week sliding average
        now				= time.time() ):# Initial time (default to seconds)

        """ Establish the fundamentals and initial conditions of the currency.  It will always be
        valued based on the initial proportional relationship between the commodities. """

        self.symbol			= symbol
        self.commodities		= commodities	
        self.reference			= basket
        self.K				= K
        self.window			= window
        self.epoch			= now

        self.computed			= now        	# When was K last computed

        # Compute the initial total value of the basket, and initialize current prices
        self.initial			= value( self.reference )

        self.average			= self.initial
        self.price			= self.reference.copy()

            
    def update(
        self,
        basket				= { },
        now 				= time.time() ):

        """ Adjust currency based on the changes in given basket of commodity prices (may be a
        subset of reference basket), at the given time.  Currently simply implements a linear ratio
        of the 1-window rolling average price vs. the reference commodity basket price.

        You may invoke multiple call to update without computing 'K' or advancing 'computed', by
        supplying the argument now <= computed """

        # Update current prices from supplied dictionary
        for k, v in basket.items():
            self.price[k]		= v

        if now > self.computed:
            elapsed			= now - self.computed
            replaced			= elapsed / self.window
            self.average	       *= max( 0.0, 1.0 - replaced )
            self.average	       += min( 1.0, replaced ) * value( self.price )


