from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ownercredit import misc
from ownercredit.misc import near
from ownercredit import filtered

def test_level_int():
    lvl                 = filtered.level( 0, 0 )
    assert 0 == lvl
    assert lvl.name() == "lo"
    assert 1 == lvl.sample( 1 )
    assert lvl.name() == "normal"
    assert -1 == lvl.sample( -1 )
    assert lvl.name() == "lo"
    assert 0 == lvl.sample( 0 )
    assert lvl.name() == "lo"
    assert 1 == lvl.sample( 1 )
    assert lvl.name() == "normal"

    lvl                 = filtered.level( 0, 0, [-10, 10] )
    assert int(lvl) == 0
    assert 0 == lvl
    assert  8 == lvl.sample(  8 )
    assert  9 == lvl.sample(  9 )
    assert  0 == lvl.level()
    assert 10 == lvl.sample( 10 )
    assert  1 == lvl.level()
    assert 11 == lvl.sample( 11 )
    assert  1 == lvl.level()
    assert 10 == lvl.sample( 10 )
    assert  1 == lvl.level()
    assert  9 == lvl.sample(  9 )
    assert  0 == lvl.level()
    
    lvl                 = filtered.level( 0, 1, [-10, 10] )
    assert int(lvl) == 0
    assert 0 == lvl
    assert  8 == lvl.sample(  8 )
    assert  8 == lvl.sample(  9 ) # ignore changes within hysteresis of 1!
    assert  0 == lvl.level()
    assert 10 == lvl.sample( 10 )
    assert  1 == lvl.level()

def test_level_float():
    lvl                 = filtered.level( 0.0, .25, [-1, 1] )
    assert near( 0.0, lvl )
    assert 0 == lvl.level()
    assert lvl.name() == "normal"
    assert near( 0.0, lvl.sample( 0.0  ))
    assert near( 0.0, lvl.sample( 0.25 ))
    assert near( 0.26, lvl.sample( 0.26 ))
    assert 0 == lvl.level()
    assert near( 0.99, lvl.sample( 0.99 ))
    assert 0 == lvl.level()
    assert near( 1.0, lvl.sample( 1.00 ))
    assert 1 == lvl.level()
    assert lvl.name() == "hi"
    assert near( 1.0, lvl.sample( 0.99 ))
    assert 1 == lvl.level()
    assert near( 1.0, lvl.sample( 0.75 ))
    assert 1 == lvl.level()
    assert near( .74, lvl.sample( 0.74 ))
    assert 0 == lvl.level()

def test_level_float_5state():

    lvl                 = filtered.level( 0.0, .25, [-3, -1, 1, 3] )
    assert near( 0.0, lvl )
    assert 0 == lvl.level()
    assert lvl.name() == "normal"
    assert near( -1.0, lvl.sample( -1.0 )) # Only need to meet limit away from normal
    assert -1 == lvl.level()
    assert near( -3.0, lvl.sample( -3.0 )) # Only need to meet limit away from normal
    assert -2 == lvl.level()
    assert near( -3.0, lvl.sample( -2.75)) # Must exceed limit toward normal!
    assert -2 == lvl.level()
    assert near( -2.74, lvl.sample( -2.74)) # Must exceed limit toward normal!
    assert -1 == lvl.level()

    # Same limits, no hysteresis
    lvl                 = filtered.level( 0.0, 0, [-3, -1, 1, 3] )
    assert near( 0.0, lvl )
    assert 0 == lvl.level()
    assert lvl.name() == "normal"
    assert near( -1.0, lvl.sample( -1.0 )) # Only need to meet limit away from normal
    assert -1 == lvl.level()
    assert near( -3.0, lvl.sample( -3.0 )) # Only need to meet limit away from normal
    assert -2 == lvl.level()
    assert near( -1.0, lvl.sample( -1.0 )) # Only need to meet limit away from normal
    assert -1 == lvl.level()
    assert near( -2.75, lvl.sample( -2.75 )) # Must exceed limit toward normal!
    assert -1 == lvl.level()


