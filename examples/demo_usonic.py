# demo_uson2z_demo.py: demo program alerting at two distances with an ultrasonic sensor
#
# This program demonsrates using a state-machine based program with an ultrasonic
#   sensor using the two zone-boundary (warning/alarm) ultrasonic sensor eventoid.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 03-May-2022 12:56

from machine  import Pin
from eventer  import Eventer
from sm_light import Light
import hc_sr04_edushields

from eventoid_uson2z import EventoidUsonic2ZonesPolled
from eventoid_timer  import EventoidTimerPolled

TRACE_STATES = True

LINGERING_MSECS = const(5000)   # tolerate these msecs in NEAR zone before countermeasures/alarms

PIN_NEOPIXEL = const(28)    # the Neopixel is now the light source
ORDER_colorS = "GRB"        # this WS2812B flavor takes green, red, then blue data
SM_NEOPIXEL  = const(0)     # which PIO-SM to use (needed by neopixel library)

COLOR_RED    = (255,   0, 0)
COLOR_YELLOW = (255, 150, 0)
COLOR_GREEN  = (  0, 255, 0)

PIN_LASER = const(0)        # countermeasure weapon

# States of the state machine
STATE_FAR      = const(0)   # object outside of outer zone
STATE_OUTER    = const(1)   # object in outer/warning zone
STATE_INNER    = const(2)   # object in inner/danger zone
STATE_ALARMING = const(3)   # object in inner/danger zone for more than LINGERING_MSECS

STATE_STR = { STATE_FAR:      'STATE_FAR',
              STATE_OUTER:    'STATE_OUTER',
              STATE_INNER:    'STATE_INNER',
              STATE_ALARMING: 'STATE_ALARMING'}

# Events returned from all of our eventoids
EVENT_ENTERING_OUTER = const(0)  # occurs when entering OUTER from FAR
EVENT_EXITING_OUTER  = const(1)  # occurs when exiting  OUTER into FAR
EVENT_ENTERING_INNER = const(2)  # occurs when entering INNER from OUTER
EVENT_EXITING_INNER  = const(3)  # occurs when exiting  INNER into OUTER
EVENT_LINGERING_NEAR = const(4)  # occurs after LINGERING_MSECS in INNER zone

EVENT_STR = { EVENT_ENTERING_OUTER: 'EVENT_ENTERING_OUTER',
              EVENT_EXITING_OUTER:  'EVENT_EXITING_OUTER',
              EVENT_ENTERING_INNER: 'EVENT_ENTERING_INNER',
              EVENT_EXITING_INNER:  'EVENT_EXITING_INNER',
              EVENT_LINGERING_NEAR: 'EVENT_LINGERING_NEAR' }

PIN_USON_TRIGGER = const(7)   # The Seeed/Grove sensor only has one pin
PIN_USON_ECHO    = const(7)

DISTANCE_OUTER_MM         = const(300)  # mm to outer/warning zone
DISTANCE_INNER_MM         = const(150)  # mm to inner/danger  zone
DISTANCE_RANGE_CUTOFFS_MM = (100, 1000) # toss all ultrasonic values outside of this range
DISTANCE_HYSTERESIS_MM    = const(5)    # hysteresis band on each side of inner/outer distance values
DISTANCE_DEBUG_MM         = None        # movement threshold in mm to test ranging, or None to turn off

usonic = hc_sr04_edushields.HCSR04(PIN_USON_TRIGGER, PIN_USON_ECHO)
light  = Light(PIN_NEOPIXEL, ORDER_colorS, SM_NEOPIXEL, duty=0)
laser  = Pin(PIN_LASER, Pin.OUT)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_uson2z = EventoidUsonic2ZonesPolled(
                    eventer,
                    usonic,
                    DISTANCE_RANGE_CUTOFFS_MM,
                    ( (DISTANCE_OUTER_MM, (EVENT_ENTERING_OUTER,EVENT_EXITING_OUTER)),
                      (DISTANCE_INNER_MM, (EVENT_ENTERING_INNER,EVENT_EXITING_INNER)) ),
                    DISTANCE_HYSTERESIS_MM,
                    DISTANCE_DEBUG_MM)
eo_timer = EventoidTimerPolled(eventer, EVENT_LINGERING_NEAR)
_ = eventer.register(eo_uson2z)
_ = eventer.register(eo_timer)

def countermeasures_start(): laser.on()
def countermeasures_stop():  laser.off()

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    if state == STATE_FAR:
            if   event == EVENT_ENTERING_OUTER:
                                    light.set_color(COLOR_YELLOW)
                                    return STATE_OUTER
            elif event == EVENT_ENTERING_INNER:
                                    light.set_color(COLOR_RED)
                                    return STATE_ALARMING
            else:
                                    eventer.err_unexpected_event(state, event, event_data)
    elif state == STATE_OUTER:
            if   event == EVENT_EXITING_OUTER:
                                    light.set_color(COLOR_GREEN)
                                    return STATE_FAR
            elif event == EVENT_ENTERING_INNER:
                                    light.set_color(COLOR_RED)
                                    eo_timer.start(LINGERING_MSECS)
                                    return STATE_INNER
            else:
                                    eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_INNER:
            if   event == EVENT_EXITING_INNER:
                                    eo_timer.cancel()
                                    light.set_color(COLOR_YELLOW)
                                    return STATE_OUTER
            elif event == EVENT_EXITING_OUTER:
                                    eo_timer.cancel()
                                    light.set_color(COLOR_GREEN)
                                    return STATE_FAR
            elif event == EVENT_LINGERING_NEAR:
                                    countermeasures_start()
                                    return STATE_ALARMING
            elif event == EVENT_ENTERING_OUTER:
                                    print("WTF:Inner-<EntOuter!")
                                    return state
            else:
                                    eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_ALARMING:
            if   event == EVENT_EXITING_INNER:
                                    countermeasures_stop()
                                    light.set_color(COLOR_YELLOW)
                                    return STATE_OUTER
            elif event == EVENT_EXITING_OUTER:
                                    countermeasures_stop()
                                    eo_timer.cancel()
                                    light.set_color(COLOR_GREEN)
                                    return STATE_FAR
            else:
                                    eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

light = Light(PIN_NEOPIXEL, ORDER_colorS, SM_NEOPIXEL, duty=0)
light.set_duty(50)
countermeasures_stop()

eventer.loop(event_process, STATE_FAR)
