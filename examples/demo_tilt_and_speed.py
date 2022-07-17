# demo_tilt_and_speed.py: simple hardware-light demo of tilt-and-speed eventoid
#
# This program fakes speed changes by using presses of a single button to denote changes of
# 10 "units" of speed.

# potentiometer to set the value from a periodic timer.
# The proof-of-concept eventoid alarms when the speed exceeds the angle (in degrees) from the horizontal
#   (e.g. going faster than 0 when horizontal and faster than 90 even when upright is bad).
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 27-Apr-2022 18:40

from machine import Pin, I2C, ADC
import lis3dh
from eventer import Eventer
from eventoid_tilt_and_speed import EventoidTiltAndSpeed

TRACE_STATES = True  # you can turn this off once your SM is debugged

# The following are only for testing or development.  Don't turn them on unless you
# really need them because they slow everything down
USE_POT_TO_SET_SPEED = False
PLOT_DATA            = True

PIN_LED   = const( 0)  # turn on LED in alarm/danger state
PIN_PULSE = const(20)  # FIXME: using the button, for demo/

PIN_SDA = const(8)
PIN_SCL = const(9)

alarm = Pin(PIN_LED, Pin.OUT)

I2C_CHANNEL    = const(0)
I2C_FREQ       = const(400000)
I2CADDR_LIS3DH = const(0x19)

STATE_SAFE      = const(0)
STATE_DANGEROUS = const(1)
STATE_STR = { STATE_SAFE:      'STATE_SAFE',
              STATE_DANGEROUS: 'STATE_DANGEROUS' }

EVENT_NOW_SAFE       = const(0)
EVENT_NOW_DANGEROUS  = const(1)
EVENT_STR = { EVENT_NOW_SAFE:       'EVENT_NOW_SAFE',
              EVENT_NOW_DANGEROUS:  'EVENT_NOW_DANGEROUS' }

def StateMachineErrorException(Exception):
    pass

i2c = I2C(I2C_CHANNEL, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
print("I2C address scan: ", end="")
for adr in i2c.scan():
    print(hex(adr), end=" ")
print()

accelerometer = lis3dh.LIS3DH_I2C(i2c, address=I2CADDR_LIS3DH)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_tiltspeed = EventoidTiltAndSpeed(eventer,
                                    (EVENT_NOW_SAFE, EVENT_NOW_DANGEROUS),
                                    accelerometer,
                                    Pin(PIN_PULSE, Pin.IN))
_ = eventer.register(eo_tiltspeed)

g_first_event = True  # this helps solve the first-event startup problem

def event_process(state, event, event_ms, event_data):
    if (event == EVENT_NOW_SAFE) or (event == EVENT_NOW_DANGEROUS):
        (ts_tilt, ts_speed) = event_data

    global g_first_event
    steady_state = not g_first_event
    g_first_event = False

    if   state == STATE_SAFE:
            if   event == EVENT_NOW_DANGEROUS:
                        alarm.on()
                        return STATE_DANGEROUS
            elif event == EVENT_NOW_SAFE:
                        if steady_state:
                            eventer.err_bad_event_in_state(state, event, event_data)
                        else:
                            return STATE_SAFE
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_DANGEROUS:
            if   event == EVENT_NOW_SAFE:
                        alarm.off()
                        return STATE_SAFE
            elif event == EVENT_NOW_DANGEROUS:
                        if steady_state:
                            eventer.err_bad_event_in_state(state, event, event_data)
                        else:
                            return STATE_DANGEROUS
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

# this chunk of crap is what lets you fake the speed setting in the eventoid with a pot
if USE_POT_TO_SET_SPEED:
    PIN_POT   = const(27)
    FAKE_SPEED_MIN = const(  0)
    FAKE_SPEED_MAX = const(100)
    ADC_MAX = (2**16)-1
    ADC_TO_SPEED = ((FAKE_SPEED_MAX-FAKE_SPEED_MIN)/ADC_MAX)
    pot = ADC(Pin(PIN_POT))

    def fake_speed_update(tmr):
        spd = ((ADC_MAX-pot.read_u16()) * ADC_TO_SPEED) + FAKE_SPEED_MIN
        eo_tiltspeed.set_speed(spd)

    timer = machine.Timer(period=50, mode=machine.Timer.PERIODIC, callback=fake_speed_update)

# This chunk of crap might allow you to plot the state and most recent tilt,speed
if PLOT_DATA:
    g_state = None
    def save_state(st):
        global g_state
        g_state = st
    eventer.set_loop_hook(save_state)

    def plot(tmr):
        print((g_state*10, eo_tiltspeed.tilt, eo_tiltspeed.speed))
    timer = machine.Timer(period=100, mode=machine.Timer.PERIODIC, callback=plot)

eventer.loop(event_process, STATE_SAFE)
