# demo_gpio2.py: This program is a demo for the gpio eventoid.
#
# It shows how to use the same event for multiple instances of event-generating devices,
#   differentiating them using the optional device-specific data returned with the event.
#
# Note: For simplicity this code blocks for a non-trivial amount of time when flashing the
#       LED, and this is generally (quite) poor practice.  However, this is only a demo and
#       flashing the LED is not the point of this program.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 16:19

from machine import Pin
import time
from eventer import Eventer
from eventoid_gpio import EventoidGPIOPolled

TRACE_STATES = True

BLINK_MSECS = const(200)

PIN_BUTTON1 = const(20)
PIN_BUTTON2 = const(21)
PIN_BUTTON3 = const(22)
PIN_LIGHT   = const(18)

# States of the state machine
STATE_START = const(0)
STATE_STR = { STATE_START: 'STATE_START' }

# Events returned from all of our eventoids
EVENT_PRESS = const(0)
EVENT_STR = { EVENT_PRESS: 'EVENT_PRESS' }

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_btn1 = EventoidGPIOPolled(eventer, (None,EVENT_PRESS), Pin(PIN_BUTTON1, Pin.IN), data=1)
eo_btn2 = EventoidGPIOPolled(eventer, (None,EVENT_PRESS), Pin(PIN_BUTTON2, Pin.IN), data=2)
eo_btn3 = EventoidGPIOPolled(eventer, (None,EVENT_PRESS), Pin(PIN_BUTTON3, Pin.IN), data=3)
_ = eventer.register(eo_btn1)
_ = eventer.register(eo_btn2)
_ = eventer.register(eo_btn3)

light = Pin(PIN_LIGHT, Pin.OUT)

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    if state == STATE_START:
            if event == EVENT_PRESS:
                for i in range(event_data):
                    light.on()
                    time.sleep_ms(BLINK_MSECS)
                    light.off()
                    time.sleep_ms(BLINK_MSECS)
                return STATE_START
            else:
                eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

light.off()

eventer.loop(event_process, STATE_START)
