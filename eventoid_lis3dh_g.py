# eventoid_lis3dh.py -- event checker for the LIS3DH accelerometer
#
# Events are generated when a single axis exceeds a given threshold value.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 26-Apr-2022 14:30

from machine import ADC
import time, eventoid

class EventoidLIS3DH_g(eventoid.Eventoid):
    """EventoidLIS3DH_1axis - generate events for independent g-values crossing a threshold in either axis"""

    def __init__(self, eventer, events_axes, lis3dh, data=None):
        """
        EventoidLIS3DH_1axis - create obj for monitoring g-value of a single X|Y|Z axis.
        
        eventer - Eventer maintaining the queue of generated events
        events - triple of tuples of (rising,falling) events to return for each axis,
                 or None for any axis or edge in axis
        lis3dh - instance of driver object for accelerometer
        data - optional data to return with event (current triple of g-values return if None)
        """
        super().__init__(eventer, "LIS3DH_g", True)

        if len(events_axes) != 3:
            raise FIXMEException("events_axes must have three components")
        ev_temp = list()
        for i in range(3):
            ev_temp.append((None,None) if events_axes[i] is None else events_axes[i])
        self.events = tuple(ev_temp)

        self.lis3dh = lis3dh

        self.threshold_g = None
        self.halfwidth_g = None
        self.data        = data

        self.prev_level  = None

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""

        return super().__repr__() + ",events=("+str(self.events)+\
               "),g_thr=("+str(self.threshold_g)+",g_wid/2"+str(self.halfwidth_g)+"),data="+str(self.data)

    def set_thresholds_g(self, thresholds_g):
        """thresholds_g - triple of center g-values for thresholding for each axis"""

        if len(thresholds_g) != 3:
            raise BadParamFIXMEException("set_thresholds_g()")
        self.threshold_g = thresholds_g

        if self.prev_level is None: self.prev_level = [0, 0, 0]

        g = self.lis3dh.acceleration
        for axis in range(3):
            self.prev_level[axis] = 0 if g[axis] < self.threshold_g[axis] else 1

    def set_halfwidths_g(self, halfwidths_g=None):
        """halfwidths_g - triple of g-value above and below threshold for hysteresis band for each axis"""

        if halfwidths_g is None:
            self.halfwidth_g = (0.0, 0.0, 0.0)
        else:
            if len(halfwidths_g) != 3:
                raise BadParamFIXMEException("set_halfwidths_g()")
            self.halfwidth_g = tuple(halfwidths_g)

    def poll(self):
        """ poll(): poll object for eventable conditions.
                    Returns True to Eventer if an event was queued, else False. """

        if (self.threshold_g is None) or (self.halfwidth_g is None):
            Exception("threshold info not set")

        evented = False
        t = time.ticks_ms()
        g = self.lis3dh.acceleration

        ev_axis = list()

        for axis in range(3):
            if   (g[axis] > self.threshold_g[axis]+self.halfwidth_g[axis]) and (self.prev_level[axis] == 0):
                self.eventer.add((self.events[axis][0], t, g[axis] if self.data is None else self.data))
                self.prev_level[axis] = 1
                evented = True
            elif (g[axis] < self.threshold_g[axis]-self.halfwidth_g[axis]) and (self.prev_level[axis] == 1):
                self.eventer.add((self.events[axis][1], t, g[axis] if self.data is None else self.data))
                self.prev_level[axis] = 0
                evented = True

        return evented
