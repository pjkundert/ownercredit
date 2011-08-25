import alarm
import misc
import filtered

def test_ack():

    a = alarm.ack()
    trans = list( a.compute() )
    assert 1 == len( trans )
    assert str( a ) == "<ack seq# 0, sev: 0, acknowledged>"
    assert ( 0, 0 ) == a.state()
    assert 0 == a.sequence()
    assert 0 == a.severity()

    # Increase the (base) severity beyond default threshold (1)
    a._severity = 1
    assert 1 == a.severity()
    trans = list( a.compute() )
    assert str( a ) == "<ack seq# 1, sev: 2, ack required>"
    assert 1 == len( trans )
    assert 1 == a.sequence()
    assert 2 == a.severity()

    # Ack the alarm
    trans = list( a.compute( ack = 1) )
    assert 1 == len( trans )
    assert str( a ) == "<ack seq# 2, sev: 1, acknowledged>"
    trans = list( a.compute( ack= 1) )
    assert 0 == len( trans )
    
    a._severity = 0
    trans = list( a.compute() )
    assert 0 == len( trans )
    a._severity = 1
    trans = list( a.compute() )
    assert 1 == len( trans )
    assert str( a ) == "<ack seq# 3, sev: 2, ack required>"
    a._severity = 0
    trans = list( a.compute() )
    assert 0 == len( trans )
    assert str( a ) == "<ack seq# 3, sev: 1, ack required>"
    trans = list( a.compute( ack = 3 ) )
    assert 1 == len( trans )
    assert str( a ) == "<ack seq# 4, sev: 0, acknowledged>"

def test_level():
    a = alarm.level( level={
            'normal':           .0,
            'hysteresis':       .25,
            'limits':           [-3,-1,1,3]})

    trans = list( a.compute( level=0.0 ))
    assert 1 == len( trans )
    assert 0 == a.severity()
    assert str( a ) == "<level seq# 0, sev: 0, normal>"
    trans = list( a.compute( level=-2 ))
    assert 1 == len( trans )
    assert 2 == a.severity()
    assert str( a ) == "<level seq# 1, sev: 2, lo>"
    trans = list( a.compute( level=-1 ))
    assert 0 == len( trans )
    assert -1 == a.value.level()
    assert 2 == a.severity()
    assert str( a ) == "<level seq# 1, sev: 2, lo>"
    trans = list( a.compute( level=-.74 ))
    assert 1 == len( trans )
    assert 0 == a.value.level()
    assert 0 == a.severity()
    assert str( a ) == "<level seq# 2, sev: 0, normal>"

def test_acklevel():
    a = alarm.acklevel( level={
            'normal':           .0,
            'hysteresis':       .25,
            'limits':           [-3,-1,1,3]})

    
    tritr = iter( a.compute( level=2 ))
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 0, sev: 0, normal, acknowledged>"
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 1, sev: 2, hi, acknowledged>"
    assert True == a.acknowledged()
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 2, sev: 3, hi, ack required>"
    assert False == a.acknowledged()
    assert 0 == len(list( tritr ))
    assert False == a.acknowledged()

    tritr = iter( a.compute( level=3 ))
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 3, sev: 5, hi hi, ack required>"
    assert 0 == len(list( tritr ))

    trans = list( a.compute( ack =3 ))
    assert 1 == len( trans )
    assert str( a ) == "<acklevel seq# 4, sev: 4, hi hi, acknowledged>"
    
def test_positional():
    a = alarm.acklevel( { 
            'threshold': 4 },
                  {
            'normal':           .0,
            'hysteresis':       .25,
            'limits':           [-3,-1,1,3]})

    tritr = iter( a.compute( None, 2 ))
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 0, sev: 0, normal, acknowledged>"
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 1, sev: 2, hi, acknowledged>"
    assert True == a.acknowledged()
    assert 0 == len(list( tritr ))

    tritr = iter( a.compute( None, 3 ))
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 2, sev: 4, hi hi, acknowledged>"
    trans = tritr.next()
    assert str( a ) == "<acklevel seq# 3, sev: 5, hi hi, ack required>"
    assert 0 == len(list( tritr ))

    trans = list( a.compute( 3 ))
    assert 1 == len( trans )
    assert str( a ) == "<acklevel seq# 4, sev: 4, hi hi, acknowledged>"
    
    



if __name__=='__main__':
    test_ack()
    test_level()
    test_acklevel()
