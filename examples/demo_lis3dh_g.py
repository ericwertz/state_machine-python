# demo_lis3dh_g.py: "somewhat" simple demo of 3-axis g-level thresholding eventoid
#
# Set an arbitrary g-value threshold for each axis and consider any value above that to
#   be an alarm condition on that axis.  Remain in STATE_CHILL only as long as no axes
#   are in an alarm condition.
# LEDs also display which axes are currently in an alarm condition.
# If you really want to see how important hysteresis is (virtually everywhere), set one
#   or more of the G_HALFWIDTHS to zero.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 26-Apr-2022 21:16

from machine import Pin, I2C
import lis3dh
from eventer import Eventer
from eventoid_lis3dh_g import EventoidLIS3DH_g

TRACE_STATES = True

PIN_LED_X = const(0)
PIN_LED_Y = const(1)
PIN_LED_Z = const(2)

PIN_SDA = const(8)
PIN_SCL = const(9)

led = (Pin(PIN_LED_X, Pin.OUT), Pin(PIN_LED_Y, Pin.OUT), Pin(PIN_LED_Z, Pin.OUT))

G_THRESHOLDS = (0.0, 0.0, 0.0)   # as you (smoothly) rotate the accel. this will vary from 9.8 to -9.8
G_HALFWIDTHS = (1.0, 1.0, 1.0)   # hysteresis half-band widths around G_THRESHOLD

I2C_CHANNEL    = const(0)
I2C_FREQ       = const(400000)
I2CADDR_LIS3DH = const(0x19)

INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

STATE_CHILL = const(0)
STATE_ALARM = const(1)
STATE_STR = { STATE_CHILL: 'STATE_CHILL',
              STATE_ALARM: 'STATE_ALARM' }

EVENT_RISING  = const(0)
EVENT_FALLING = const(1)
EVENT_STR = { EVENT_RISING:  'EVENT_RISING',
              EVENT_FALLING: 'EVENT_FALLING' }

def StateMachineErrorException(Exception):
    pass

i2c = I2C(I2C_CHANNEL, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
print("I2C address scan: ", end="")
for adr in i2c.scan():
    print(hex(adr), end=" ")
print()

accelerometer = lis3dh.LIS3DH_I2C(i2c, address=I2CADDR_LIS3DH)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_lis3dh = EventoidLIS3DH_g(eventer,
                             ((EVENT_RISING, EVENT_FALLING),  # x-axis threshold-crossing events
                              (EVENT_RISING, EVENT_FALLING),  # y
                              (EVENT_RISING, EVENT_FALLING)), # z
                             accelerometer)
_ = eventer.register(eo_lis3dh)    # ignore register() return value

def event_process(state, event, event_ms, event_data):
    global axis_alarming

    if (event == EVENT_RISING) or (event == EVENT_FALLING):
        eventing_axis = event_data[0]

    if   state == STATE_CHILL:
            if   event == EVENT_RISING:
                        led[eventing_axis].on()
                        axis_alarming[eventing_axis] = True
                        return STATE_ALARM

            elif event == EVENT_FALLING:
                        if (axis_alarming[eventing_axis] is None):
                            axis_alarming[eventing_axis] = False  # first event on that axis, and non-alarming
                        else:
                            eventer.err_bad_event_in_state(state, event, event_data)
                        return STATE_CHILL
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_ALARM:
            if   event == EVENT_FALLING:
                        led[eventing_axis].off()
                        axis_alarming[eventing_axis] = False
                        return STATE_ALARM if (True in axis_alarming) else STATE_CHILL
            elif event == EVENT_RISING:
                        led[eventing_axis].on()
                        axis_alarming[eventing_axis] = True
                        return STATE_ALARM
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

# Configure the thresholds and hysteresis bandwidths (you can change these on-the-fly if necessary)
eo_lis3dh.set_thresholds_g(G_THRESHOLDS)
eo_lis3dh.set_halfwidths_g(G_HALFWIDTHS)

# Keep track of the current alarm condition of each axis
axis_alarming = [None, None, None]

eventer.loop(event_process, STATE_CHILL)
