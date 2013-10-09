import math
import collections

import web

from misc import scale
import pid

def linear( t, duration, interval ):
    beg,end		= interval
    return beg + (end-beg) * t/duration

def exponential( t, duration, interval ):
    beg,end		= interval
    root		= math.sqrt( end-beg )
    return beg + linear( t, duration, (0,root) ) ** 2

def normalize( value, target, reverse=False ):
    dom			= (0.0, target)
    rng			= (0.0, 1.0)
    if not reverse:
        return scale( value, dom, rng )
    return scale( value, rng, dom )


trend			= {}

class history( object ):
    def __init__( self, sunset=None, interval=1./60/60/10 ):
        """Collect samples on minimum (default) 1/10th second intervals."""
        self._interval	= interval
        self._sunset	= sunset
        self._values	= collections.deque()

    def sunset( self, now ):
        if not self._sunset:
            return
        while self._values and self._values[0][0] < now - self._sunset:
            self._values.popleft()

    def sample( self, now, value ):
        if self._values and self._values[-1][0] < now - self._interval:
            self._values.append( (now,value) )
        self.sunset()

    @property
    def values( self ):
        return self._values


def simulate( security, duration=1000, price_interval=(10.00, 1000.00) ):

    trend.setdefault( security, history() )

    target		= lambda t: exponential( t, duration, price_interval )

    start		= 0        # hours
    dt			= 1./60/60 # seconds
    P_event		= 1./2     # events/hour
    velocity		= 10.0	   # $/h
    accel		= 0.0      # $/h/h
    price		= target( start )
    now			= start

    # We will transform the current price and target such that $0.00 is 0.0, and target is 1.0.
    control         	= pid.controller(
        Kpid    = ( .01, .000001, 20.0 ),
        setpoint= 1.0, # filtered.weighted_linear( now=now, interval=0., value=1.0 ),
        process = 1.0, # filtered.weighted_linear( now=now, interval=0., value=1.0 ),
        output  =  0.0,
        now     =  start )

    print
    print "%8.8s %7.7s %7.7s %7.7s %7.7s %7.7s %7.7s %7.7s %7.7s %7.7s" % (
        "time", "target", "price", "veloc.", "event", "accel.", "P", "I", "D", "thrust" )

    last		= None
    while now < start + duration:
        now	       += dt

        velocity       += accel*dt

        price	       += velocity*dt
        
        
        goal		= target( now ) # What the price should be

        setpoint	= 1.0
        process		= normalize( price, target=goal )
        thrust		= control.loop( setpoint=1.0, process=process, now=now )
                                        
        # in $/hr/hr; next sample period's acceleration
        accel          += normalize( thrust, target=goal, reverse=True )*dt

        hour		= int( now )
        minute		= int( now * 60 % 60 )
        second		= int( now * 60 * 60 % 60 )

        if minute != last:
            event	= 0
            if 0 == random.randrange( 0, int( P_event * 60 )):
                # Once every few minutes, add a random acceleration
                event	= random.gauss( 0, 1 ) * price/10
            velocity   += event

            print "%02d:%02d:%02d %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f" % (
                hour, minute, second,
                goal, #control.setpoint, # .compute(now=now),
                price, #control.process,  # .compute(now=now), 
                velocity, event, accel,
                control.P, control.I, control.D, thrust )
            last	= minute


def data_request( path, queries, environ, accept, framework ):
    """
    Returns data, as HTML or JSON.

        api/data		-- all 
        api/data/Air		-- by description (partial match)

    """
    # When using jQuery $.ajax() w/dataType: 'jsonp', it appends a
    # ?callback=... query, and sends an Accept: ... text/javascript
    # header.  Hence, accept either form.
    content			= deduce_encoding( [ "text/html",
                                                     "application/json", "text/javascript",
                                                     "text/plain" ],
                                                   environ=environ, accept=accept )
    response			= ""

    data			= {}
    data["title"]		= "Sensors"
    data["path"]		= path
    data["list"] = sl		= []
    data["keys"]		= ["description", "family", "id", "value"]

    global sensor
    for desc in sorted( sensor.keys(), key=misc.natural):
        sens		= sensor[desc]
        if not path or path in desc or path == sens.id:
            value	= sens.compute( max( timer(), sens.now ))
            sl.append( {
                    "description":	desc,
                    "family":		sens.family,
                    "id":		sens.id,
                    "value":		value,
                    } )

    if content and content in ( "application/json", "text/javascript", "text/plain" ):
        callback		= queries.get( 'callback', "" ) if queries else ""
        if callback:
            response           += callback + "( "
        response               += json.dumps( data, indent=4 )
        if callback:
            response           += " )"
    elif content and content in ( "text/html" ):
        render			= framework.template.render( "static/resources/templates/", base="layout" )
        response		= render.keylist( data )
    else:
        raise http_exception( framework, 406, "Unable to produce %s content" % (
                content or accept or "unknown" ))

    return content, response


