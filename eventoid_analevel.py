# eventoid_analevel.py -- event checker for crossing of an analog threshold
#
# Events can be generated by both rising and falling through the specified threshold
# level, measured in ADC counts, as this the width of the hysteresis band on each side
# of the threshold.
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 19-Apr-2022 23:18

from machine import ADC
import time, eventoid

class EventoidAnalogLevel(eventoid.Eventoid):
    """EventoidAnalogLevel - generate events for bi-directional crossing over an analog threshold value."""

    def __init__(self, eventer, events, adc, adc_threshold, half_width=0, data=None):
        """
        EventoidAnalogLevel - create obj for monitoring bi-directional crossing over an analog threshold.
        
        eventer - Eventer maintaining the queue of generated events
        events - tuple of (rising,falling) events to return
        adc - instance of machine.ADC to poll
        adc_threshold - center ADC value for thresholding
        half_width - ADC counts above and below threshold for hysteresis band
        data - optional data to return with event
        """
        super().__init__(eventer, "analevel", True)

        if half_width is None: half_width = 0

        (self.event_rising,self.event_falling) = events
        self.adc       = adc
        self.band_low  = adc_threshold - half_width
        self.band_high = adc_threshold + half_width
        self.level     = 1 if adc.read_u16() >= adc_threshold else 0
        self.data      = data

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""
        return super().__repr__() + ",events=("+str(self.event_rising)+","+str(self.event_falling)+\
               "),band=("+str(self.band_low)+","+str(self.band_high)+"),prev="+str(self.level)+",data="+str(self.data)

    def poll(self):
        """ poll(): poll object for eventable conditions.  Returns True to Eventer if an event was queued, else False. """

        val = self.adc.read_u16()
        t   = time.ticks_ms()
        evented = False
        if (val <= self.band_low) and (self.level == 1):
            self.level = 0
            self.eventer.add((self.event_falling, t, self.data))
            evented = True
        elif (val >= self.band_high) and (self.level == 0):
            self.level = 1
            self.eventer.add((self.event_rising, t, self.data))
            evented = True

        return evented