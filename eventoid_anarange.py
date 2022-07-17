# eventoid_anarange.py -- generate events for subdivided analog range (can simulate rotary encoder)
#
# FIXME: hysteresis width not configurable
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 19-Apr-2022 23:23

from machine import ADC
import time, eventoid

HYSTERESIS_LEVEL_FRACT = const(5)  # top and bottom 1/5 of subdivision for hysteresis

ANALOG_MAX = const((2**16)-1)

class EventoidAnalogMultirange(eventoid.Eventoid):
    """
    EventoidAnalogMultirange - generate events for subdivided analog ranges (can simulate rotary encoder)
    """
    def __init__(self, eventer, events, adc, levels, data=None):
        """
        EventoidAnalogMultirange - create obj for monitoring subdivided analog range
        
        eventer - Eventer maintaining the queue of generated events
        events - tuple of (rising,falling) events to return
        adc - instance of machine.ADC to poll
        levels - number of subdivisions within ADC range
        data - optional data to return with event
        """
        super().__init__(eventer, "anarange", True)

        (self.event_up,self.event_down) = events
        self.adc    = adc
        self.levels = levels
        self.width  = (int)(ANALOG_MAX/levels)
        self.margin = self.width // HYSTERESIS_LEVEL_FRACT # hysteretic dead-zone top/bottom 20% of the level width
        self.level  = EventoidAnalogMultirange._get_level(adc.read_u16(), levels-1, self.width, self.margin)[0]
        self.data   = data

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""
        return super().__repr__() + ",events=("+str(self.event_up)+","+str(self.event_down)+"),levels="+str(self.levels)+\
               "width="+str(self.width)+",margin="+str(self.margin)+",level="+str(self.level)+",data="+str(self.data)

    def _get_level(adcval, max_level, width, margin):
        lvl = adcval // width
        if lvl > max_level: return (max_level, 1)
        if lvl < 0        : return (0, -1)

        n = adcval  % width
        if adcval < margin:
            sublvl = -1
        elif adcval > (width-margin):
            sublvl = 1
        else:
            sublvl = 0
        return (lvl, sublvl)

    def poll(self):
        """ poll(): poll object for eventable conditions.  Returns True to Eventer if an event was queued, else False. """
        evented = False
        val = self.adc.read_u16()
        t   = time.ticks_ms()
        (lev, sublev) = EventoidAnalogMultirange._get_level(val, self.levels-1, self.width, self.margin)

        while lev != self.level:
            if lev == self.level+1:
                if sublev >= 0:   # mid-range or higher
                    self.level = lev
                    self.eventer.add((self.event_up, t, self.level if self.data is None else self.data))
                    evented = True
                break
            elif lev == self.level-1:
                if sublev <= 0:   # mid-range or lower
                    self.level = lev
                    self.eventer.add((self.event_down, t, self.level if self.data is None else self.data))
                    evented = True
                break
            else:
                if lev > self.level+1:
                    self.level += 1
                    self.eventer.add((self.event_up, t, self.level if self.data is None else self.data))
                    evented = True
                elif lev < self.level-1:
                    self.level -= 1
                    self.eventer.add((self.event_down, t, self.level if self.data is None else self.data))
                    evented = True