# Test that filtered.level samples a misc.value correctly, recomputing it.
def test_level_value():
    # Value will increase linearly from 0. to 10. over time period from 10 to 20
    v			= filtered.weighted_linear( value=0., now=0, interval=10 )
    v.sample( value=10., now=10 )

    l			= filtered.level( value=v, normal=5., now=10 )

    for t in range( 10, 21 ):
        l.sample( value=v, now=t )
        lev		= l.level()
        #print "now==%d: value == %7.2f, lev==%d" % ( t, v.compute( now=t ), lev )
        assert lev == 0 if t > 15 else -1
        


# Test the base averaged class.  Acts like a plain integer or float value, but is charged with
# timestamped values using the .sample( value [, time ] ) method.  Implements a simple average of
# all sample values within the time span specified at creation.
def test_averaged():
    a                   = filtered.averaged( 10., 0., 90. )
    assert near( 0.0000, a )
    assert near( 0.5000, a.sample(  1.,  91. ))
    assert near( 1.0000, a.sample(  2.,  94. ))
    assert near( 2.0000, a.sample(  3., 100. ))

    a                   = filtered.averaged( 10., 5., 1. )
    assert near( 5.0, a )
    assert near( 4.5, a.sample(  4.,  2. ))
    assert near( 4.5, a )
    assert near( 5.0, a.sample(  6.,  3. ))
    assert near( 5.0, a )
    assert near( 5.0, a.sample(  5.,  4. ))
    assert near( 5.0, a.sample(  5., 10. ))
    assert 5 == len( a.history )
    assert near( 5.25,a.sample(  5., 12. ))     # timestamps 3-12 now within interval 10; 1-2 drop off
    assert 5 == len( a.history )                #   but 1 outside interval retained
    assert near( 5.0, a.sample(  5., 13. ))     # 0 x 4, 4 x 5, 1 x 6
    assert 5 == len( a.history )
    assert near( 5.0, a.sample(  5., 14. ))
    assert 5 == len( a.history )
    assert near( 5.0, a )


# Test the (better) weighted_linear classs
def test_weighted_linear():
    # sample == 0. @ 90.,  interval == 10.
    w                   = filtered.weighted_linear( 10., 0., 90. )
    assert near( 0.0000, w )
    assert near( 0.0000, w.compute( now=91. ))  # future value, single historical value

    # sample == 1. @ 91.
    assert near( 0.0000, w.sample(  1.,  91. )) # 0. has interval of 1. (90. to 91.); 1.0 has no interval yet
    assert len( w.history ) == 2
    assert near( 0.5000, w.compute( now=92. ))  # future value, two historical values
    assert near( 0.9000, w.compute( now=100. )) #  ''
    assert near( 1.0000, w.compute( now=101. )) #  ''

    # sample == 2. @ 94.
    assert near( 0.7500, w.sample(  2.,  94. )) # 0. has interval of 1., 1. has interval of 3. (91. to 94.)
    assert len( w.history ) == 3

    # sample == 3. @ 100.
    assert near( 1.5000, w.sample(  3., 100. )) # 0. x 1.ticks, 1. x 3.t, 2. x 6.t, 3. x 0.t == 15. / 10.
    assert near( 1.5000, w.compute( now=100. )) # future value, several historical values.  See if they drop...
    assert near( 1.8000, w.compute( now=101. )) # 0. x 0.ticks, 1. x 3.t, 2. x 6.t, 3. x 1.t == 18. / 10.
    assert near( 2.2000, w.compute( now=103. )) # 0. x 0.ticks, 1. x 1.t, 2. x 6.t, 3. x 3.t == 22. / 10.
    assert near( 2.5000, w.compute( now=105. )) # 0. x 0.ticks, 1. x 0.t, 2. x 5.t, 3. x 5.t == 25. / 10.
    assert near( 2.9000, w.compute( now=109. )) # 0. x 0.ticks, 1. x 0.t, 2. x 5.t, 3. x 5.t == 29. / 10.

    w                   = filtered.weighted_linear( 10., 5., 1. )
    assert near( 5.0, w )                       # Single value so far
    assert near( 5.0, w.sample(  4.,  2. ))     # The 5. has now been in effect for 1. of the interval; 4. has no interval yet
    assert near( 5.0, w )
    assert near( 4.5, w.sample(  6.,  3. ))     # Now 5. and 4. have been in effect for 1. (each); 6. has no interval yet
    assert near( 4.5, w )
    assert near( 5.0, w.sample(  5.,  4. ))     # 4. and 6. now each in effect for 1.; 5. not yet
    assert near( 5.0, w.sample(  5., 10. ))
    assert near( 5.0, w.sample(  5., 12. ))     # Drops the 4. (but retains for time-weighted average!)
    assert near( 5.1, w.sample(  5., 13. ))     # Drops the 6. (but ...)
    assert near( 5.0, w.sample(  5., 14. ))     # Finally, only 5.'s in effect
    assert near( 5.0, w )

    # Try NaN handling
    w                   = filtered.weighted_linear( 10., misc.nan, 0. )
    assert misc.isnan( w )
    assert len( w.history ) == 0
    assert misc.isnan( w.compute( now=1. ))

    assert w.sample( 999., 1. )
    assert len( w.history ) == 1
    assert near( 999.00, w )
    assert near( 999.00, w.sample(  0., 2. ))
    assert near( 499.50, w.compute( now=3. ))
    assert near( 333.00, w.compute( now=4. ))
    assert near(   0.00, w.compute( now=100. ))
    assert near( 999.00, w )


