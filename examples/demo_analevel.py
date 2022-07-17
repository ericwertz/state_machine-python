# analevel_demo.py: Simple demo of analog level thresholding eventoid
#
# 70% of the full-scale ADC range arbitrarily chosen as the threshold value,
# with a hysteresis band of +/- 1%.  Events for both rising and falling through
# the hysteresis band are generated.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 20:28

from machine import Pin, ADC
from eventer import Eventer
from eventoid_analevel import EventoidAnalogLevel

TRACE_STATES = True

PIN_LED    = const( 0)
PIN_ANALOG = const(27)

ADC_COUNTS = const(2**16)                     # resolution of the ADC

# TODO set these to your liking
ADC_THRESHOLD       = int(ADC_COUNTS * 0.7)   # threshold is 70% of full-scale ADC range
HYSTERESIS_HALFBAND = ADC_COUNTS//100         # 2% hysteresis (full) band width around ADC_THRESHOLD

# States of the state machine
STATE_START = const(0)
STATE_LOW   = const(1)
STATE_HIGH  = const(2)
STATE_STR = { STATE_START: 'STATE_START',
              STATE_LOW:   'STATE_LOW',
              STATE_HIGH:  'STATE_HIGH' }

# Events returned from all of our eventoids
EVENT_LEVELCROSS_RISING  = const(0)
EVENT_LEVELCROSS_FALLING = const(1)
EVENT_STR = { EVENT_LEVELCROSS_RISING:  'EVENT_LEVELCROSS_RISING',
              EVENT_LEVELCROSS_FALLING: 'EVENT_LEVELCROSS_FALLING' }

led = Pin(PIN_LED, Pin.OUT)
adc = ADC(Pin(PIN_ANALOG))

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_level = EventoidAnalogLevel(eventer,
                               (EVENT_LEVELCROSS_RISING, EVENT_LEVELCROSS_FALLING),
                               adc,
                               ADC_THRESHOLD,
                               HYSTERESIS_HALFBAND)
                             
_ = eventer.register(eo_level)

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    if state == STATE_START:
            if   event == EVENT_LEVELCROSS_RISING:
                        led.on()
                        return STATE_HIGH
            elif event == EVENT_LEVELCROSS_FALLING:
                        led.off()
                        return STATE_LOW
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    if state == STATE_LOW:
            if   event == EVENT_LEVELCROSS_RISING:
                        led.on()
                        return STATE_HIGH
            elif event == EVENT_LEVELCROSS_FALLING:
                        eventer.err_unexpected_event(state, event, event_data)
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_HIGH:
            if   event == EVENT_LEVELCROSS_FALLING:
                        led.off()
                        return STATE_LOW
            elif event == EVENT_LEVELCROSS_RISING:
                        eventer.err_unexpected_event(state, event, event_data)
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

# figure out where we're starting from based on initial pot position
if adc.read_u16() < ADC_THRESHOLD:
    state = STATE_LOW
    led.off()
else:
    state = STATE_HIGH
    led.on()

eventer.loop(event_process, state)
