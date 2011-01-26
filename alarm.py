#!/usr/bin/env python
__author__ 				= "Perry Kundert (perry@kundert.ca)"
__version__				= "$Revision: 45 $"
__date__ 				= "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "GNU General Public License, Version 3 (or later)"

import time
import misc
import math
import collections
import random



"""
    Alarm state machinery.  May be used to implement arbitrary alarm (and
other value-driven) state machines.

    Each stage of the alarm processes its input values, deduces 0, 1 (or
more) state changes, and outputs the alarm state to the next handler.

    @alarm.delay	# 3. Change states based on time in present state
    @alarm.level	# 2. Change states based on comparing input to levels
    @alarm.ack		# 1. Process acknowledgments
    def nstate_ack_delay( state, value, limits ):
        

    (0) --> (1)
            ^\
           /  \
          /    \
         /      v
       (3)<----(2)

USAGE

    After one or more state variables has changed, you may want to evaluate whether 
an alarm's state has changed.

    


  class 5state_ack( alarm ):
    # Class attributes
    .table={
      'name':[                'severity':[        'ackreqd':[
        "hi hi (ack req'd)",    5,                  True,
        "hi hi",                4,                  False,
        "hi (ack reqd)",        3,                  True,
        "hi",                   2,                  False,
        "normal (ack req'd)",   1,                  True,
        "normal",               0,                  False,
        "lo (ack reqd)",        3,                  True,
        "lo",                   2,                  False,
        "lo lo (ack req'd)",    5,                  True,
        "lo lo",                4,                  False,
      ]                        ]                    ]
    }

    # Instance attributes
    .state    = 
    .sequence = 124

    .history
    .acked=[  .level=[
     123       
     123
    ]


DESIGN

    Each component of the alarm (eg ack, level, timer) has a small
state machine for just its own calculations, probably encoded in its
own code.  The total agregate alarm state is a tuple of the current
state in each sub-machine.  Eg (1,4,0) --> State 1 in ack, state 4 in
level, state 0 in timer.



alarm

    Base class for alarm components, which contains a value type
(eg. misc.value) implementing the descriptor protocol (ie. __get__,
__set__).  Whenever a new value is assigned or accessed, the alarm
chain is re-evaluated in light of the newly updated value, and the
state machine may drive to a new state, triggering zero or more
events.  The value is transparently returned -- the caller is unaware
that all this is occuring.



    self.something = alarm( misc.averaged( ... ))

    self.something = 1
    ...
    self.something = 2

    
    Chain the classes together to form instance factories for complex
state machines.


"""

class alarm( object ):
    __slots__ = [ '_sequence', '_severity' ]

    def __init__( self,
                  obj		= None,
                  *args, **kwargs ):
        self._sequence 		= 0
        self._severity		= 0	# Base severity (normally 0, except for testing)

    def description( self ):
        return [ "seq# %d" % self.sequence(), "sev.: %d" % self.severity() ]

    def __repr__( self ):
        return "<alarm " + ", ".join( self.description() ) + ">"

    def state( self ):
        return ( self._sequence, )

    def severity( self ):
        return ( self._severity )

    def sequence( self ):
        return self._sequence

    def transition( self ):
        self._sequence	       += 1
        return self
    
    def compute( self, *args, **kwargs ):
        """
        Override to compute state transitions, if any, resulting from
        the provided inputs.  We force this base method to be a
        generator, but we never yield any state transitions.
        """
        print "%s.compute( %s )" % ( self.__class__, kwargs )
        assert args == ()
        assert kwargs == {}
        
        raise StopIteration
    	yield self

