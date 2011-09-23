#!/usr/bin/env python

"""
stock 		-- Market simulation framework
  .actor	-- A basic actor in a stock market/exchange

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

import collections
import logging

import misc 


need = collections.namedtuple( 
    'Need', [
        'priority', 
        'deadline', 
        'security',
        'cycle', 
        'amount',
        ] )


class actor( object ):
    """
    Each actor produces and/or requires certain amounts of commodities
    (eg. food, goods, housing, labour) per time period.  The market should reach
    an equilibrium price for all of these, depending on their desirability and
    rarity.

    Different commodities have different levels of urgency, and will cause the
    actor to buy or sell at different prices.  For example, food must be sold at
    whatever the market will pay (or it will spoil), and must be bought at
    whatever the market prices it at (or the actor will starve).

    Labour will normally be sold at a certain price level, if the actor has
    excess money to purchase food/housing.  However, if the actor has no money
    for food/housing, the actor will sell labour at whatever the market will
    pay.  An actor with excess money may invest in education, to be able to
    deliver more desirable labour.

    Each time the actor is run, it may go into the market to buy/sell something;
    if other actors are in the market simultaneously with a corresponding
    sell/buy, then a trade may take place.
    """
    def __init__( self, name=None, balance=0., assets=None, needs=None, now=None ):
        self.name		= name if name else hex(id(self))
        self.now		= now if now is not None else misc.timer()
        self.dt			= 0.			# The latest tick

        self.trades		= []
        self.assets		= {}   			# { 'something': 1000, 'another': 500 }
        if assets:
            self.assets.update( assets )
        self.needs		= needs			# [ need(...), ... ]
        self.balance		= balance

    def record( self, order ):
        """
        Buy/sell the specified amount of security, at the given price.  If
        amount is -'ve, then this is a sale.  Selling short, buying on margin is
        allowed.
        """
        self.trades.append( order )
        self.assets.setdefault(order.security, 0)
        logging.info( "%s %5s %6d %10s @ $%7.2f: " % (
                self.name, "sells" if order.amount < 0 else "buys",
                abs( order.amount ), order.security, order.price ))
        self.assets[order.security] += order.amount
        self.balance	       -= order.amount * order.price

    def run( curr, exch, now=None ):
        """
        Do whatever this actor does in the market, adjusting any open trades.

        A basic actor needs to sell labor to buy food to live.  He might lend
        excess cash on the borrowing market.  But in general, his action is to
        buy low, sell high.

        The base class does nothing but compute the self.dt since the last run,
        and update self.now, and arrange to acquire the upcoming needs.  As the
        deadline for a need approaches, the urgency to acquire the need
        increases.  Assets that are not needed will be sold, if necessary, to
        supply the needs.
        """
        last			= self.now
        self.now		= now if now is not None else misc.timer()
        self.dt			= self.now - last
        
        for n in self.needs:
            short		= n.amount - self.assets.get( n.security, 0 )
            if short > 0:
                # Hmm. We're short.  Adjust our offered purchase price based on
                # how much of the need's cycle remains.  If the deadline passes,
                # the difference will go -'ve, and the result will be > 1.  If
                # the deadline is a full cycle (or more) away, the difference
                # will go to 1. (or more), and the result will be < 0.  Convert
                # this into a price factor, ranging from ~10% under to ~5% over
                # current market asking price (greatest of bid, ask and latest).
                proportion	= 1. - ( n.deadline - self.now ) / n.cycle
                factor		= misc.scale( proportion, (0., 1.), (0.90, 1.05))
                price		= max( exch.price( n.security ))
                if lowestprice is None or misc.near( 0, lowestprice ):
                    offer	= 0.01
                else:
                    offer	= factor * lowestprice
                logging.info( "%s needs %d %s; bidding %7.2f" % ( self.name, short, n.security, offer ))
                exch.enter( trade( n.security, price=offer, time=now, amount=short ), update=True )

        # Now, total up what we are bidding, and see if we have enough.  Sell
        # something, if not...  This sums up all open buys and sells!
        value = 0.
        for order in exch.open(self):
            value	       += order.amount * order.price
        if value > self.balance:
            # We're trying to buy more stuff than we can afford.  Sell!
            logging.warning(
                "%s has orders totalling $%7.2f, but only has $%7.2f" % (
                    self.name, value, self.balance ))
                           


class producer( actor ):
    def __init__( self, security, cycle, output,
                  now=None, name=None, balance=0., assets=None ):
        actor.__init__( self, now=now, name=name, balance=balance, assets=assets )
        self.crop		= crop
        self.cycle		= cycle
        self.output		= output

        self.harvested		= self.now

    def run( self, curr, exch, now=None ):
        """
        Produce a certain commodity on a certain cycle, with a certain range of output.
        """
        super( producer, self ).run( currency, market, now=now )
        while self.now >= self.harvested + self.cycle:
            self.harvested     += self.cycle
            produced		= random.uniform( *self.output )
            logging.info( "%s harvests %d %s" % ( 
                    self.name, produced, self.crop ))
            self.record( trade( security=self.crop, price=0., 
                                amount=produced, now=self.harvested ))