def http( address=("0.0.0.0", 8000) ):
    import socket
    import web
    import wsgilog
    def proxy( env ):
        """Detects if we are behind a proxy, and creates correct path if
        necessary, to use the original forwarded host."""
        proxy			= env.get( "HTTP_X_FORWARDED_HOST", "" )
        if proxy:
            proxy		= "http://" + proxy
        return proxy

    urls			= (
        "/",			"home",
        "/(.*)/",		"trailing_slash",
        "/index.html",		"index",
        "/login",		"login",
        "/logout",		"logout",
        "/api/data(.json)?",	"data",                 # path: "", ".json"
        "/api/data/(.+$)",	"data",                 # path: ...
    )

    class trailing_slash:
        def GET( self, path ):
            web.header( "Cache-Control", "no-cache" )
            web.seeother( proxy( web.ctx.environ ) + '/' + path )

    class home:
        def GET( self ):
            web.header( "Cache-Control", "no-cache" )
            web.seeother( proxy( web.ctx.environ ) + "/index.html" )

    class index:
        def GET( self ):
            render		= web.template.render( "static/resources/templates/",
                                                       base="layout" )
            response		= render.index( {"title": "Home" } )
            web.header( "Content-Type", "text/html" )
            return response

    class data:
        def GET( self, path ):
            accept		= None
            if path and path.endswith( ".json" ):
                path		= path[:-5]		# clip off ".json"
                accept		= "application/json"

            # Always returns a content-type and response.  If an exception is
            # raised, it should be an appropriate one from the supplied framework to
            # carry a meaningful HTTP status code.  Otherwise, a generic 500 Server
            # Error will be produced.
            content, response	= data_request(
                path=path, queries=web.input(), environ=web.ctx.environ,
                accept=accept, framework=web )
            web.header( "Cache-Control", "no-cache" )
            web.header( "Content-Type", content )
            return response


    class Log( wsgilog.WsgiLog ):
        def __init__( self, application ):
            """Set up logging, and then make sure sys.stderr goes to whereever
            sys.stdout is now going.  This ensures that environ['wsgi.errors']
            (which is always set to sys.stderr by web.py) goes to the log file; this
            is used to log each incoming HTTP request.  After setup, disable
            logging, 'til our first WSGI call is made (the bind to server address
            has succeeded).
    
            We want to be able to try to bind, and fail -- producing only
            sys.stdout/stderr output.  When the first WSGI call is made,
            then enable logging.  This may let a few log messages through,
            because we don't handle /static/... URLs, so our wsgi middleware
            doesn't get called 'til we handle something....
            """
            wsgilog.WsgiLog.__init__(
                self, application,
                logname		= "",
                loglevel	= level,		# Closure captures 'level'!
                tohtml		= True,			# Exceptions generate HTML
            )
            self.log		= False
    
        def __call__( self, *args ):
            if not self.log:
                # Enable interception of stdout/stderr at logging.INFO level
                # (eg. logging of URLs served by web.py)
                self.log	= True
                sys.stdout	= wsgilog.LogStdout( self.logger, logging.DEBUG )
                sys.stderr	= sys.stdout
            return wsgilog.WsgiLog.__call__( self, *args )

    # Get the required web.py classes from the local namespace.  The
    # iface:port must always passed on argv[1] to use app.run(), so use
    # lower-level web.httpserver.runsimple interface.  This sets up the
    # WSGI middleware chain, prints the address and then invokes
    # httpserver.WSGIserver.start(), which does the bind, and then makes
    # WSGI calls (enabling our logging, above).
    app			= web.application( urls, locals() )
    web.httpserver.runsimple( app.wsgifunc( Log ), address )

def main():
    # Parse args
    parser			= argparse.ArgumentParser(
        description = "Provide HTTP access to simulated market data",
        epilog = "" )

    # -v[v...]/--verbose
    parser.add_argument( '-v', '--verbose',
                         default=2, action="count",
                         help="Display logging information." )
    parser.add_argument( '-a', '--address',
                         default="0.0.0.0:8000",
                         help="Default interface[:port] to bind to (default: all, port 8000)" )
    parser.add_argument( '-l', '--log',
                         default=None,
                         help="Log file, if desired" )
    args			= parser.parse_args()

    def parse_address( address, port=80 ):
        parts			= address.split(':')
        assert 1 <= len( parts ) <= 2
        return ( str( parts[0] ),
                 int( parts[1] ) if len( parts ) > 1 else port )
    
    # Deduce logging level and target file (if any)
    # 
    # web.py sets up logging, and then prints (hence logs) the address it is
    # about to bind to before it actually binds.  Thus, if another server is
    # already running on the port, the bind fails -- but output has already been
    # logged to the same log file destination, disturbing the log file.  So,
    # create a Wsgi Middleware that intercepts logging, and only sets up a
    # wsiglog.LogStdout interceptor at the first actual Wsgi call (ie. *after*
    # successfully setting up the web server.)
    # 
    levelmap 			= {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        }
    level			= ( levelmap[args.verbose] 
                                    if args.verbose in levelmap
                                    else logging.DEBUG )
    logger			= logging.getLogger("")
    handler			= ( logging.StreamHandler()
                                    if not args.log
                                    else logging.handlers.RotatingFileHandler(
                                            args.log, maxBytes=10*1024*1024, backupCount=5 ))
    formatter			= logging.Formatter( "%(asctime)s %(name)-12s %(levelname)-8s %(message)s" )
    handler.setFormatter( formatter )
    logger.addHandler( handler )
    logger.setLevel( level )

    logging.error( "Starting; log level: %d" % ( level ))


if __name__ == "__main__":
    main()