class ack( alarm ):
    """
    Detect and remember if the underlying alarm increases in severity.
    Require that the state with the greatest unacknowledged severity
    is acked.

      .unacked		The unacked ( sequence, severity ), or None
      .threshold	Severity >= this requires ack

    If we are presently acknowledged (unack[0] == self.sequence()),
    then we will remain acked so long as the severity remains at or
    below the acked severity.

    If we are presently unacknowledged, the sequence number provided
    to ack must exceed the stored sequence number.
    """
    __slots__ = [ 'unacked', 'threshold' ]

    def __init__( self, ack_threshold = 1, **kwargs ):
        """
        Pick off our parameters, if any, passing remaining
        keyword args along to next class' __init__.  Start off acked (no
        sequence number unacknowledged; it is up-to-date)
        """
        super( ack, self ).__init__( **kwargs )
        self.unacked		= ( self._sequence, self._severity )
        self.unacked		= ( self.sequence(), self.severity() )
        self.threshold		= ack_threshold

    def description( self ):
        return super( ack, self ).description() + [ not self.acknowledged() and "ack req'd" or "acked" ]

    def state( self ):
        return ( not self.acknowledged() and 1 or 0, ) + super( ack, self ).state() 

    def severity( self ):
        return super( ack, self ).severity() + ( not self.acknowledged() and 1 or 0 )

    def acknowledged( self ):
        """
        Test if the we are presently deemed to be acknowledged.
        """
        return self.sequence() == self.unacked[0]

    def ack( self, seq ):
        """
        If the provided sequence number is acknowledged, then drive to
        the acknowledged state, returning True.
        """
        if not self.acknowledged():
            if seq > self.unacked[0]:
                self.unacked	= ( self.sequence(), self.severity() - 1 )
            else:
                return False
        return True

    def compute( self, ack_seq = None, **kwargs ):
        """
        Generate a series of state changes, due to the provided
        input arguments.
        """
        print "%s.compute( %s )" % ( self.__class__, kwargs )

        # First, see if we've been acked.  If the state sequence being
        # acknowledged is equal to the unacked sequence number, then
        # yes.
        if not self.acknowledged() and self.ack( ack_seq ):
            trans = self.transition()
            self.unacked	= ( self.sequence(), self.severity() )
            yield trans

        # Next, yield any state transitions produced from the remaining
        # alarm classes that comprise this alarm.  As we see them,
        # test to see if we've met or exceeded our threshold to update/enter
        # our unacked status.
        acked			= self.acknowledged()
        transitions		= super( ack, self ).compute( **kwargs )
        done			= False
        while not done:
            try:
                trans		= transitions.next()
            except StopIteration:
                trans		= None
                done		= True
            if not done:
                yield trans

            print "%s.compute -- yielded: %s" % ( self.__class__, trans )

            # After each transition (and after detecting terminating
            # StopIteration), check if we should update/enter unack.
            sev			= self.severity()
            if not acked:
                if sev >= self.unacked[1]:
                    # Already unacked, and this state is at least as
                    # severe as before; update, so this is the one
                    # that must be acked now!  Attempts to ack
                    # with prior sequence numbers will not work.
                    print "%s.compute -- unacked updated was %s, now %s" % (
                        self.__class__, self.unacked, ( self.sequence()-1, sev ))
                    self.unacked= ( self.sequence()-1, sev )
            else:
                # Presently Acked.  Remain acked, unless severity increases.
                if sev > self.unacked[1] and sev >= self.threshold:
                    # Transition to unacknowledged state, by leaving
                    # the self.unacked[0] sequence in the past...  The
                    # severity will increase by 1 due to being unacked
                    # (but won't yet show), so account for that.
                    print "%s.compute -- trans. unacked, was %s, now %s" % (
                        self.__class__, self.unacked, ( self.sequence(), sev + 1 ))
                    self.unacked= ( self.sequence(), sev + 1 )
                    yield self.transition()
                else:
                    print "%s.compute -- stays    acked, was %s, now %s" % (
                        self.__class__, self.unacked, ( self.sequence(), self.severity()))
                    self.unacked= ( self.sequence(), self.severity() )

'''
class nstate_ack_delay( ack, level, delay ):
    def __init__( self, my_args = None, *args, **kwargs ):
        super( nstate_ack_delay, self ).__init__( self, *args, **kwargs )

    def state( s ):
        """
        Compose our own additional state into the state tuple.
        """
        return ( self._state, ) + super( nstate_ack_delay, self ).state()

    temperature = alarm()




    class value_desc( object ):
        __slots__		= [ '_value' ]
        # Descriptor Protocol
        # 
        #     If an instance of this object is contained in another new-style class,
        # then access/assignment is intercepted.
        #
        def __init__( self ):
            self._value		= None

        def __get__( self, obj, objtype ):
            print "__get__: self == %r, obj == %r, objtype == %r --> %r" % (
                self, obj, objtype, obj.value )
            return self._value
        
        def __set__( self, obj, value ):
            print "__set__: self == %r, obj == %r <-- %r" % (self, obj, value )
            obj.sample( value )

    value = value_desc()

class alarm( object ):
    def __init__( self,
                  obj		= None,
                  *args, **kwargs ):
        self._value		= obj
        self.state 		= None

    def value_get( self ):
        self.compute()
        print "%r.value_get == %r" % ( self, self._value )
        return self._value

    def value_set( self, value ):
        print "%r.value_set = %r" % ( self, value )
        self._value = value
        self.compute()

    def value_del( self ):
        print "%r.value_del" % ( self )
        del self._value

    value 			= property( value_get, value_set, value_del )
            
    def compute( self ):
        """
        Perform state transitions, based on updated self.value
        """
        print "%r.compute" % ( self )
        pass

class ack( alarm ):
    # Class attributes
    .table={
      #             0          1                   2
      'name':     [ "reset",   "ack req'd",        "acked" ],
      'severity': [ 10,        1,                  0       ],
      'ackreqd':  [ False,     True,               False   ],
      'ack':      [ 1,         2,                  1       ],
      }

    def ack( self, *args ):
        if 


class example( object ):
    def __init__(self):
        self._temp = 0
        self._tempalarm = ack_alarm()

    def settemp( self, value ):
        orig = self._temp
        self._temp = value
        self._tempalarm( self._temp, orig )

    def gettemp( self ):
        return self._temp

    temperature = property( gettemp, settemp )

    def update( self ):
        self.temperature = random.uniform( 0.0, 20.0 )
'''
