#!/usr/bin/env python
__author__                              = "Perry Kundert (perry@kundert.ca)"
__version__                             = "$Revision: 45 $"
__date__                                = "$Date: 2008-09-07 16:29:06 -0600 (Sun, 07 Sep 2008) $"
__copyright__                           = "Copyright (c) 2006 Perry Kundert"
__license__                             = "GNU General Public License, Version 3 (or later)"

import collections
import logging
import math
import random
import time

import filtered
import misc



"""
    Alarm state machinery.  May be used to implement arbitrary alarm (and other value-driven) state
machines.  Multiple such state machines may be composed, resulting in an alarm with a
multi-dimensinal state coordinate, containing the individual state of each sub-alarm.

USAGE

    After one or more input variables has changed, you may want to evaluate whether an alarm's state
has changed.


DESIGN

    Each component of the alarm (eg ack, level, timer) has a small state machine for just its own
calculations, probably encoded in its own code.  The total agregate alarm state is a tuple of the
current state in each sub-machine.  Eg (1,4,0) --> State 1 in ack, state 4 in level, state 0 in
timer.


"""

def process( transitions ):
    """
    Process and discard a sequence of alarm notifications:

        process( notify( a.compute(), logging.info ))

    """
    for trans in transitions:
        pass

def notify( transitions, logger ):
    """
    A generator taking a sequence of alarm transitions, logs them, and then re-yields them:

        transitions = notify( a.compute(), logging.info )
        for trans in transitions:
            ...
    """
    for trans in transitions:
        logger( trans.message() )
        yield trans


class alarm( object ):
    """
    Base class for alarm components.

    Each alarm state transition is deemed to occur at an instant in time; the beginning of the
    compute(), or the moment the thread returned from the last transition()'s yeild marks the new()
    time for the next alarm state.  This is the "now" moment, which should be used by all state
    transition computations during the compute, and by any code receiving the alarm state yield
    results.
    
    Here's an example stack of compute() calls, with some resulting transitions.

  real  alarm
  time  .now()
     1      1 compute           acklevel  Initial entry defines initial now()
     2          compute         ack       First invokes super().compute...
     3          compute         level     First invokes super().compute...
     4            compute       alarm     Does nothing
     6      1     transition    level     Trans from "normal" to "hi", advance now
     7      6   transition      ack       Trans from "acked" to "ack req'd", advance now
     8      7 (done)                      Return from compute, leaving now at 7
    """
    def __init__( self,
                  obj           = None,
                  *args, **kwargs ):
        self._sequence          = -1    # Force initial transition
        self._severity          = 0     # Base severity (normally 0, except for testing)
        self._now               = None

    def description( self ):
        return [ "seq# %d" % self.sequence(), "sev: %d" % self.severity() ]

    def __repr__( self ):
        return "<%s " % self.__class__.__name__ + ", ".join( self.description() ) + ">"

    def state( self ):
        return ( self._sequence, )

    def severity( self ):
        return ( self._severity )

    def sequence( self ):
        return self._sequence

    def now( self, now=None ):
        """
        Return (and possibly update) the present alarm time.
        """
        if self._now is None or now is not None:
            # Forced update, due to initial state or a recent transition(), or caller providing a
            # new 'now' time.
            if now is None:
                now             = time.time()
            self._now           = now
        return self._now

    def message( self ):
        """
        Return the state change notification message for this type of alarm.  Override in derived
        class to replace (or append to) the default output.
        """
        return "%s: Seq# %5d Sev: %2d" % (
            time.ctime( self.now() ),
            self.sequence(),
            self.severity() )

    # ----------------------------------------------------------------------------
    # State Transition Generator 
    # 
    #     Each alarm state transition generated during self.compute() must yield the results of
    # self.transition(), and invoke self.advance() immediately following the yield:
    #  
    #     trans = self.transition()
    #     yield trans
    #     self.advance()
    # 
    # Whenever we just pass along transitions generated somewhere else, we do not issue a
    # self.advance(); the initiator of the transition will will do so.
    # 

    def transition( self ):
        """
        A transition has occured; advance sequence() numbering immediately.  The caller will be
        yielding this soon.
        """
        self._sequence         += 1
        return self

    def advance( self ):
        """
        After yielding a new alarm state transition (and all resultant processing due to that state
        change is complete), invalidates the now() time.  This will force it to be updated the next
        time it is accessed.
        """
        self._now               = None

    def compute( self, *args, **kwargs ):
        """
        Override to compute state transitions, if any, resulting from the provided inputs.  We only
        ever generate the initial boot-up transition.
        """
        assert () == args
        if 0 == kwargs.pop( '__depth', 0 ):
            self.advance()
        assert {} == kwargs
        if self._sequence < 0:
            yield self.transition()
            self.advance()
        raise StopIteration

