# demo_simple.py:
# This program is about the simplest state machine program that does anything useful,
#   intended to demonstrate just the core structore of how this system works.
# However, it is a fairly poor example of how to build up a more sophisticated
#   state machine program that's easier to enhance, debug and be efficient.
#   All of the other demo programs are better starting points for your own program(s)
#     because they use more sustainable, albeit more elaborate, practices.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 20:33

from machine import Pin

from eventer       import Eventer
from eventoid_gpio import EventoidGPIOPolled

led = Pin(16, Pin.OUT)

eventer = Eventer()
_ = eventer.register(EventoidGPIOPolled(eventer,
                                        ("EVENT_RELEASE","EVENT_PRESS"),
                                        Pin(20, Pin.IN)))

# (current state, current EVENT_*, approx ticks_ms() of the event, optional event data tag)
def event_process(state, event, event_msecs, event_data):
    if   state == "STATE_OFF":
                    if event == "EVENT_PRESS":
                                        led.on()
                                        return "STATE_ON"
    elif state == "STATE_ON":
                    if event == "EVENT_RELEASE":
                                        led.off()
                                        return "STATE_OFF"

led.off()
eventer.loop(event_process, "STATE_OFF")
