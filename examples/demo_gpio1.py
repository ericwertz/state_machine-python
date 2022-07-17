# demo_gpio1.py: nearly simplest, cleanest demo of using the GPIO eventoid.
#
# This program merely sets up an event watchesr on one button GPIO pin and
#   toggles an LED on every press.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 16:52

from machine import Pin
from eventer import Eventer
from eventoid_gpio import EventoidGPIOPolled

TRACE_STATES = True

PIN_BUTTON = const(20)
PIN_LIGHT  = const(16)

# States of the state machine
STATE_OFF = const(0)
STATE_ON  = const(1)
STATE_STR = { STATE_OFF: 'STATE_OFF',
              STATE_ON:  'STATE_ON' }

# Events returned from all of our eventoids
EVENT_PRESS = const(0)
EVENT_STR = { EVENT_PRESS: 'EVENT_PRESS' }

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_btn = EventoidGPIOPolled(eventer,
                            (None, EVENT_PRESS),     # ignore rising edge, EVENT_PRESS upon falling edge
                            Pin(PIN_BUTTON, Pin.IN))
_ = eventer.register(eo_btn)

light = Pin(PIN_LIGHT, Pin.OUT)

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    if state == STATE_OFF:
            if event == EVENT_PRESS:
                light.on()
                return STATE_ON
            else:
                eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_ON:
            if event == EVENT_PRESS:
                light.off()
                return STATE_OFF
            else:
                eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

light.off()

eventer.loop(event_process, STATE_OFF)
