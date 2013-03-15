#!/usr/bin/env python

"""
trading		-- Market trading simulation framework
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

from .. import misc 

from exchgs import *

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
    an equilibrium price for all of these, depending on their desirability
    (demand -- how many need it, and how much is needed) and rarity (supply --
    how many produce it, and how much is produced).

    Rather than directly simulating demand and supply to arrive at equilibrium
    prices, and controlling monetary systems to reach equilibrium PPM
    (Purchasing Power of Money), we create simple independent actors that
    actually try to sell the commodities they produce, to build a monetary
    balance, to fulfil their needs.  These commodities in supply and demand by
    independent actors create marketplace price and monetary purchasing power
    equilibrium.


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
    def __init__( self, name=None, balance=0., assets=None, target=None,
                  needs=None, minimum=0., now=None ):
        self.name		= name if name else hex(id(self))
        self.now		= now if now is not None else misc.timer()
        self.dt			= 0.			# The latest tick

        self.trades		= []

        # These are the target levels (if any) and assets holdings
        self.target		= {}			# { 'something': 350, ...}
        if target:
            self.target.update( target )
        self.assets		= {}   			# { 'something': 1000, 'another': 500 }
        if assets:
            self.assets.update( assets )

        self.needs		= needs			# [ need(...), ... ]

        self.balance		= balance		# Credit balance
        self.minimum		= minimum		#  and target minimum

    def record( self, order, comment=None ):
        """
        Buy/sell the specified amount of security, at the given price.  If
        amount is -'ve, then this is a sale.  Selling short, buying on margin is
        allowed.
        """
        self.trades.append( order )
        self.assets.setdefault(order.security, 0)
        logging.info( "%s %5s %6d %10s @ $%7.2f%s" % (
                self.name, "sells" if order.amount < 0 else "buys",
                abs( order.amount ), order.security, order.price,
                ": " + comment if comment else ""))
        self.assets[order.security] += order.amount
        self.balance	       -= order.amount * order.price

    def run( self, exch, now=None ):
        """
        Do whatever this actor does in the market, adjusting any open trades.

        A basic actor has assets, and a list of needs, each with a cycle and
        priority relative to others.  For example, he might sell labor to buy
        food to live.

        The base class does nothing but compute the self.dt since the last run,
        and update self.now, and arrange to acquire the upcoming needs.  As the
        deadline for a need approaches, the urgency to acquire the need
        increases.  Assets that are not needed will be sold, if necessary, to
        supply the needs.

        The basic actor tries to acquire things earlier, at a price below the
        current market rate, if possible.
        """
        last			= self.now
        self.now		= now if now is not None else misc.timer()
        self.dt			= self.now - last

        self.acquire_needs( exch )
        self.cover_balance( exch )
        self.fix_portfolio( exch )

    def acquire_needs( self, exch ):
        """
        Iterate over needs by priority first, then deadline.  The 'target'
        amount is the base amount of the security we must have on hand; when a
        need expires, it is added to target.

        Issue market trade orders for those securities we have an upcoming need
        for, modulating our bid depending on the urgency of the need.

        The target is increased when the need's 
        """
        nl = sorted(self.needs)
        needs = []
        for n in nl:
            # First, see if this need's deadline has arrived; if so, record that
            # the need was expended (eg. food eaten, rent due, ...) by
            # increasing the target for that need, and reschedule the need.
            if self.now < n.deadline:
                needs.append( n )
            else:
                try:    self.target[n.security] += n.amount
                except: self.target[n.security]  = n.amount
                needs.append( need(n.priority, n.deadline + n.cycle, 
                                   n.security, n.cycle, n.amount ))
                logging.info(
                    "%s increased target for %s to %7.2f" % (
                        self.name, n.security, self.target[n.security] ))

            # See if we are short, and try to acquire if so
            short		= (n.amount + self.target.get( n.security, 0 )
                                   - self.assets.get( n.security, 0 ))
            if short <= 0:
                logging.info(
                    "%s has full target of %s" % (self.name, n.security))
            else:
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
                if price is None or misc.near( 0, price ):
                    # No market yet!  Offer 1 cent per unit.
                    offer	= 0.01
                else:
                    offer	= factor * price
                logging.info(
                    "%s needs %d %s; bidding $%7.2f (%7.2f of $%7.2f price)" % (
                        self.name, short, n.security, offer,
                        factor, price if price else misc.nan ))
                # Enter the trade for the required item, updating existing order
                exch.enter( trade( security=n.security, price=offer,
                                           time=self.now, amount=short,
                                           agent=self ),
                            update=True )

    def cover_balance( self, exch ):
        """
        Total up everything we are bidding on, and see if we have enough.  Sell
        something, if not...

        This sums up all open buys and sells!  Basically, the more cash we have
        on hand, the less likely we are to sell assets, and the more we'll
        charge for them.
        """
        value = 0.
        buying = []
        for order in exch.open( self ):
            value	       += order.amount * order.price
            if order.amount > 0:
                buying.append( order.security )

        if value > self.balance:
            # We're trying to buy more stuff than we can afford.  Sell!
            self.raise_capital( value - self.balance, exch, exclude=buying )

    def check_holdings( self, exch, exclude=None ):
        """
        Return the value of our holdings beyond our target levels on
        the given exchange, except those in the exclude list.
        """
        excess 			= {}
        for sec, bal in self.assets.items():
            if exclude and sec in exclude:
                continue
            price		= max( exch.price( sec ))
            if price is None:
                continue
            # There is bidding on this security.  Compute the value of
            # our excess amount of each security we hold.
            excess[sec] = price * (self.assets[sec] - self.target.get( sec, 0 ))
        return excess

    def raise_capital( self, value, exch, exclude=None ):
        """
        Raise cash by selling the assets (not in the exclude list) with the
        greatest excess value, at market rates!

        For anything we are not currently short of, sell small amounts
        at high prices when not in need of cash, and larger amounts at
        lower prices when in need.
        """
        excess = {}
        logging.warning(
            "%s wants to raise an additional $%7.2f; presently has $%7.2f" % (
                self.name, value, self.balance ))

        excess = self.check_holdings( exch, exclude=exclude )

        for sec, val in sorted( excess.items(), lambda sv: -sv[1] ):
            # Sell some of the securities at current market rate (no price) we
            # have the most excess value of, 'til we have enough.  We'll have to
            # guess approximately how many units, because we don't know exactly
            # what the sale price will be.
            overage 		= (self.assets[sec] - self.target.get( sec, 0 ))
            amount 		= min( int( value / excess[sec] ) + 1, overage )
            estimate 		= amount * excess[sec] / overage   # units * $/unit
            print "Sell %d of %d excess %s (worth ~%7.2f) for about %7.2f" % (
                amount, overage, sec, val, estimate  )
            exch.enter( trade( security=sec, price=misc.nan,
                                       time=self.now, amount=-amount,
                                       agent=self ),
                        update=True )
            value 	       -= estimate
            if value <= 0:
                break

    def fix_portfolio( self, exch ):
        """
        The default behaviour is to buy low, and sell high.

        With a commodity backed currency system, when the price of the
        "reference" basket of commodities representing one unit of currency is
        priced above or below its defined value, this is a signal to either sell
        commodities to "too much" currency (ie. at inflated prices, when money
        is too cheap), or buy commodities for "too little" money (in times of
        deflation, where money is too expensive).

        So, we'll use the currency's Inflation index as a signal to either
        acquire or sell commodities into the market.  Since we can't really
        deduce which commodity is overpriced, we'll just sell the ones we have
        the most excess supplies of (and we aren't actively trying to acquire at
        the present time).  This makes sense, because we trust that the credit
        system is going to tighten or ease credit, in general, to quench
        inflation or deflation -- this will effect every commodity, not just the
        one that might be at the root of the in/deflation.
        """
        bases = {
            "alloys": 1.00,
            "energy": 2.00,
            "arrays": 4.00,
            }

        # Compute inflation.  <1.0 --> deflation (prices too low), >1.0 --> inflation
        total 			= 0.
        reference 		= 0.
        for sec, bas in bases.items():
            reference 	       += bas
            price 		= max( exch.price( sec ))
            print "Inflation: %s @%r" % ( sec, price )
            total 	       += price if price is not None else 0.
        inflation 		= total / reference
        print "Inflation == %7.2f" % ( inflation )

        buying 			= {}
        selling 		= {}
        open 			= exch.open( self )
        for order in open:
            if order.amount > 0:
                buying[order.security] = order.amount
            else:
                selling[order.security] = -order.amount

        holdings 		= self.check_holdings( exch )
        print repr( holdings.items() )
        for sec, val in sorted( holdings.items(), key=lambda sv: -sv[1], reverse=True ):
            print "fix: %s: holds %s" % ( sec, val )
            amount 		= 1
            if inflation < 1.0:
                # Prices too low; buy at market!
                exch.enter( trade( security=sec, price=misc.nan,
                                           time=self.now, amount=amount,
                                           agent=self ))
            else:
                # Prices too high; sell into the market; just a bit 
                exch.enter( trade( security=sec, price=misc.nan,
                                           time=self.now, amount=-amount,
                                           agent=self ))
                

                


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
        Produce a certain commodity on a certain cycle, with a certain range of
        output.  Performs all the tasks of a base actor, plus produces
        something, if the actor can meet his needs.

        If he has excess cash, he might expand production.
        """
        super( producer, self ).run( currency, market, now=now )
        
        while self.now >= self.harvested + self.cycle:
            self.harvested     += self.cycle
            produced		= random.uniform( *self.output )
            self.record( trade( security=self.crop, price=0., 
                                amount=produced, now=self.harvested ),
                         "%s harvests %d %s" % ( 
                    self.name, produced, self.crop ))