# We can simulate linear by putting ending values at the same 
# timestamp as the next beginning value.  Uses same tests as
# test_weighted_linear above
def test_weighted_with_simultaneous():
    w                   = filtered.weighted( 10., 0., 90. )
    assert near( 0.0000, w )
    assert near( 0.0000, w.sample(  0.,  91. ))
    assert near( 0.0000, w.sample(  1.,  91. )) # 0. has interval of 1. (90. to 91.); 1.0 has no interval yet
    assert len( w.history ) == 3
    assert near( 0.7500, w.sample(  1.,  94. ))
    assert near( 0.7500, w.sample(  2.,  94. )) # 0. has interval of 1., 1. has interval of 3. (91. to 94.)
    assert len( w.history ) == 5
    assert near( 1.5000, w.sample(  2., 100. ))
    assert near( 1.5000, w.sample(  3., 100. )) # 0. x 1., 1. x 3., 2. x 6.

    w                   = filtered.weighted( 10., 5., 1. )
    assert near( 5.0, w )                       # Single value so far
    assert near( 5.0, w.sample(  5.,  2. ))
    assert near( 5.0, w.sample(  4.,  2. ))     # The 5. has now been in effect for 1. of the interval; 4. has no interval yet
    assert near( 5.0, w )
    assert near( 4.5, w.sample(  4.,  3. ))
    assert near( 4.5, w.sample(  6.,  3. ))     # Now 5. and 4. have been in effect for 1. (each); 6. has no interval yet
    assert near( 4.5, w )
    assert near( 5.0, w.sample(  6.,  4. ))
    assert near( 5.0, w.sample(  5.,  4. ))     # 4. and 6. now each in effect for 1.; 5. not yet
    assert near( 5.0, w.sample(  now=10. ))
    assert near( 5.0, w.sample(  now=12. ))     # Drops the 4. (but retains for time-weighted average!)
    assert near( 5.1, w.sample(  5., 13. ))     # Drops the 6. (but ...)
    assert near( 5.0, w.sample(  5., 14. ))     # Finally, only 5.'s in effect
    assert near( 5.0, w )

