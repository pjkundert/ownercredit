#!/usr/bin/env python


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

import time
import random
import math

# Local modules
import misc
import filtered
import pid


# message
#
#     Clip message to available display area.  (0,0) is transformed to the lower-left.
# 
def message( window, text, row = 0, col = 0 ):
    rows, cols                  = window.getmaxyx()

    c                           = col
    r                           = rows - 1 - row

    if r < 0 or r >= rows:
        return
    if c < 0:
        if c + len( text ) < 0:
            return
        text                    = text[-c:]
        c                       = 0
    if c + len( text ) >= cols:
        if c >= cols:
            return
        text            = text[:cols - c]

    window.addstr( r, c, text )


# object
# 
#     Define an object with a position, velocity and acceleration.  New position
# and velocity is computed over time.
# 
class object:
    def __init__( self, p, v, a, now = None, what = '.'  ):
        self.p                  = p
        self.v                  = v
        self.a                  = a

        if now is None:
            now                 = time.time()
        self.now                = now

        self.what               = what

    def move( self, now = None ):
        if now is None:
            now                 = time.time()
        dt                      = now - self.now
        self.now                = now

        ov                      = self.v
        self.v                  = tuple( [ v + a * dt for v,a in zip( list( self.v ), list( self.a ) )] )
        self.p                  = tuple( [ p + ( ov + v ) / 2 * dt for p,ov,v in zip( list( self.p ), list( ov ), list( self.v )) ] )

    def draw( self, window ):
        message( window, self.what, col = self.p[0], row = self.p[1] )

# lander
# 
#     Animate lunar lander in a gravity field, with 3 scales
# 
# Scale:
#   x16 +          x4              x1
#                               .........
#               .........       \ -24'  /
#  .........    \ -24'  /          _o_
#  \ -24'  /                     +/< >\+
#                  /^\            \ @ /O
#                 |XAX|          / / \ \
#      A          / M \        _/  ( )  \_ 
#      '            V               v
# 
#
#
class lander ( object ):
    def __init__( self, p, v, g, now = None ):
        object.__init__( self, p, v, ( 0., -g ), now )
        self.g                  = g
        self.rot                = 0.    # radians; -'ve == left lean, +'ve right lean
        self.rot_lim            = ( -math.pi*30/180, math.pi*30/180 )
        self.thrust             = 0             # kg m/s^2
        self.engine             = ( 0, 3000 )   # kg m/s^2 range
        self.fuel               = 250.          # kg
        self.fuel_energy        = 500.          # kg m/s^2 per kg
        self.mass               = 1000.         # kg

    def throttle( self, proportion ):
        self.thrust             = int( misc.scale( proportion, ( 0., 1. ), self.engine ))

    def roll( self, proportion ):
        self.rot                = misc.scale( proportion, ( -1., 1. ), self.rot_lim )

    def move( self, now = None ):
        if now is None:
            now                 = time.time()
        dt                      = now - self.now

        # Compute thrust, fuel consumption, average mass and over time period 'dt'
        burnt                   = min( self.fuel,                        # kg
                                       self.thrust / self.fuel_energy )
        gross                   = self.mass + ( self.fuel - burnt / 2 )
        self.fuel              -= burnt

        self.a                  = ( 0., self.thrust / gross - self.g )

        object.move( self, now )

    def draw( self, window, scale = 1 ):
        message( window, 'Fuel: %5.2f, Thrust: %5.2f, Acc: %5.2f' % ( self.fuel, self.thrust, self.a[1] ), col = 1, row = 1 )

        thr_mag                 = int( misc.scale( self.thrust, self.engine, ( 1.0, 10.99 )))
        height                  = 0

        if ( scale >= 16 ):
            height              = 1
            message( window,  'A',
                     col = self.p[0]    , row = self.p[1] + 0 )
            message( window,  " '''!!!!!|"[int( self.now * 1000000 ) % thr_mag],
                     col = self.p[0]    , row = self.p[1] - 1 )

        elif ( scale > 1 ):
            height              = 3
            message( window,  '/^\\',
                     col = self.p[0] - 1, row = self.p[1] + 2 )
            message( window, '|XAX|',
                     col = self.p[0] - 2, row = self.p[1] + 1 )
            message( window, '/ ^ \\',
                     col = self.p[0] - 2, row = self.p[1] + 0 )
            message( window, ' vvvVVVVVW'[int( self.now * 1000000 ) % thr_mag],
                     col = self.p[0]    , row = self.p[1] - 1 )
        else:
            height              = 5
            thr_char            = ' \'vvvVVVVW'[int( self.now * 1000000 ) % thr_mag]

            message( window,    '_o_',
                     col = self.p[0] - 1, row = self.p[1] + 4 )
            message( window,  '+/< >\\+',
                     col = self.p[0] - 3, row = self.p[1] + 3 )
            message( window,   '\\ @ /O',
                     col = self.p[0] - 2, row = self.p[1] + 2 )
            message( window,   '/ / \\ \\',
                     col = self.p[0] - 3, row = self.p[1] + 1 )
            if thr_mag > 5:
                message( window, '_/  ( )  \\_',
                         col = self.p[0] - 5, row = self.p[1] + 0 )
                message( window, thr_char,
                         col = self.p[0]    , row = self.p[1] - 1 )
            else:
                message( window, '_/   ' + thr_char + '   \\_',
                         col = self.p[0] - 5, row = self.p[1] + 0 )

        eighths                 = int( misc.scale( self.rot, self.rot_lim, ( 0.0, 8.999 )))
        dot                     = ' ' * ( 8 - eighths ) + '.'
        message( window,  dot, col = self.p[0] - 4, row = self.p[1] + height + 2 )
        message( window,  '\\  %- 3d\' /' % int( self.rot * 180 / math.pi ), col = self.p[0] - 4, row = self.p[1] + height + 1 )



    

def ui( win, title = "Test" ):
    # Run a little rocket up to 1/4 way up screen, and then station-keep.  Use both styles of PID loop controller.

    rows, cols                  = win.getmaxyx()

    lastchar                    = ' '

    X                           = 0     # Indices for (x,y) tuples
    Y                           = 1
    now                         = time.time()
    pos                         = ( cols/2, rows/2 )
    throttle                    = 0.  # ( 0, 1)
    angle                       = 0.  # (-1,+1)
    g                           = 9.8 / 6

    # Generate some tarrain at various X positions.  -'ve (leftward) ground is simply inverse of +'ve
    elevation                   = ( 4, 10 )     # min/max elevation (avg. is beginning)
    ground                      = {}
    ground[0]                   = elevation[0] + ( elevation[1] - elevation[0] ) / 2
    for x in range( 1, 1000 ):
        ground[x]               = misc.clamp( ground[x-1] + random.randint( -1, 1 ), elevation )
        ground[-x]              = misc.scale( ground[x], elevation, ( elevation[1], elevation[0] ))

    autopilot                   = True

    # PID loop tuning
    #Kpid                       = (   5.0,       1.0,        2.0   )
    #Kpid                       = (  10.0,       0.0001, 10000.0   )
    Kpid                        = (   3.0,       0.1,      100.0   )
    Lout                        = ( 0., 1. )

    autocntrl                   = pid.controller( Kpid,
                                                  setpoint      = 0.0,
                                                  process       = 1.0 * pos[1] / rows,
                                                  output        = throttle,
                                                  now           = now )


    othr                        = [ ]
    lndr                        = lander( pos, ( 0., 0. ), g, now = now )

    for i in range( 0, 10 ):
        othr.append( object( ( 10., 0. ), ( 5. + i -  5, 25. + i - 5 ), ( 0., -9.8 ), now = now ) )

    # Average altitude is a time-weighted average over the last 1/2 second.
    altitude                    = filtered.weighted( 0.5, now = now )

    while 1:
        win.refresh()

        input                   = win.getch()
        if input >= 0 and input <= 255:
            lastchar            = chr( input )

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
                autocntrl.P     = 0.
                autocntrl.I     = 0.
                autocntrl.D     = 0.
                
            # Adjust Kp
            if input <= 255 and chr( input) == 'P':
                inc             = misc.magnitude( autocntrl.Kp )
                autocntrl.Kp   += inc + inc / 100
                autocntrl.Kp   -= autocntrl.Kp % inc
            if input <= 255 and chr( input) == 'p':
                inc             = misc.magnitude( autocntrl.Kp )
                autocntrl.Kp   -= inc - inc / 100
                autocntrl.Kp   -= autocntrl.Kp % inc

            # Adjust Ki
            if input <= 255 and chr( input) == 'I':
                inc             = misc.magnitude( autocntrl.Ki )
                autocntrl.Ki   += inc + inc / 100
                autocntrl.Ki   -= autocntrl.Ki % inc
            if input <= 255 and chr( input) == 'i':
                inc             = misc.magnitude( autocntrl.Ki )
                autocntrl.Ki   -= inc - inc / 100
                autocntrl.Ki   -= autocntrl.Ki % inc

            # Adjust Kd
            if input <= 255 and chr( input) == 'D':
                inc             = misc.magnitude( autocntrl.Kd )
                autocntrl.Kd   += inc + inc / 100
                autocntrl.Kd   -= autocntrl.Kd % inc
            if input <= 255 and chr( input) == 'd':
                inc             = misc.magnitude( autocntrl.Kd )
                autocntrl.Kd   -= inc - inc / 100
                autocntrl.Kd   -= autocntrl.Kd % inc


        lndr.throttle( throttle )
        lndr.roll( angle )

        # Next frame of animation
        win.clear()

        last                    = now
        now                     = time.time()
        dt                      = now - last

        # 
        # Compute the scale.  We'll assume that the character cells
        # are ~ 1 unit wide x 2 tall:
        # 
        #   +---+---+---+---+
        #   |   |   |   |   |
        #   +---+---+---+---+
        #   |   |   |   |   |
        #   +---+---+---+---+
        #   |   |   |   |   |
        #   +---+---+---+---+
        #   |   |   |   |   |
        #   +---+---+---+---+
        # 

        #   There will be 3 scales:
        # 
        # 
        #  1: x 1.0000: 16 cells wide / meter
        #  4: x  .2500:  4 cells wide / meter
        # 16: x  .0625:  1 cell  wide / meter

        c_m                     = {}
        c_m[ 1]                 = ( 16.,   8.   )
        c_m[ 4]                 = (  4.,   2.   )
        c_m[16]                 = (  1.,   .5   )
        c_m[64]                 = (  1./4, .5/4 )

        # How far from the surface are we?  If more than 3/4 screen
        # for the last second, zoom out (increase scale)
        scale                   = 1
        scale_max               = 64
        while scale < scale_max and float( altitude ) > .75 * rows / c_m[scale][Y]:
            scale              *= 4

        # Draw the ground
        for c in range ( 0, cols - 1 ):
            if ( ground[c+1] > ground[c] ):
                message( win, '/',  col = c, row = ground[c] )
            elif ( ground[c+1] < ground[c] ):
                message( win, '\\', col = c, row = ground[c] - 1 )
            else:
                message( win, '_',  col = c, row = ground[c] )
            

        Op,Oi,Od                = autocntrl.contribution()
        message( win,
                 "Altitude: % 8.4f (x% 2d),  Thrust: % 8.4f [P/p]: % 8.4f/% 8.4f (% 3d%%) [I/i]: % 8.4f/% 8.4f (% 3d%%) [D/d]: %8.4f/% 8.4f (% 3d%%))"
                   % ( float( altitude ), scale,
                       autocntrl.value,
                       autocntrl.Kp, autocntrl.P, not misc.isnan( Op ) and int( Op * 100 ) or 0,
                       autocntrl.Ki, autocntrl.I, not misc.isnan( Oi ) and int( Oi * 100 ) or 0,
                       autocntrl.Kd, autocntrl.D, not misc.isnan( Od ) and int( Od * 100 ) or 0 ),
                 row = 2, col = 0 )

        message( win, "(%s) % 7.3f,% 7.3fm @ % 7.3f,% 7.3fm/s %+ 7.3f,%+ 7.3fm/s^2" % (
                autopilot and "auto" or "man.",
                lndr.p[X], lndr.p[Y], 
                lndr.v[X], lndr.v[Y],
                lndr.a[X], lndr.a[Y] ),
                 row = 0, col = 0 )
                 

        # Update the Lunar Lander, and keep track of its altidute (time-weighted)
        lndr.move( now = now )
        lndr.draw( win )
        altitude.sample( lndr.p[Y] - ground[int( lndr.p[X] )], now = now )

        # Update all other objects
        for o in othr:
            o.move( now = now )
            o.draw( win )
            # If object has crashed down thru ground surface, destroy object, make crater.  
            x                   = int( o.p[X] )
            if ( o.v[Y] < 0 and o.p[Y] <= ground[x] ):
                ground[x] -= 1
                w               = 1
                if ( ground[x+w+1] - ground[x+w] > 1 ):
                    ground[x+w+1] = ground[x+w] + 1
                if ( ground[x-w-1] - ground[x-w] > 1 ):
                    ground[x-w-1] = ground[x-w] + 1

                othr.remove( o )


        if autopilot:
            # Autopilot enabled; set next period's throttle position
            # based on this period's resultant position vs. ground
            throttle            = autocntrl.loop( ground[lndr.p[X]] / float( rows ),
                                                  lndr.p[Y] / float( rows ), now, Lout )


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

