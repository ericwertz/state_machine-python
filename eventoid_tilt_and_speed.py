# eventoid_tilt_and_speed.py -- event checker for fusing of speed and tilt sensor data
#
# This eventoid isn't very useful in this form, but it an example of how one could fuse-
# together data from two different sensors into one eventoid.  It has a bunch of FIXMEs in
# it where you have to change the code to behave sensibly, but out-of-the-box code path
# does a lot # of fakery, or silly things, instead.
#
# The first "sensor" is connected to a GPIO pin.  You *could* connect it to a pulse counter,
# but this implementation assumes that falling edges denote a 10-unit decrease in speed.  THe
# represented speed value oscillates over a sequences of presses between a maximum value and
# a minimum value.  You need to replace that with code to make it useful.
# This GPIO pin is set up to use interrupts.  On every interrupt you re-compute the input
# speed and remember it for use by the code that does the eventing logic.  This interrupt
# path does NOT generate events, only the polling path (described below) does.  This was
# a design choice, but isn't necessary.  If you call the poll() path frequently enough,
# you can get by with eventing from poll() rather than both there and/or in the ISR.  It
# could be done however/wherever you'd like.
#
# The second sensor is a LIS3DH accelerometer that we use to compute some sort of "tilt".
# This implementation uses fake math and just the Y-axis to derive this fake tilt value.
# This is the sensor that is the body of the eventoid.  The poll function gets called
# to force the accelerometer to get read to figure out what the "tilt" value is, and uses
# it with the speed value that the ISR maintains to decide if the combo is worth of generating
# an event over.  To know if you've crossed a threshold you have to know what the previous state
# as for comparison purposes (just like the ISR has to remember when the previous pulse came in).
#
# Events are generated when a measure of a combination of fake speed and fakely-computed tilt
# bi-directionally cross a threshold.  This demo version compares the speed to the angle from the
# horizontal to determine whether one is in or out of the safe operating range.  As long as the
# speed doesn't exceed the angle, you're good.  For example, you can go up to speed=90 when the
# tilt (actually, angle from the cartesian origin theta=0) is 90 (fake degrees), but when you're
# horizontal (tilt=0) there's no safe operating speed >0 that it's safe to go because you'd be
# getting dragged across the ground.  Similarly, you're allowed to go up to speed=45 when tilt=45,
# and vice-versa.
#
# It's a silly example eventoid as written, but demonstrates how to fuse two sensors, with one
# that happens to use polling, and one that happens to use interrupts.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 27-Apr-2022 19:14

from machine import ADC, Pin
import time, eventoid

FAKE_SPEED_CHANGE_BEHAVIOR = True  # turn this off (or nuke its code) once you start pulse counting/measuring

class EventoidTiltAndSpeed(eventoid.Eventoid):
    """EventoidLIS3DH_1axis - generate events for independent g-values crossing a threshold in either axis"""

    def __init__(self, eventer, events, lis3dh, pin_pulse):
        """
        EventoidTiltAndSpeed - create obj for eventing based on tilt and speed
        
        eventer - Eventer maintaining the queue of generated events
        events - tuple of (becoming_safe,becoming_dangerous) threshold-crossing events
        lis3dh - instance of driver object for LIS3DH accelerometer
        pin_pulse - Pin object for detecting input frequency pulses
        data - optional data to return with event
        """
        super().__init__(eventer, "tilt_and_speed", True)

        self.events    = events
        self.lis3dh    = lis3dh
        self.pin_pulse = pin_pulse

        self.t_prev_pulse_ms = 0      # this is when we saw the previous Hall pulse
        self.was_in_danger   = False  # remember previous condition for comparison to now
        
        self.tilt  = EventoidTiltAndSpeed._compute_tilt(lis3dh) # most recent tilt  calculation result
        self.speed = 0                                          # most recent speed calculation result

        pin_pulse.irq(trigger=Pin.IRQ_FALLING, handler=self._isr_pulse)  # enable ISR for Hall pulses

    def __repr__(self):
        """ __repr__(): Return printable obj representation"""

        return super().__repr__() + ",event(now_safe,now_danger)=("+str(self.events)+\
               "),t_prev=("+str(self.t_prev_pulse_ms)+",was="+str(self.was_in_danger)+\
               ",spd="+str(self.speed)+",tilt="+str(self.tilt)

    def _isr_pulse(self, pin):
        """ _isr_pulse: ISR for Hall sensor
                        computes current speed from time between the last two pulses"""
        if FAKE_SPEED_CHANGE_BEHAVIOR:
            FAKE_SPEED_MIN =   0
            FAKE_SPEED_MAX =  91
            FAKE_SPEED_INCR=  10
            # ugly hack: speeds ending in 0 are rising, in 1 are decreasing
            if (self.speed % 10) == 0:
                self.speed = min(self.speed+FAKE_SPEED_INCR, FAKE_SPEED_MAX)
            else:
                self.speed = max(self.speed-FAKE_SPEED_INCR, FAKE_SPEED_MIN)
        else:
            t = time.ticks_ms()
            t_diff_ms = t - self.t_prev_pulse_ms
            self.speed = FIXME  # do math here to do a real speed calculation
            self.t_prev_pulse_ms = t
 
    def set_speed(self, speed):
        """ set_speed(): TEST USE ONLY: set the absolute speed for testing purposes (perhaps using a periodic timer)"""
        self.speed = speed
                           
    def set_tilt(self, tilt):
        """ set_tilt(): TEST USE ONLY: set the tilt for testing purposes (perhaps instead of a real accelerometer)"""
        self.tilt = tilt

    def _compute_tilt(acc):
        (gx, gy, gz) = acc.acceleration

        # FIXME placeholder for tilt angle measured from the *horizontal* using just the y-axis
        gy_bounded = max(0, min(gy, 9.8))
        return gy_bounded * 9.184  # 9.184 = 90/9.8

    def poll(self):
        """ poll(): poll object for eventable conditions.  Based on the continuously updated
                    speed value maintained by the ISR and the current level of tilt
                    generate events based on whatever *changes* warrant it.
                    Returns True to Eventer if an event was queued, else False. """

        evented = False
        t = time.ticks_ms()

        self.tilt = EventoidTiltAndSpeed._compute_tilt(self.lis3dh)

        # FIXME placeholder fake tilt computation, with a +/- 10% thick hysteresis band
        if self.speed > (self.tilt * 1.1):   # DANGEROUS range of operation
            if not self.was_in_danger:
                # it's now dangerous, but it wasn't before
                self.eventer.add((self.events[1], t, (self.tilt,self.speed))) # FIXME provide event_data makes sense to you
                evented = True
            self.was_in_danger = True
        elif self.speed < (self.tilt * 0.9): # SAFE range of operation
            if self.was_in_danger:
                # it's not dangerous now, but it was
                self.eventer.add((self.events[0], t, (self.tilt,self.speed))) # FIXME (same as above)
                evented = True
            self.was_in_danger = False
        else:
            pass  # nothing changed enough to warrant an event

        return evented
