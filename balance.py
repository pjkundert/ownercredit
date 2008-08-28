import curses, os, sys, time

class object:
    def __init__( pos, vel, now = time.time() ):
        self.pos		= pos
        self.vel		= vel
        self.now		= now

    def step( now = time.time() ):
        dt			= now - self.now
        pos[0]		       += vel[0] * dt
        pos[1]		       += vel[1] * dt
        self.now		= now

class world:
    g				= 9.8
    
    
