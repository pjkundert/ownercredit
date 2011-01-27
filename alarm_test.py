import alarm
import misc
import filtered

def test_ack():

    a = alarm.ack()
    assert str( a ) == "<alarm seq# 0, sev.: 0, acked>"
    assert ( 0, 0 ) == a.state()
    assert 0 == a.sequence()
    assert 0 == a.severity()

    trans = list( a.compute() )
    assert 0 == len( trans )
    assert 0 == a.sequence()
    assert 0 == a.severity()

    # Increase the (base) severity beyond threshold
    a._severity = 1
    assert 1 == a.severity()
    trans = list( a.compute() )
    assert str( a ) == "<alarm seq# 1, sev.: 2, ack req'd>"
    assert 1 == len( trans )
    assert 1 == a.sequence()
    assert 2 == a.severity()

    # Ack the alarm
    trans = list( a.compute( ack_seq = 1) )
    assert 1 == len( trans )
    assert str( a ) == "<alarm seq# 2, sev.: 1, acked>"
    trans = list( a.compute( ack_seq = 1) )
    assert 0 == len( trans )
    
    a._severity = 0
    trans = list( a.compute() )
    assert 0 == len( trans )
    a._severity = 1
    trans = list( a.compute() )
    assert 1 == len( trans )
    assert str( a ) == "<alarm seq# 3, sev.: 2, ack req'd>"
    a._severity = 0
    trans = list( a.compute() )
    assert 0 == len( trans )
    assert str( a ) == "<alarm seq# 3, sev.: 1, ack req'd>"
    trans = list( a.compute( ack_seq = 3 ) )
    assert 1 == len( trans )
    assert str( a ) == "<alarm seq# 4, sev.: 0, acked>"

def test_level():
    a = alarm.level( leval_normal=0.0, level_hysteresis=.25,
                     level_limits=[-3,-1,1,3] )

    trans = list( a.compute( level_value=0.0 ))
    assert 0 == len(trans)
    assert 0 == a.severity()
    assert str( a ) == "<alarm seq# 0, sev.: 0, normal>"
    trans = list( a.compute( level_value=-2 ))
    assert 1 == len(trans)
    assert 2 == a.severity()
    assert str( a ) == "<alarm seq# 1, sev.: 2, lo>"
    trans = list( a.compute( level_value=-1 ))
    assert 0 == len(trans)
    assert -1 == a.value.level()
    assert 2 == a.severity()
    assert str( a ) == "<alarm seq# 1, sev.: 2, lo>"
    trans = list( a.compute( level_value=-.74 ))
    assert 1 == len(trans)
    assert 0 == a.value.level()
    assert 0 == a.severity()
    assert str( a ) == "<alarm seq# 2, sev.: 0, normal>"

'''
class acklevel( alarm.ack, alarm.level ):
    pass

def test_acklevel():
    a = alarm.level( leval_normal=0.0, level_hysteresis=.25,
                     level_limits=[-3,-1,1,3] )
    
'''

if __name__=='__main__':
    test_ack()
    test_level()
    #test_acklevel()
