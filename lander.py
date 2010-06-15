#!/usr/bin/env python

__author__ 			= "Perry Kundert (perry@kundert.ca)"
__version__ 			= "$Revision: 1.2 $"
__date__ 			= "$Date: 2006/05/10 16:51:11 $"
__copyright__			= "Copyright (c) 2008 Perry Kundert"
__license__			= "GNU General Public License V3 (or higher)"

import time
from misc import *
import pid
import random

# message
#
#     Clip message to available display area.  (0,0) is transformed to the lower-left.
# 
def message( window, text, row = 0, col = 0 ):
    rows, cols			= window.getmaxyx()

    c				= col
    r				= rows - 1 - row

    if r < 0 or r >= rows:
        return
    if c < 0:
        if c + len( text ) < 0:
            return
	text			= text[-c:]
        c			= 0
    if c + len( text ) >= cols:
        if c >= cols:
            return
        text		= text[:cols - c]

    window.addstr( r, c, text )


# object
# 
#     Define an object with a position, velocity and acceleration.  New position
# and velocity is computed over time.
# 
class object:
    def __init__( self, p, v, a, now = None, what = '.'  ):
        self.p			= p
        self.v			= v
        self.a			= a

        if now is None:
            now			= time.time()
        self.now		= now

        self.what		= what

    def move( self, now = None ):
        if now is None:
            now			= time.time()
        dt			= now - self.now
        self.now		= now

        ov			= self.v
        self.v			= tuple( [ v + a * dt for v,a in zip( list( self.v ), list( self.a ) )] )
        self.p			= tuple( [ p + ( ov + v ) / 2 * dt for p,ov,v in zip( list( self.p ), list( ov ), list( self.v )) ] )

    def draw( self, window ):
        message( window, self.what, col = self.p[0], row = self.p[1] )

# lander
# 
#     Animate lunar lander in a gravity field.
# 
#         
#    .........
#    \ -24'  /
# 
#       /^\
#      |XAX|
#      / v \
#
class lander ( object ):
    def __init__( self, p, v, g, now = None ):
        object.__init__( self, p, v, ( 0., -g ), now )
        self.g			= g
        self.rot		= 0.    # radians; -'ve == left lean, +'ve right lean
        self.rot_lim		= ( -math.pi*30/180, math.pi*30/180 )
        self.thrust		= 0		# kg m/s^2
        self.engine		= ( 0, 3000 )	# kg m/s^2 range
        self.fuel		= 250.  	# kg
        self.fuel_energy	= 500.  	# kg m/s^2 per kg
        self.mass		= 1000. 	# kg

    def throttle( self, proportion ):
        self.thrust		= int( scale( proportion, ( 0., 1. ), self.engine ))

    def roll( self, proportion ):
        self.rot		= scale( proportion, ( -1., 1. ), self.rot_lim )

    def move( self, now = None ):
        if now is None:
            now 		= time.time()
        dt			= now - self.now

        # Compute thrust, fuel consumption, average mass and over time period 'dt'
        burnt			= min( self.fuel,			 # kg
                                       self.thrust / self.fuel_energy )
        gross			= self.mass + ( self.fuel - burnt / 2 )
        self.fuel	       -= burnt

        self.a			= ( 0., self.thrust / gross - self.g )

        object.move( self, now )

    def draw( self, window ):
        message( window, 'Fuel: %5.2f, Thrust: %5.2f, Acc: %5.2f' % ( self.fuel, self.thrust, self.a[1] ), col = 1, row = 1 )

        eighths			= int( scale( self.rot, self.rot_lim, ( 0, 8.999 )))
        dot 			= ' ' * ( 8 - eighths ) + '.'

        message( window,  dot, col = self.p[0] - 4, row = self.p[1] + 5 )
        message( window,  '\\  % +2d\'  /' % int( self.rot * 180 / math.pi ), col = self.p[0] - 4, row = self.p[1] + 4 )
        message( window,  '/^\\', col = self.p[0] - 1, row = self.p[1] + 2 )
        message( window, '|XAX|', col = self.p[0] - 2, row = self.p[1] + 1 )
        message( window, '/ ' + ' vvvVVVVVV'[int( self.now * 1000000 ) % scale( int( self.thrust ), self.engine, ( 1, 9 ))] + ' \\', col = self.p[0] - 2, row = self.p[1] + 0 )

    