# Test the (best) weighted class.  Uses a weighted average of each sample, weighted by their
# duration vs. the total interval of the filter.  Until the initially specified time span is full of
# values, the average only reflects the shorter (actual) time span of the values specified thus far.
def test_weighted():
    w                   = filtered.weighted( 10., 0., 90. )
    assert near( 0.0000, w )
    assert len( w.history ) == 1
    assert near( w.interval, 10. )
    assert near( 0.5000, w.sample(  1.,  91. )) # 0.-->1.(.5) has interval of 1. (90. to 91.); 1.0 has no interval yet
    assert len( w.history ) == 2
    assert near( 1.2500, w.sample(  2.,  94. )) # 0.5 has interval of 1., 1.-->2.(1.5) has interval of 3. (91. to 94.) 5/4==1.25
    assert len( w.history ) == 3
    assert near( 2.0000, w.sample(  3., 100. )) # .5 x 1., 1.5 x 3., 2.5 x 6. == .5+4.5+15/10 == 2.0

    w                   = filtered.weighted( 10., 5., 1. )
    assert near( 5.00, w )                      # Single value so far
    assert near( 4.50, w.sample(  4.,  2. ))    # The 5.-->4. has now been in effect for 1. of the interval
    assert near( 4.50, w )
    assert near( 4.75, w.sample(  6.,  3. ))    # Now 5. and 4. have been in effect for 1. (each); followed by 6
    assert near( 4.75, w )
    assert near( 5.00, w.sample(  5.,  4. ))    # 4. and 6. now each in effect for 1.; now another 5.
    assert near( 5.00, w.sample(  now=10. ))    # (if no value provided, assumes no change since last value)
    assert near( 5.05, w.sample(  now=12. ))    # Drops the 4. (but retains for time-weighted average!)
    assert near( 5.05, w.sample(  now=13. ))    # Drops the 6. (but ...)
    assert near( 5.00, w.sample(  now=14. ))    # Finally, only 5.'s in effect
    assert near( 5.00, w )

def test_weighted_no_samples():
    w                   = filtered.weighted( 10., value=None, now=0. )
    assert w == None

    w.sample(1.0, now=1.)
    assert near( 1.0, w )

    w.sample(0.0, now=10.)
    assert near( 0.5, w )

