#!/usr/bin/env python

"""
server.prodsumer
server.server

    Implement a threaded producer/consumer type SOCK_DGRAM server.

"""

__author__ 				= "Perry Kundert (perry.kundert@enbridge.com)"
__version__ 				= "$Revision: 1.2 $"
__date__ 				= "$Date: 2006/05/10 16:51:11 $"
__copyright__				= "Copyright (c) 2006 Perry Kundert"
__license__				= "Enbridge Pipelines Inc."

import socket
import select
import re
import time
import logging
import unittest
import threading

# Local modules
import hex

class prodsumer( threading.Thread ):
    """
    Implements a threaded producer/consumer.  Override 'run()' to implement.
    """
    def __init__( self ):
        self.consuming			= []
        self.producing			= []
        self.done			= False
        threading.Thread.__init__( self )
        self.start()

    
    def ready( self ):
        """We have something ready to consume()"""
        return 0 != len( self.consuming )

    def input( self, thing ):
        """Provide input for consume()"""
        self.consuming.append( thing )

    def consume( self ):
        """Dequeue from input()"""
        return self.consuming.pop( 0 )

    
    def waiting( self ):
        """We are waiting to deliver a product()"""
        return 0 != len( self.producing )

    def produce( self, thing ):
        """Enqueue something for output()"""
        self.producing.append( thing )

    def output( self ):
        """Retrieve output from produce()"""
        return self.producing.pop( 0 )


    def terminate( self ):
        log.info( "Shutting down..." )
        self.done			= True
        self.join()
        log.info( "Done." )

class server( prodsumer ):
    """
    Implements a single server thread, receiving/transmitting a series of packets,
    on a given local i'face:port.   Produce a series of (data,local) tuples,
    and consumes a series of (data,peer) tuples.
    """
    def __init__( self, local ):
    	self.server 			= socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.server.bind( local )
        prodsumer.__init__( self )

    def run( self ):
        """
        Process incoming and outgoing packets, to/from the given local iface:port.
        """
        while not self.done:
            # If there is data to receive AND send, we can wait longer.  Otherwise, we need to poll
            # for data ready to consume (transmit)!  We should select() on incoming data WHILE
            # awaiting outgoing packets to consume (semaphore), but that would require 2 threads...
            rxabl,txabl,err		= select.select( [self.server],
                                                         self.ready() and [self.server] or [],
                                                         [],
                                                         self.ready() and 1.0 or 0.01 )
            if rxabl:
                data,peer		= self.server.recvfrom( 65536 )
                log.info( "Recv <== %16s:%-5d\n" % peer + hex.dump( data ))
                self.produce( (data,peer) )
            if txabl:
                data,peer		= self.consume()
                log.info( "Send ==> %16s:%-5d\n" % peer + hex.dump( data ))
                self.server.sendto( data, peer )
            if err:
                # TODO: What to do?  Signal error somehow?  We're in a thread, here...
                for p in err:
                    log.info( "Error:   %16s:%-5d\n" % p )
        log.info( "Done === %16s:%-5d\n" % peer )

# 
# Unit Tests
# 
class TestServer( unittest.TestCase ):
    def setUp( self ):
        pass

    def testSimple( self ):
        prt1				= 23232
        prt2				= 23233
        add1				= ( 'localhost', prt1 )
        add2				= ( 'localhost', prt2 )
        svr1				= server( add1 )
        svr2				= server( add2 )

        self.assertEqual( svr1.ready(),   False )
        self.assertEqual( svr1.waiting(), False )
        self.assertEqual( svr2.ready(),   False )
        self.assertEqual( svr2.waiting(), False )

        svr1.input( ("Hello, world!",add2) )
        then			= time.time() + 2
        while time.time() < then and not svr2.waiting():
            time.sleep( 0.001 )
        self.assertEqual( svr2.waiting(), True )
        if svr2.waiting():
            data,peer			= svr2.output()
            self.assertEqual( data, "Hello, world!" )
            self.assertEqual( peer, ( '127.0.0.1', prt1 ))
        svr1.terminate()
        svr2.terminate()

if __name__ == "__main__":
    # Run directly.  Set up "default" logging, and run unit tests.
    logfile				= "./server.py.log"
    logformat				= '%(asctime)s %(levelname)-8s %(message)s'
    log					= logging.getLogger('server.py')
    loghandler				= logging.FileHandler( logfile )
    logformatter			= logging.Formatter( logformat )
    loghandler.setFormatter( logformatter )
    log.addHandler( loghandler )
    log.setLevel( logging.INFO )
    unittest.main()
