# demo_lis3dh_g.py: (somewhat) simple demo of 3-axis g-value thresholding eventoid
#
# Choosing a g-value threshold for each axis, consider any value above that to
#   be an alarm condition.
# Remain in STATE_ALARM only as long as at least one axis is in an alarm condition.
# LEDs display which axes are currently in the alarm condition.
#
# Design/implementation notes:
#   If you really want to see how important hysteresis (almost always) is, set one
#     or more of the G_HALFWIDTHS to zero.
#   Rather than defining six unique events for two each (rising, falling) of the three axes,
#     use only two for RISING and FALLING, and determine the axis number (INDEX_[XYZ])
#     returned in the data portion (axis#, g-value) of the event triple.  However, either
#     method would be fine, but this example demonstrates how use of an eventoid's returned
#     data can simplify certain applications.
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 18-Sep-2022 17:31

from machine import Pin, I2C
import lis3dh
from eventer import Eventer
from eventoid_lis3dh import EventoidLIS3DH

TRACE_STATES = True

# LED pins for X,Y,Z axis alarm indication, respectively
PINS_LED = (0, 1, 2)

PIN_SDA = const(8)
PIN_SCL = const(9)

G_THRESHOLDS = (0.0, 0.0, 0.0)  # eventing/alarming threshold g-values
G_HALFWIDTHS = (0.5, 0.5, 0.5)  # hysteresis half-band widths around G_THRESHOLDS

I2C_CHANNEL    = const(0)
I2C_FREQ       = const(400000)
I2CADDR_LIS3DH = const(0x19)

INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

# States of the state machine
STATE_IDLE = const(0)
STATE_ALARM = const(1)
STATE_STR = { STATE_IDLE:  'STATE_IDLE',
              STATE_ALARM: 'STATE_ALARM' }

# Events for our eventoids to send us
EVENT_RISING  = const(0)
EVENT_FALLING = const(1)
EVENT_STR = { EVENT_RISING:  'EVENT_RISING ',
              EVENT_FALLING: 'EVENT_FALLING' }

led = [Pin(pin, Pin.OUT) for pin in PINS_LED]

i2c = I2C(I2C_CHANNEL, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
print("I2C address scan: ", end="")
for adr in i2c.scan():
    print(hex(adr), end=" ")
print()

accelerometer = lis3dh.LIS3DH_I2C(i2c, address=I2CADDR_LIS3DH)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_lis3dh = EventoidLIS3DH(eventer,
                           ((EVENT_RISING, EVENT_FALLING),  # x-axis threshold-crossing events
                            (EVENT_RISING, EVENT_FALLING),  # y
                            (EVENT_RISING, EVENT_FALLING)), # z
                             accelerometer)
_ = eventer.register(eo_lis3dh)    # ignore register() return value

# Keep track of the current alarm condition of each axis
axis_alarming = [None, None, None]

def StateMachineErrorException(Exception):
    pass

def print_axisdata(acc):
    gs = acc.acceleration
    print(end=" (")
    for axis in range(3):
        print("%6.2f," % (gs[axis]/9.8), end="")
    print(end=")")
    
def event_process(state, event, event_ms, event_data):
    global axis_alarming

    if (event == EVENT_RISING) or (event == EVENT_FALLING):
        eventing_axis = event_data

    if   state == STATE_IDLE:
            if   event == EVENT_RISING:
                        led[eventing_axis].on()
                        axis_alarming[eventing_axis] = True
                        print_axisdata(accelerometer)
                        return STATE_ALARM

            elif event == EVENT_FALLING:
                        if ((axis_alarming[eventing_axis] is None) or axis_alarming[eventing_axis]):
                            axis_alarming[eventing_axis] = False
                        else:
                            eventer.err_bad_event_in_state(state, event, event_data)
                        return STATE_IDLE
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    elif state == STATE_ALARM:
            if   event == EVENT_FALLING:
                        led[eventing_axis].off()
                        axis_alarming[eventing_axis] = False
                        print_axisdata(accelerometer)
                        return STATE_ALARM if (True in axis_alarming) else STATE_IDLE
            elif event == EVENT_RISING:
                        led[eventing_axis].on()
                        axis_alarming[eventing_axis] = True
                        print_axisdata(accelerometer)
                        return STATE_ALARM
            else:
                        eventer.err_bad_event_in_state(state, event, event_data)
    else:
            eventer.err_bad_state(state)

eo_lis3dh.set_thresholds_g(G_THRESHOLDS)
eo_lis3dh.set_halfwidths_g(G_HALFWIDTHS)

eventer.loop(event_process, STATE_IDLE)