def ui( win, title = "Test" ):
    # Run a little rocket up to 1/4 way up screen, and then station-keep.  Use both styles of PID loop controller.

    rows, cols			= win.getmaxyx()

    lastchar			= ' '

    now				= time.time()
    pos				= ( cols/2, rows/2 )
    throttle			= 0.  # ( 0, 1)
    angle			= 0.  # (-1,+1)
    g				= 9.8 / 6

    # Generate some tarrain at various X positions.  -'ve (leftward) ground is simply inverse of +'ve
    elevation			= ( 3, 10 )	# min/max elevation (avg. is beginning)
    ground			= {}
    ground[0]			= elevation[0] + ( elevation[1] - elevation[0] ) / 2
    for x in range( 1, 1000 ):
        ground[x]		= clamp( ground[x-1] + random.randint( -1, 1 ), elevation )
        ground[-x]		= scale( ground[x], elevation, ( elevation[1], elevation[0] ))

    autopilot			= True

    # PID loop tuning
    #Kpid			= (   5.0,       1.0,        2.0   )
    #Kpid			= (  10.0,       0.0001, 10000.0   )
    Kpid			= (   3.0,       0.1,      100.0   )
    Lout			= ( 0., 1. )

    autocntrl			= pid.controller( Kpid,
                                                  setpoint	= 0.0,
                                                  process	= 1.0 * pos[1] / rows,
                                                  output	= throttle,
                                                  now		= now )


    ol				= [ ]
    lndr			= lander( pos, ( 0., 0. ), g, now = now )
    ol.append( lndr )

    for i in range( 0, 10 ):
        ol.append( object( ( 10., 0. ), ( 5. + i -  5, 25. + i - 5 ), ( 0., -9.8 ), now = now ) )

    escaped			= False
    while 1:
        # Draw the ground
        for c in range ( 0, cols - 1 ):
            if ( ground[c+1] > ground[c] ):
                message( win, '/',  col = c, row = ground[c] )
            elif ( ground[c+1] < ground[c] ):
                message( win, '\\', col = c, row = ground[c] - 1 )
            else:
                message( win, '_',  col = c, row = ground[c] )
            
        win.refresh()

        input			= win.getch()
        if input >= 0 and input <= 255:
            lastchar		= chr( input )

            if chr( input ) == '-' or chr( input ) == 'i':
                throttle        = max( 0., throttle - .1 )

            if chr( input ) == '+' or chr( input ) == 'k':
                throttle        = min( 1., throttle + .1 )

            if chr( input ) == 'j':
                angle           = max( -1., angle - .1 )

            if chr( input ) == 'l':
                angle           = min(  1., angle + .1 )

            if chr( input ) == ' ':
                autopilot       = not autopilot

            if chr( input ) ==  'z':
                autocntrl.P	= 0.
                autocntrl.I	= 0.
                autocntrl.D	= 0.
                
            # Adjust Kp
            if input <= 255 and chr( input) == 'P':
                    inc			= magnitude( autocntrl.Kp )
                    autocntrl.Kp     += inc + inc / 100
                    autocntrl.Kp     -= autocntrl.Kp % inc
            if input <= 255 and chr( input) == 'p':
                    inc			= magnitude( autocntrl.Kp )
                    autocntrl.Kp     -= inc - inc / 100
                    autocntrl.Kp     -= autocntrl.Kp % inc

            # Adjust Ki
            if input <= 255 and chr( input) == 'I':
                    inc			= magnitude( autocntrl.Ki )
                    autocntrl.Ki     += inc + inc / 100
                    autocntrl.Ki     -= autocntrl.Ki % inc
            if input <= 255 and chr( input) == 'i':
                    inc			= magnitude( autocntrl.Ki )
                    autocntrl.Ki     -= inc - inc / 100
                    autocntrl.Ki     -= autocntrl.Ki % inc

            # Adjust Kd
            if input <= 255 and chr( input) == 'D':
                    inc			= magnitude( autocntrl.Kd )
                    autocntrl.Kd     += inc + inc / 100
                    autocntrl.Kd     -= autocntrl.Kd % inc
            if input <= 255 and chr( input) == 'd':
                    inc			= magnitude( autocntrl.Kd )
                    autocntrl.Kd     -= inc - inc / 100
                    autocntrl.Kd     -= autocntrl.Kd % inc


        lndr.throttle( throttle )
        lndr.roll( angle )

        # Next frame of animation
        win.clear()

        last			= now
        now			= time.time()
        dt			= now - last

        Op,Oi,Od		= autocntrl.contribution()
        message( win,
                 "(out: % 8.4f/% 8.4f [P/p]: % 8.4f/% 8.4f (% 3d%%) [I/i]: % 8.4f/% 8.4f (% 3d%%) [D/d]: %8.4f/% 8.4f (% 3d%%))"
                   % ( autocntrl.output, autocntrl.value,
                       autocntrl.Kp, autocntrl.P, not isnan( Op ) and int( Op * 100 ) or 0,
                       autocntrl.Ki, autocntrl.I, not isnan( Oi ) and int( Oi * 100 ) or 0,
                       autocntrl.Kd, autocntrl.D, not isnan( Od ) and int( Od * 100 ) or 0 ),
                 row = 2, col = 0 )

        message( win, "(%s) % 7.3f,% 7.3fm @ % 7.3f,% 7.3fm/s %+ 7.3f,%+ 7.3fm/s^2" % (
                autopilot and "auto" or "man.",
                lndr.p[0], lndr.p[1], 
                lndr.v[0], lndr.v[1],
                lndr.a[0], lndr.a[1] ),
                 row = 0, col = 0 )
                 


        for o in ol:
            o.move( now = now )
            o.draw( win )

        if autopilot:
            # Autopilot enabled; set next period's throttle position
            # based on this period's resultant position vs. ground
            throttle		= autocntrl.loop( ground[lndr.p[0]] / float( rows ), lndr.p[1] / float( rows ), now, Lout )


if __name__=='__main__':
    import curses, traceback
    try:        # Initialize curses
        stdscr=curses.initscr()
        curses.noecho() ; curses.cbreak(); curses.halfdelay( 1 )
        stdscr.keypad(1)
        ui( stdscr, title="Rocket" )        # Enter the mainloop
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()                 # Terminate curses
    except:
        stdscr.keypad(0)
        curses.echo() ; curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception

