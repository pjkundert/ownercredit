import alarm
import misc
import filtered

def test_alarm():

    a = alarm.ack()
    assert str( a ) == "<alarm seq# 0, sev.: 0, acked>"
    assert ( 0, 0 ) == a.state()
    assert 0 == a.sequence()
    assert 0 == a.severity()

    trans = list( a.compute() )
    assert 0 == len( trans )
    assert 0 == a.sequence()
    assert 0 == a.severity()

    # 

    a._severity = 1
    assert 1 == a.severity()
    trans = list( a.compute() )
    assert str( a ) == "<alarm seq# 1, sev.: 2, ack req'd>"
    assert 1 == len( trans )
    assert 1 == a.sequence()
    assert 2 == a.severity()

    trans = list( a.compute( ack_seq = 1) )
    assert 1 == len( trans )

if __name__=='__main__':
    test_alarm()
