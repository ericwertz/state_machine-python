# eventoid_lis3dh.py -- eventoid for the LIS3DH accelerometer
#
# Events are generated when at at least one axis crosses (one of) its specified
#   threshold value(s).
#
# See the class' docstring(s) for usage information.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 18-Sep-2022 21:55

from machine import ADC
import time, eventoid

NUM_AXES = 3    # X,Y,Z
G_MPS    = 9.8  # g in meters/sec^2

# index positions for RISING, FALLING
IDX_RISING  = 0
IDX_FALLING = 1

class EventoidLIS3DH(eventoid.Eventoid):
    """EventoidLIS3DH - generate events for g-values crossing any axis' threshold"""

    def __init__(self, eventer, events_axes, lis3dh):
        """
        EventoidLIS3DH - create obj for monitoring g-value of a single X|Y|Z axis.
        
        eventer - Eventer maintaining the queue of generated events
        events - triple of (rising,falling) tuples of events to return for each axis.
                 None may be specified for an to ignore within the triple.
                 None may be specified for either the rising or falling event to ignore
                 within the axis' tuple.
        lis3dh - accelerometer driver instance
        
        The event_data returned by this eventoid denotes the axis (0=X, 1=Y, and 2=Z)
        that has alarmed or idled by passing through the threshold value/band.
        
        If multiple axes cross their thresholds in one poll cycle, each will generate
        its own event with the same timestamp.
        """
        super().__init__(eventer, "LIS3DH", True)

        if len(events_axes) != NUM_AXES:
            raise EventoidException("events_axes must have three components")
        ev_temp = list()
        
        has_event = False
        for i in range(NUM_AXES):
            events = (None,None) if events_axes[i] is None else events_axes[i]
            if len(events) != 2:
                raise EventoidException("axis="+i+" event must be 2-tuple!")
            ev_temp.append(events)
            if (events[0] is not None) or (events[1] is not None):
                has_event = True
            
        if not has_event:
            raise EventoidException("events_axes must have three components")
        
        self.events = tuple(ev_temp)

        self.lis3dh      = lis3dh
        self.threshold_g = None
        self.halfwidth_g = None
        self.prev_alarm  = [False, False, False]

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""

        return super().__repr__() + ",events=("+str(self.events)+\
               "),g_thr=("+str(self.threshold_g)+",g_wid/2"+str(self.halfwidth_g)+")"

    def set_thresholds_g(self, thresholds_g):
        """thresholds_g - triple of center-of-hysteresis-band g-values for thresholding each axis"""

        if len(thresholds_g) != NUM_AXES:
            raise BadParamFIXMEException("set_thresholds_g()")
        self.threshold_g = thresholds_g

        g = self.lis3dh.acceleration
        for axis in range(NUM_AXES):
            self.prev_alarm[axis] = (g[axis] >= self.threshold_g[axis])

    def set_halfwidths_g(self, halfwidths_g=None):
        """halfwidths_g - per-axis triple of g-values above and below threshold for hysteresis band"""

        if halfwidths_g is None:
            self.halfwidth_g = (0.0, 0.0, 0.0)
        else:
            if len(halfwidths_g) != NUM_AXES:
                raise Exception("set_halfwidths_g() param != "+NUM_AXIS)
            self.halfwidth_g = tuple(halfwidths_g)

    def poll(self):
        """ poll(): poll object for eventable conditions.
                    Returns True to Eventer if an event was queued, else False. """

        if (self.threshold_g is None) or (self.halfwidth_g is None):
            Exception("threshold info not set")

        evented = False
        t = time.ticks_ms()
        g = self.lis3dh.acceleration

        for axis in range(NUM_AXES):
            g_axis = g[axis] / G_MPS
            if (g_axis > self.threshold_g[axis]+self.halfwidth_g[axis]) and not self.prev_alarm[axis]:
                self.eventer.add((self.events[axis][IDX_RISING], t, axis))
                self.prev_alarm[axis] = True
                evented = True
            elif (g_axis < self.threshold_g[axis]-self.halfwidth_g[axis]) and self.prev_alarm[axis]:
                self.eventer.add((self.events[axis][IDX_FALLING], t, axis))
                self.prev_alarm[axis] = False
                evented = True

        return evented
