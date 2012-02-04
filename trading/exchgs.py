#!/usr/bin/env python

"""
stock 		-- Market simulation framework
  .market	-- A market in one security
  .exchange	-- Many simultaneous securities markets

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
import itertools
import logging

import misc 


trade = collections.namedtuple( 
    'Trade', [ 
        'security', 
        'price', 
        'time', 
        'amount', 
        'agent',
        ] )


prices = collections.namedtuple(
    'Prices', [
        'bid', 
        'ask',
        'last',
        ] )


# The sell and buy order books are ordered in ascending 'price', and
# opposite 'time' order.  This is because the first entries of the
# sell book are used first, and the last entries of the buy book are
# used first, and we want to ensure that entries with equal prices are
# always consumed in ascending time-order (oldest entry first).

def sell_book_key( order ):
    return ( misc.nan_first( order.price ), -order.time )

def buy_book_key( order ):
    return ( misc.nan_last( order.price ), order.time )


class market( object ):
    """
    Implements a market for the named security.  Attempts to solve the set of trades available for
    completion at the given moment.  The market supports fixed-price (>= $0.00) and market-price
    (None or NaN) bids.

    buying = [
            ("wheat", 4.05,  2.,  500, <agent B>)   # @2. A buy  of 500 bu. at $4.00
            ]

    selling = [
            ("wheat", 4.10,  5., -100, <agent E>)   # @5. A sell of 100 bu. at $4.10
            ("wheat", 4.01,  3., -200, <agent D>)   # @3. A sell of 100 bu. at $4.01
            ("wheat", 4.00,  1., -250, <agent A>)   # @1. A sell of 250 bu. at $4.15
            ("wheat", 4.00,  2., -200, <agent C>)   # @2. A sell of 100 bu. at $4.00
            ]


    This market would use the 2 $4.00 sellers, in time order, then part of the 4.01 seller to
    satisfy the $4.05 buyer.

    When a buyer is matched by a seller, whoever put their order on the market first defines the
    trade price.  The lowest priced and oldest seller gets sold first:

        200/200 @ $4.00 from <agent C>
        250/250 @ $4.00 from <agent A>
         50/200 @ $4.01 from <agent D>

    Market-price orders are always processed before fixed-price orders.
    """
    def __init__( self, name, now=None):
        self.name 		= name
        self.now 		= now if now is not None else misc.timer()
        self.buying 		= []
        self.selling 		= []
        self.lastprice		= 0.
        self.transaction	= 0

    def __repr__( self ):
        return "\n".join([
                "%10s: %5d %10s @ %7.2f" % (
                    order.agent.name, order.amount, order.security, order.price )
                for order in self.buying + self.selling])

    def open( self, agent ):
        """
        Return all currently open trades by this agent.  All trades are returned as a single list;
        buys will have a +'ve amount, sells a -'ve amount.
        """
        return [ order
                 for order in self.buying + self.selling
                 if order.agent is agent ]

    def close( self, agent ):
        """
        Remove all open trades by agent.
        """
        self.buying  = [ order for order in self.buying  if order.agent is not agent ]
        self.selling = [ order for order in self.selling if order.agent is not agent ]

    def buy( self, agent, amount, price=None, now=None, update=True ):
        if now is None:
            now 		= misc.timer()
        self.enter( trade(self.name, price, now, amount, agent ), update=update)

    def sell( self, agent, amount, price=None, now=None, update=True ):
        if now is None:
            now 		= misc.timer()
        self.enter( trade(self.name, price, now, -amount, agent ), update=update)

    def enter( self, order, update=True ):
        """
        Enter a trade order.  If a trade exists (either buy or sell) and update is True, we'll
        replace it (closing all existing trades).  A -'ve amount indicates a sell.

        Sorts orders by price, then time.  Market orders (buy/sell at any price) are sorted to
        appear "before" limit orders in their respective buying/selling order books.  All selling
        amounts remain -'ve!
        """
        if update:
            self.close( order.agent )
        if order.amount >= 0:
            self.buying.append( order )
            self.buying.sort( key=buy_book_key )
        else:
            self.selling.append( order )
            self.selling.sort( key=sell_book_key )

    def price( self ):
        """
        Return the current market price spread; bid, ask and last.  Ignores market-price (one) bids.
        """
        bid			= 0.
        for order in reversed( self.buying ):
            if not misc.non_value( order.price ):
                bid		= order.price
                break
        ask			= 0.
        for order in self.selling:
            if not misc.non_value( order.price ):
                ask		= order.price
                break
        return prices( bid, ask, self.lastprice )

    def execute( self, now=None ):
        """
        Yield all possible trading transactions, adjust books.  Not thread-safe.  Performs
        market-price orders first, sorted by age.  Then, limit-price orders.  Remember that all
        amounts in the selling book are -'ve!
        
        The caller must record the trades with each trade's agent, as appropriate.  Normally, this
        would be something like (assuming 'mkt' is a market object, and the trade.agent supplied has
        a .record method which takes a trade):
        
            for order in mkt.execute():
                order.agent.record( order )
                # ... do other stuff with the order

        Largely ported from fms/fms/markets/continuousorderdriven.py, with handling for market-price
        and limit-price bid/ask added.
        """
        if now is None:
            now			= misc.timer()
        while ( self.buying and self.selling 
                and ( misc.non_value( self.selling[0].price )
                      or misc.non_value( self.buying[-1].price )
                      or self.selling[0].price <= self.buying[-1].price )):
            # Trades available, and lowest seller at or below greatest buyer (or one or both is None
            # or NaN, meaning market price).  If both buyer and seller are trading with market-price orders,
            # then the oldest order gets the advantage; buyers
            # If no limit-price orders exist, then no trade can be made (there is no market).
            amount 		= min( self.buying[-1].amount, -self.selling[0].amount )

            if self.buying[-1].time < self.selling[0].time:
                # Buyer place trade before seller; buyer gets better price
                price 		= self.selling[0].price
                if misc.non_value( price ):
                    # Except if it's a market-price bid; then buyer pays seller's bid price.  If
                    # both are market price, the buyer will get the priority; the best limit-price
                    # bid, or the best ask
                    price	= self.buying[-1].price
                    search	= itertools.chain( reversed( self.buying ), self.selling )
            else:
                # Seller placed trade at/after buyer; seller gets better price
                price 		= self.buying[-1].price
                if misc.non_value( price ):
                    # Except if it's a market-price ask; then seller pays buyer's bid price
                    price	= self.selling[0].price
                    search	= itertools.chain( self.selling, reversed( self.buying ) )
            if misc.non_value( price ):
                # Both are market-price orders; search order gives advantage to the oldest trade
                for order in search:
                    if not misc.non_value( order.price ):
                        price = order.price
                        break
            if misc.non_value( price ):
                # Price is *still* None/NaN: No market exists; cannot trade.
                break

            logging.info( "market %s at %7.2f" % ( self.name, price ))
            self.lastprice 	= price
            self.transaction   += 1

            buyer 		= self.buying[-1].agent
            seller 		= self.selling[0].agent
            if amount == self.buying[-1].amount:
                del self.buying[-1]
            else:
                self.buying[-1] = trade( self.buying[-1].security, self.buying[-1].price,
                                         self.buying[-1].time, self.buying[-1].amount - amount,
                                         self.buying[-1].agent )
            if amount == -self.selling[0].amount:
                del self.selling[0]
            else:
                self.selling[0] = trade( self.selling[0].security, self.selling[0].price,
                                         self.selling[0].time, self.selling[0].amount + amount,
                                         self.selling[0].agent )

            yield trade(self.name, price, now,  amount, buyer) 
            yield trade(self.name, price, now, -amount, seller)


class exchange( object ):
    """
    Implements an exchange comprised of any number of securities markets.  New markes are created as
    required, when trades for a new security are entered.

    Much the same as a market, but most methods require a security name.
    """
    def __init__( self, name ):
        self.name	        = name
        self.markets		= {}

    def __repr__( self ):
        return "\n".join( (repr( m ) for m in self.markets.values()))
        
    def open( self, agent ):
        """
        Yeilds all open orders for the agent, in all markets.
        """
        for mkt in self.markets.values():
            for ord in mkt.open( agent ):
                yield ord

    def buy( self, security, agent, amount, price, now=None, update=True ):
        if security not in self.markets:
            self.markets[security] = market( security )
        self.markets[security].buy( agent, amount, price, now=now, update=update )

    def sell( self, security, agent, amount, price, now=None, update=True ):
        if security not in self.markets:
            self.markets[security] = market( security )
        self.markets[security].buy( agent, amount, price, now=now, update=update )

    def enter( self, order, update=True ):
        if order.security not in self.markets:
            self.markets[order.security] = market( order.security )
        self.markets[order.security].enter( order, update=update )

    def execute( self, now=None ):
        """
        Invoke .execute on each market in the exchange, and yield all the resultant trades.
        """
        for market in self.markets.values():
            for order in market.execute( now=now ):
                yield order

    def price( self, security ):
        if security in self.markets:
            return self.markets[security].price()
        return prices( None, None, None )
