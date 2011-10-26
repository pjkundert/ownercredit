import logging
logging.basicConfig(level=logging.INFO)

from misc import near
import trading


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