# Test how sample intervals are handled by the various averaging
# classes, on both floating and integer samples.  Ensure that last
# sample always continues to apply after all samples pass out of
# interval window, and if the sample window is reduced to 0.
def test_intervals():
    av_i		= filtered.averaged( interval=10, now=0 )
    av_f		= filtered.averaged( interval=10, now=0 )
    ws_i		= filtered.weighted( interval=10, now=0 )
    ws_f		= filtered.weighted( interval=10, now=0 )
    wl_i		= filtered.weighted_linear( interval=10, now=0 )
    wl_f		= filtered.weighted_linear( interval=10, now=0 )
    for x in range( 0, 11 ):
        av_i.sample( value=100  + x, now=x )
        av_f.sample( value=100. + x, now=x )
        ws_i.sample( value=100  + x, now=x )
        ws_f.sample( value=100. + x, now=x )
        wl_i.sample( value=100  + x, now=x )
        wl_f.sample( value=100. + x, now=x )
    assert x == 10

    # Simple averaging includes the latest sample at full weight, and
    # discards the oldest sample as soon as it touches the end of the
    # time span.
    assert near( 105.50, av_i.compute( now=10 ))
    assert near( 106.50, av_i.sample( value=111,  now=11 ))

    assert near( 105.50, av_f.compute( now=10   )) # includes now==1, 2, 3, ... , 9, 10
    assert near( 105.50, av_f.compute( now=10.5 )) # includes now==2, 3, ... , 9, 10
    assert near( 106.00, av_f.compute( now=11   )) # includes now==3, ... , 9, 10
    assert near( 106.50, av_f.sample( value=111., now=11 )) # includes now==3, ... , 9, 10, 11

    assert near( 110.50, av_f.compute( now=19 )) # includes now==11
    assert near( 110.50, av_i.compute( now=19 ))
    assert near( 111.,   av_f.compute( now=20 )) # includes now==11
    assert near( 111.,   av_i.compute( now=20 ))
    assert near( 111.,   av_f.compute( now=21 )) # includes now==11
    assert near( 111.,   av_i.compute( now=21 ))

    # weighted includes all samples, using time weighted averaging
    # between each: (a+b)/2.  This means that new samples added will
    # cause a step-change jump when added (because the latest interval
    # will jump from being deemed a flat (say) 109.0 for the time
    # interval from 9-10, immediately to (say) 109.5 for that time
    # interval.  This is not "smooth" as time advances, and will not
    # be appropriate for all uses.  Remember, integer averaging always
    # rounds down.
    assert near( 105.0, ws_i.compute( now=10   ))  # includes now==1-2(101), ..., 4-5(104), 5-6(105), ..., 9-10(109)
    assert near( 106.0, ws_i.sample( value=111,  now=11 ))

    assert near( 105.00, ws_f.compute( now=10   )) # includes now==1-2(101.5), 2-3(102.5), 3-4, ..., 9-10(109.5)
    assert near( 105.475,ws_f.compute( now=10.5 )) # includes now==2-3(102.5), 3-4, ..., 9-10(109.5), 10-(110)
    assert near( 105.95, ws_f.compute( now=11   )) # includes now==2-3(102.5), 3-4, ..., 9-10(109.5), 10-(110)
    assert near( 106.00, ws_f.sample( value=111., now=11 )) # non-linear!

    assert near( 110.80, ws_f.compute( now=19 )) # includes now==11
    assert near( 110.80, ws_i.compute( now=19 ))
    assert near( 110.95, ws_f.compute( now=20 )) # includes now==11
    assert near( 110.95, ws_i.compute( now=20 ))
    assert near( 111.00, ws_f.compute( now=21 )) # includes now==11
    assert near( 111.00, ws_i.compute( now=21 ))

    # weighted_linear doesn't include a sample with a 0 time interval
    # (eg. the sample at now=10, with no elapsed time).  This means
    # that new samples will have *no* immediate effect on computed
    # average, and will smoothly begin to affect computed result as
    # time passes.  This is probably more appropriate for smoothly
    # changing time-based models.
    assert near( 104.50, wl_i.compute( now=10   )) # includes now==1, 2, 3, ... , 9
    assert near( 105.50, wl_i.sample( value=111,  now=11 ))

    assert near( 104.50, wl_f.compute( now=10   )) # includes now==1-2(101.), 2-3(102.), ... , 9-10(109.)
    assert near( 105.00, wl_f.compute( now=10.5 )) # includes now==2-3(102.), ... , 9-10(109.), 10-11(110.)
    assert near( 105.50, wl_f.compute( now=11   )) # includes now==2-3(102.), ... , 9-10(109.), 10-11(110.)
    assert near( 105.50, wl_f.sample( value=111., now=11 )) # smooth.

    assert near( 110.70, wl_f.compute( now=19 )) # includes now==11
    assert near( 110.70, wl_i.compute( now=19 ))
    assert near( 110.90, wl_f.compute( now=20 )) # includes now==11
    assert near( 110.90, wl_i.compute( now=20 ))
    assert near( 111.00, wl_f.compute( now=21 )) # includes now==11
    assert near( 111.00, wl_i.compute( now=21 ))

    wl_f.interval = 0
    wl_i.interval = 0
    assert near( 111.,   wl_f.compute( now=21 )) # includes now==11
    assert 	 111 ==  wl_i.compute( now=21 )




def test_NaN():
    # A NaN sample should cause any of the averaged classes to
    # .compute() NaN, after all relevant historical samples have
    # passed out of range.  This could be employed to indicate a
    # failed sensor after a specific period.  Otherwise, the last
    # known value would persist forever.
    unit_NaN(misc.value(value=None, now=0.)) # Try misc.value too
    unit_NaN(filtered.averaged(10., value=None, now=0.))
    unit_NaN(filtered.weighted_linear(10., value=None, now=0.))
    unit_NaN(filtered.weighted(10., value=None, now=0.))

def unit_NaN(w):

    assert w.compute(now=1.) is None

    assert near( 999., w.sample(999., now=1.))
    value = w.sample( 0., now=2.)
    #print value
    if hasattr( w, 'history'):
        assert 2 == len(w.history)
    value = w.sample( misc.nan, now=3.)
    #print value
    value = w.sample( misc.nan, now=10.)
    #print value
    value = w.sample( misc.nan, now=11.)
    #print value
    if hasattr( w, 'history' ):
        assert isinstance( value, float ) and not misc.isnan( value )
    value = w.sample( misc.nan, now=12.)
    #print value
    if hasattr( w, 'history') and not isinstance( w, filtered.averaged ):
        # Simple average is not inclusive of samples at the end of the range!  The otheer (weighted)
        # averages are inclusive (proportionally).
        assert isinstance( value, float ) and not misc.isnan( value )
    value = w.sample( misc.nan, now=13.)
    #print value
    assert isinstance( value, float ) and misc.isnan( value )

