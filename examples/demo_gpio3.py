# demo_gpio3.py: demo of interrupt-driven GPIO eventoid
#
# Demonstration of the flexibility of associating unique events on multiple
# GPIO eventoid instances, arbitrarily on rising and/or falling edges.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 17:00

from machine import Pin, PWM
from eventer import Eventer
from eventoid_gpio import EventoidGPIONonPolled

TRACE_STATES = True

PIN_BUTTON0 = const(20)
PIN_BUTTON1 = const(21)
PIN_BUTTON2 = const(22)
PIN_LIGHT   = const(16)

BRIGHTNESS_MIN   = const(    0)
BRIGHTNESS_MAX   = const(65535)
BRIGHTNESS_RESET = const(  512)

LIGHT_PWM_FREQ = const(1000)

# States of the state machine
STATE_START = const(0)
STATE_STR   = { STATE_START: 'STATE_START' }

# Events returned from all of our eventoids
EVENT_UP          = const(0)
EVENT_RESET_START = const(1)
EVENT_RESET_END   = const(2)
EVENT_DOWN        = const(3)
EVENT_STR   = { EVENT_UP:          'EVENT_UP',
                EVENT_RESET_START: 'EVENT_RESET_START',
                EVENT_RESET_END:   'EVENT_RESET_END',
                EVENT_DOWN:        'EVENT_DOWN' }

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

#                                               (rising,falling) edge event(s)         the GPIO Pin
eo_btn_up    = EventoidGPIONonPolled(eventer, (None,EVENT_UP),                     Pin(PIN_BUTTON0, Pin.IN))
eo_btn_reset = EventoidGPIONonPolled(eventer, (EVENT_RESET_END,EVENT_RESET_START), Pin(PIN_BUTTON1, Pin.IN))
eo_btn_down  = EventoidGPIONonPolled(eventer, (EVENT_DOWN,None),                   Pin(PIN_BUTTON2, Pin.IN))
_ = eventer.register(eo_btn_up)
_ = eventer.register(eo_btn_reset)
_ = eventer.register(eo_btn_down)

light_pwm = PWM(Pin(PIN_LIGHT, Pin.OUT))

brightness = BRIGHTNESS_RESET

def bright_up(n):   return min(n*2, BRIGHTNESS_MAX)
def bright_down(n): return n//2
    
# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    global brightness

    if state == STATE_START:
            if   event == EVENT_UP:
                            brightness = bright_up(brightness)
            elif event == EVENT_DOWN:
                            brightness = bright_down(brightness)
            elif event == EVENT_RESET_START:
                            brightness = BRIGHTNESS_MIN
            elif event == EVENT_RESET_END:
                            brightness = BRIGHTNESS_RESET
            else:
                eventer.err_bad_event_in_state(state, event, event_data)
            
            light_pwm.duty_u16(brightness)
            print(f" <brightness={brightness}>", end="")
            return STATE_START
    else:
            eventer.err_bad_state(state)

light_pwm.duty_u16(brightness)
light_pwm.freq(LIGHT_PWM_FREQ)

eventer.loop(event_process, STATE_START)
