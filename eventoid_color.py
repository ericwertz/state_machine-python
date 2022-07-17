# eventoid_color.py -- event checker for the TCS34725 color sensor
#
# This eventoid replicates the content/analysis of the demo code provided with the driver
#   generalized a bit for easier tuning
#
# Events are generated when a single color is determined to be dominant-ish.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 04-May-2022 12:40

from machine import SoftI2C #FIXME Pin?
import time, eventoid

from tcs34725 import *

class EventoidColor(eventoid.Eventoid):
    """EventoidColor - generate events for independent g-values crossing a threshold in either axis"""

    def __init__(self, eventer, events_colors, tcs, sat_factor=1.45, halfwidth_satfactor=0.05, data=None):
        """
        EventoidColor - create obj for monitoring dominancy of a single (R|G|B) color         
        eventer - Eventer maintaining the queue of generated events
        events - triple of four tuples of (recognized,de-recognized) color threshold-exceeding/receeding events
                 to return for each color, in the order of (clear, red, green, blue), or None
        tcs - instance of driver object for color sensor
        data - optional data to return with event (current 4-tuple of color-values returned if None)
        """
        super().__init__(eventer, "color_TCS34725", True)

        if len(events_colors) != 3:
            raise FIXMEException("events_colors must have three components")
        self.events = events_colors
        self.tcs    = tcs

        self.sat_factor_high = sat_factor + halfwidth_satfactor
        self.sat_factor_low  = sat_factor - halfwidth_satfactor
        self.data            = data

        self.prev_color = None

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""

        return super().__repr__() + ",events=("+str(self.events)+\
               "),sats_f=("+str(self.sat_factor_low)+","+str(self.sat_factor_high)+"),sat_wid/2"+str(self.halfwidth_sat)+"),data="+str(self.data)

    def poll(self):
        """ poll(): poll object for eventable conditions.
                    Returns True to Eventer if an event was queued, else False. """

        evented = False
        t = time.ticks_ms()

        color_counts = list(tcs.colors[1:])     # get rid of unused "clear" data so that R,G,B indexes start at 0

        for count in color_counts:
            if count >= tcs.overflow_count:
                count = 0                       # toss value that overflowed
        largest_count = max(color_counts)             # largest R/G/B count
        largest_color = color_count.index(largest_count)
        avg_count     = sum(color_counts) // 3        # average of RGB counts

        data = color_counts if self.data is None else self.data

        if self.last_color is not None:
            # did previous color fall out of dominance?
            if color_counts[self.last_color] < int(avg * self.sat_factor_low):
                if (self.events[self.last_color] is not None) and (self.events[self.last_color][1] is not None):
                   self.eventer.add((self.events[self.last_color][1], t, data))     # send out-of-dominance event
                   self.last_color = None
                   evented = True

        if self.last_color is None:
            if largest_count > int(avg * self.sat_factor_high):
                # a color is now dominant, send event if we care about that color
                if (self.events[largest_color] is not None) and (self.events[largest_color][0] is not None):
                   self.eventer.add((self.events[largest_color][0], t, data))   # send new dominance event
                   self.last_color = largest_color
                   evented = True

        return evented
