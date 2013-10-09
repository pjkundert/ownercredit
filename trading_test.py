import logging
import math
import random
logging.basicConfig(level=logging.INFO)

from misc import near, scale
import trading
import pid
import filtered
import market

def test_market_simple():
    m			= trading.market("grain")
    m.sell( "agent A", 250, 4.00, now=1. )
    m.buy(  "agent B", 500, 4.10, now=2. )
    m.sell( "agent C", 200, 4.00, now=2. )
    m.sell( "agent D", 200, 4.01, now=3. )
    m.sell( "agent E", 100, 4.10, now=5. )
    m.buy(  "agent F",  10, 3.99, now=6. )

    assert len( m.selling ) == 4
    assert near( 4.00, m.selling[0].price )
    assert len( m.buying ) == 2
    assert near( 4.10, m.buying[-1].price )

    print "Buying (pre-execution):"
    for order in m.buying:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )

    print "Selling (pre-execution):"
    for order in m.selling:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )

    print "Executing:"
    trades = list( m.execute( now=6. ))
    assert len( trades ) == 6
    for order in trades:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent D":
            assert near( 4.01, order.price )
        if order.agent == "agent A" or order.agent == "agent C":
            assert near( 4.10, order.price )

    print "Buying:"
    for order in m.buying:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent F":
            assert 10 == order.amount
    assert len( m.buying ) == 1
        
    print "Selling:"
    for order in m.selling:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent D":
            assert near( 4.01, order.price )
            assert -150 == order.amount
        if order.agent == "agent E":
            assert near( 4.10, order.price )
            assert -100 == order.amount
    assert len( m.selling ) == 2

    # Now, try some buying and selling at market price.  We have the following buy/sell books:
    # 
    #    Buying:
    #       agent F:    10      grain @    3.99
    #    Selling:
    #       agent D:  -150      grain @    4.01
    #       agent E:  -100      grain @    4.10
    # 
    # If only one of the sides of the trade is buying/selling at market, the price computation is
    # easy; the market-price trader buys/sells at the price defined by the limit-price trade.
    # 
    # However, if *both* sides are trading at "market", then we need to deduce a price.  The oldest
    # order will still get the advantage; if the seller, he gets the highest current ask price, if
    # the buyer, he pays the lowest current bid price.  Basically, the order takes the price of of
    # the best existing limit-price order of its type.

    m.buy(  "agent G", 20, None, now=7. )
    print "Executing market-limit buy:"
    trades = list( m.execute( now=7. ))
    assert len( trades ) == 2
    for order in trades:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent G" or order.agent == "agent D":
            assert near( 4.01, order.price )
            assert near( 20, abs( order.amount ))
        else:
            assert False and "Invalid agent in trade: %s" % order.agent
    
    print "Buying:"
    for order in m.buying:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
    print "Selling:"
    for order in m.selling:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )

    m.sell( "agent H", 2, None, now=8. )
    print "Executing market-limit sell:"
    trades = list( m.execute( now=8. ))
    assert len( trades ) == 2
    for order in trades:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent H" or order.agent == "agent F":
            assert near( 3.99, order.price )
            assert near( 2, abs( order.amount ))
        else:
            assert False and "Invalid agent in trade: %s" % order.agent

    m.buy(  "agent I", 3, None, now=9. )
    m.sell( "agent J", 3, None, now=10. )
    print "Executing market-limit buy/sell (buyer wins):"
    trades = list( m.execute( now=10. ))
    assert len( trades ) == 2
    for order in trades:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent I" or order.agent == "agent J":
            assert near( 3.99, order.price )
            assert near( 3, abs( order.amount ))
        else:
            assert False and "Invalid agent in trade: %s" % order.agent

    m.sell( "agent K", 3, None, now=11. )
    m.buy(  "agent L", 3, None, now=12. )
    print "Executing market-limit buy/sell (seller wins):"
    trades = list( m.execute( now=10. ))
    assert len( trades ) == 2
    for order in trades:
        print "%10s: %5d %10s @ %7.2f" % ( order.agent, order.amount, order.security, order.price )
        if order.agent == "agent K" or order.agent == "agent L":
            assert near( 4.01, order.price )
            assert near( 3, abs( order.amount ))
        else:
            assert False and "Invalid agent in trade: %s" % order.agent

def test_market_fluctuating():
    # Runs the market along some long-term trend.  At random times, random
    # accelerations are added to the price change velocity.   A PID loop move
    # the price back to the trend.

    assert near(   10.00,      market.linear(    0, 1000, (10.00,1000.00)))
    assert near(  505.00,      market.linear(  500, 1000, (10.00,1000.00)))
    assert near( 1000.00,      market.linear( 1000, 1000, (10.00,1000.00)))

    assert near(   10.00, market.exponential(    0, 1000, (10.00,1000.00)))
    assert near(  257.50, market.exponential(  500, 1000, (10.00,1000.00)))
    assert near( 1000.00, market.exponential( 1000, 1000, (10.00,1000.00)))

    duration		= 1000
    price_interval	= (10.00, 1000.00)
    target		= lambda t: market.exponential( t, duration, price_interval )

    assert near(  1.0, market.normalize( 10.00, target=target( 0.0 )))
    assert near( 10.0, market.normalize( 1.00,  target=target( 0.0 ), reverse=True ))


def test_market_agent():
    m			= trading.market("grain")
    a			= trading.actor( now=0., balance=1000. )
    b			= trading.actor( now=0., assets={"grain":100} )

    # An earlier (or simultaneous) seller sets the price
    m.sell( b, 100, 10., now=1.)
    m.buy(  a,  90, 11., now=1.)
    for order in m.execute():
        order.agent.record( order )
    
    assert near( 10., a.balance )
    assert near( 990., b.balance )
    assert "grain" in a.assets
    assert 10 == b.assets["grain"]
    assert 90 == a.assets["grain"]

    m			= trading.market("grain")
    a			= trading.actor( now=0., balance=1000. )
    b			= trading.actor( now=0., assets={"grain":100} )

    # An earlier buyer sets the price
    m.sell( b, 100, 10., now=1.)
    m.buy(  a,  90, 11., now=0.)
    for order in m.execute():
        order.agent.record( order )
    
    assert near( 100., a.balance )
    assert near( 900., b.balance )
    assert "grain" in a.assets
    assert 10 == b.assets["grain"]
    assert 90 == a.assets["grain"]


def test_exchange():
    """
    Tests trading of multiple markets simultaneously.
    """
    GSE			= trading.exchange( "GSE" )
    actors		= []
    needs		= []
    needs.append( trading.need( priority=1, deadline=3.,
                               security="alloy", cycle=3, amount=4 ))
    needs.append( trading.need( priority=1, deadline=5.,
                               security="energy", cycle=7, amount=2 ))
    needs.append( trading.need( priority=1, deadline=7.,
                               security="arrays", cycle=11, amount=1 ))
                  
    actors.append( trading.actor( balance=1000., needs=needs,
                                  assets={"alloy":    1000}, now=0 ))
    actors.append( trading.actor( balance=1000., needs=needs,
                                  assets={"energy":   1000}, now=0 ))
    actors.append( trading.actor( balance=1000., needs=needs,
                                  assets={"arrays":   1000}, now=0 ))

    for t in range(0,30):
        for a in actors:
            a.run( GSE, now=t )
        for order in GSE.execute( now=t ):
            order.agent.record( order )
        logging.info( "GSE after %d:\n%s" % ( t , repr( GSE )))