class ack( alarm ):
    """
    Detect and remember if the underlying alarm increases in severity.  Require that the state with
    the greatest unacknowledged severity is acked.

      .unacked          The unacked ( sequence, severity ), or None
      .threshold        Severity >= this requires ack

    If we are presently acknowledged (unack[0] == self.sequence()), then we will remain acked so
    long as the severity remains at or below the acked severity.

    If we are presently unacknowledged, the sequence number provided to ack must exceed the stored
    sequence number.
    """
    def __init__( self, *args, **kwargs ):
        """
        Pick off our parameters, if any, passing remaining args along
        to next class' __init__.  Start off acked (no sequence number
        unacknowledged; it is up-to-date)
        """
        if args:
            arg, args   = args[0], args[1:]
        else:
            arg         = kwargs.pop( 'ack', None )
        super( ack, self ).__init__( *args, **kwargs )
        threshold       = ( arg and arg or {} ).pop( 'threshold', 1 )
        if threshold is not None:
            self.threshold      = threshold
        assert not arg

        self.unacked            = ( self._sequence, 0 ) # Boostrap...
        self.unacked            = ( self._sequence, self.severity() )

    def description( self ):
        return super( ack, self ).description() + [self.acknowledged()
                                                   and "acknowledged"
                                                   or  "ack required"]

    def message( self ):
        return super( ack, self ).message() \
            + ( self.acknowledged()
                and " acknowledged"
                or  " ack required" )

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
        the acknowledged state, returning True.  A None is ignored.
        """
        if not self.acknowledged():
            if seq is not None and seq > self.unacked[0]:
                self.unacked    = ( self.sequence(), self.severity() - 1 )
            else:
                return False
        return True

    def compute( self, *args, **kwargs ):
        """
        Generate a series of state changes, due to the provided input arguments.  Any provide
        positional arg (or an 'ack' keyword arg) is assumed to be an acknowledgement sequence number
        (None ==> no acknowledgement)
        """
        if 0 == kwargs.setdefault( '__depth', 0 ):
            self.advance()
        kwargs['__depth']      += 1

        if args:
            arg, args   = args[0], args[1:]
        else:
            arg         = kwargs.pop( 'ack', None )

        # First, see if we've been acked.  If the state sequence being acknowledged is equal to the
        # unacked sequence number, then yes.
        if not self.acknowledged() and self.ack( arg ):
            trans = self.transition()
            self.ack( self.sequence() )
            #print "%s.compute -- yielding: %s" % ( "ack", trans )
            yield trans
            self.advance()

        # Next, yield any state transitions produced from the remaining alarm classes that comprise
        # this alarm.  As we see them, test to see if we've met or exceeded our threshold to
        # update/enter our unacked status.
        acked                   = self.acknowledged()
        transitions             = super( ack, self ).compute( *args, **kwargs )
        done                    = False
        while not done:
            # Determine whether we are acked before making next transition
            acked = self.acknowledged()

            try:
                trans           = transitions.next()
            except StopIteration:
                trans           = None
                done            = True
            if not done:
                # Yield the transition, maintaining acked state; we'll decide below whether or not
                # to make a transition to unacked...
                if acked:
                    self.unacked= ( self.sequence(), self.unacked[1] )
                #print "%s.compute -- yielding: %s" % ( "ack", trans )
                yield trans

            # After each transition (and after detecting terminating StopIteration), check if we
            # should update/enter unack.
            sev                 = self.severity()
            if not acked:
                if sev >= self.unacked[1]:
                    # Already unacked, and this state is at least as severe as before; update, so
                    # this is the one that must be acked now!  Attempts to ack with prior sequence
                    # numbers will not work.

                    #print "%s.compute -- unacked updated was %s, now %s" % (
                    #    "ack", self.unacked, ( self.sequence()-1, sev ))
                    self.unacked= ( self.sequence()-1, sev )
            else:
                # Presently Acked.  Remain acked, unless severity increases.
                if sev > self.unacked[1] and sev >= self.threshold:
                    # Severity increased across threshold; Transition to unacknowledged state, by
                    # leaving the self.unacked[0] sequence in the past...  The severity will
                    # increase by 1 due to being unacked (but won't yet show), so account for that.

                    #print "%s.compute -- transition to unacked, was %s, now %s" % (
                    #    "ack", self.unacked, ( self.sequence(), sev + 1 ))
                    self.unacked= ( self.sequence(), sev + 1 )
                    trans = self.transition()
                    #print "%s.compute -- yielding: %s" % ( "ack", trans )
                    yield trans
                    self.advance()
                else:
                    # Severity stayed same, or lowered.  Remain acked.

                    #print "%s.compute -- stays    acked, was %s, now %s" % (
                    #    "ack", self.unacked,
                    #    ( self.sequence(), sev ))
                    self.unacked= ( self.sequence(), sev )

class level( alarm ):
    """
    Detect when a value passes various levels.  Uses the filtered.level class to implement.  Default
    severity multiplies the number of levels away from "normal" by 2; eg. normal==>0, lo==>2,
    hi-hi==>4.
    """
    def __init__( self, *args, **kwargs ):
        """
        Pick off our configuration parameters, if any, passing remaining args along to next class'
        __init__.  Take the next positional arg (to support configuring alarms with multiple level
        base classes), or a keyword arg.  Since we expect keyword args with the same name as our
        class, we'll have to pick them out of kwargs manually (to avoid overriding our class
        name)...

        We allow either an instance of filtered.level, or a dict of keyward args to configure a new
        one (None ==> defaults)
        """
        if args:
            arg, args   = args[0], args[1:]
        else:
            arg         = kwargs.pop( 'level', None )
        super( level, self ).__init__( *args, **kwargs )
        if isinstance( arg, filtered.level ):
            self.value  = arg
        else:
            self.value          = filtered.level( **( arg and arg or {} ))
        # Memory of last-known level; external events may be driving the filtered.level, and we
        # don't want to miss changes.
        self.before     = self.value.level()

    def description( self ):
        return super( level, self ).description() + [self.value.name()]

    def message( self ):
        return super( level, self ).message() \
            + "%9.3f ==> %-8s" % ( 
                self.value, self.value.name() )

    def state( self ):
        return ( self.value.state(), ) \
               + super( level, self ).state()

    def severity( self ):
        return super( level, self ).severity() \
                 + 2 * abs(self.value.level())

    def compute( self, *args, **kwargs ):
        """
        Generate a series of state changes, due to the provided input arguments.  Pick off the next
        positional arg, or the keyword arg named after our class.
        """
        if 0 == kwargs.setdefault( '__depth', 0 ):
            self.advance()
        kwargs['__depth']      += 1

        if args:
            arg, args   = args[0], args[1:]
        else:
            arg         = kwargs.pop( 'level', None )

        transitions             = super( level, self ).compute( *args, **kwargs )
        for trans in transitions:
            #print "%s.compute -- yielding: %s" % ( "level", trans )
            yield trans

        # Always process a sample; at the least, 'now' will advance on __depth == 0 external
        # invocations of compute()
        self.value.sample( arg, now=self.now() )
        after           = self.value.level()
        if after != self.before:
            #print "%s.compute -- transition on level change; was %s, now %s" % (
            #    "level", self.before, after)
            self.before = after
            trans = self.transition()
            #print "%s.compute -- yielding: %s" % ( "level", trans )
            yield trans
            self.advance()
        

class acklevel( ack, level ):
    """
    Level monitoring alarm, with acknowledgement.
    """
    pass