# 
# WARNING
# 
#     filtered.filter is obsolete; use filtered.averaged et. al. instead.
# 

# A simple summing filter over 10. time units, starting at time 0.
def test_filter():
    f                   = filtered.filter( 10., 0. )
    assert near( 0.0000, f.add(  0.,  90. ))
    assert near( 0.5000, f.add(  1.,  91. ))
    assert near( 1.0000, f.add(  2.,  94. ))
    assert near( 2.0000, f.add(  3., 100. ))

    f                   = filtered.filter( 10., 0. )
    assert near( 5.0, f.add(  5.,  1. ))
    assert near( 4.5, f.add(  4.,  2. ))
    assert near( 4.5, f.get(),         )
    assert near( 5.0, f.add(  6.,  3. ))
    assert near( 5.0, f.get()          )
    assert near( 5.0, f.add(  5.,  4. ))
    assert near( 5.0, f.add(  5., 10. ))
    assert 5 == len( f.history )
    assert near( 5.25,f.add(  5., 12. ))        # timestamps 3-12 now within interval 10; 1-2 drop off
    assert 4 == len( f.history )
    assert near( 5.0, f.add(  5., 13. ))        # 0 x 4, 4 x 5, 1 x 6
    assert near( 5.0, f.add(  5., 14. ))
    assert near( 5.0, f.get()         )

# A time-weighted filter over 10. time units, starting at time 0., and initial value 0.
def test_filter_weighted():
    f                   = filtered.filter( ( 10., 0. ), 0. )
    assert near( 0.0000, f.add(  0.,  90. ))
    assert near( 0.0000, f.add(  1.,  91. ))
    assert near( 0.3000, f.add(  2.,  94. ))
    assert near( 1.5000, f.add(  3., 100. ))

    f                   = filtered.filter( ( 10., 0. ), 0. )
    assert near( 0.0, f.add(  5.,  1. ))        # No effect 'til later; time-weighted samples have 0. time weight when first entered!
    assert near( 0.5, f.add(  4.,  2. ))        # The 5. has now been in effect for 1. of the interval 10.
    assert near( 0.5, f.get(),         )
    assert near( 0.9, f.add(  6.,  3. ))        # Now 5. and 4. have been in effect for 1. (each) of 10.
    assert near( 0.9, f.get(),         )
    assert near( 1.5, f.add(  5.,  4. ))
    assert near( 0.0, f.weighted );
    assert near( 4.5, f.add(  5., 10. ))
    assert near( 0.0, f.weighted );
    assert near( 5.0, f.add(  5., 12. ))        # Drops the 4. (but retains for time-weighted average!)
    assert near( 4.0, f.weighted );
    assert near( 5.1, f.add(  5., 13. ))        # Drops the 6. (but ...)
    assert near( 5.0, f.add(  5., 14. ))        # Finally, only 5.'s in effect
    assert near( 5.0, f.get(),         )

def test_filter_weighted_interval():
    f                   = filtered.filter( ( 10., 0. ), 0. )
    assert near( 0.0, f.add(  5.,  1. ))        # No effect 'til later; time-weighted samples have 0. time weight when first entered!
    assert near( 0.5, f.add(  4.,  2. ))        # The 5. has now been in effect for 1. of the interval 10.
    assert near( 0.9, f.add(  6.,  3. ))        # Now 5. and .4 have been in effect for 1. (each) of 10.
    assert len( f.history ) == 3
    # now, set the interval to 0, and test effects
    f.interval          = 0.
    assert near( 6.0,  f.get() )                # Should now be instantaneous value
    assert len( f.history ) == 3
    assert near( 7.0,  f.add( 7., 4. ))
    assert len( f.history ) == 1
    assert near( 7.0,  f.get() )
    assert near( 8.0,  f.add( 8., 5. ))
    assert near( 8.0,  f.get() )

