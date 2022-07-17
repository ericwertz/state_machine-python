# demo_color.py: demo program detecting color predominancy change events
#
# This program demonsrates using a state-machine based program with an ultrasonic
#   sensor using the two zone-boundary (warning/alarm) ultrasonic sensor eventoid.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 03-May-2022 18:00

from machine  import Pin
from eventer  import Eventer
from sm_light import Light

from eventoid_color import EventoidColor
from eventoid_timer import EventoidTimerPolled

TRACE_STATES = True

REASSESS_MSECS = const(5000)   # recheck sensor value for persistence after this time

PIN_LASER = const(0)

# States of the state machine
STATE_STOPPED  = const(0)   # waiting for the green light
STATE_RUNNING  = const(1)   # running until red light or we decide otherwise

STATE_STR = { STATE_STOPPED: 'STATE_STOPPED',
              STATE_RUNNING: 'STATE_RUNNING' }

# Events returned from all of our eventoids
EVENT_GREEN      = const(0)  # green just became dominant
EVENT_GREEN_GONE = const(1)  # green stopped being dominant
EVENT_RED        = const(2)  # red just became dominant
EVENT_RED_GONE   = const(3)  # red stopped being dominant
EVENT_REASSESS   = const(4)

EVENT_STR = { EVENT_GREEN:      'EVENT_GREEN',
              EVENT_GREEN_GONE: 'EVENT_GREEN_GONE',
              EVENT_RED:        'EVENT_RED',
              EVENT_RED_GONE:   'EVENT_RED_GONE',
              EVENT_REASSESS:   'EVENT_REASSESS' }

DISTANCE_OUTER_MM         = const(300)  # mm to outer/warning zone
DISTANCE_INNER_MM         = const(150)  # mm to inner/danger  zone
DISTANCE_RANGE_CUTOFFS_MM = (100, 1000) # toss all ultrasonic values outside of this range
DISTANCE_HYSTERESIS_MM    = const(5)    # hysteresis band on each side of inner/outer distance values
DISTANCE_DEBUG_MM         = None        # movement threshold in mm to test ranging, or None to turn off

tcs = TCS34725(scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_uson2z = EventoidColor(
                    eventer,
                    ( (DISTANCE_OUTER_MM, (EVENT_ENTERING_OUTER,EVENT_EXITING_OUTER)),
                      (DISTANCE_INNER_MM, (EVENT_ENTERING_INNER,EVENT_EXITING_INNER)) ),
                    tcs,
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
