# tests_lis3dh.py: (mostly negative) tests for lis3dh eventoid
#
# Written by Eric Wertz (eric@edushields.com)
# Last modified 18-Sep-2022 14:44

from machine import Pin, I2C
import lis3dh
from eventer import Eventer
from eventoid_lis3dh import EventoidLIS3DH

EVENT_RISING  = const(0)
EVENT_FALLING = const(1)

PIN_SDA = const(8)
PIN_SCL = const(9)

I2C_CHANNEL    = const(0)
I2C_FREQ       = const(400000)
I2CADDR_LIS3DH = const(0x19)

INDEX_X = 0
INDEX_Y = 1
INDEX_Z = 2

i2c = I2C(I2C_CHANNEL, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=I2C_FREQ)
print("I2C address scan: ", end="")
for adr in i2c.scan():
    print(hex(adr), end=" ")
print()

acc = lis3dh.LIS3DH_I2C(i2c, address=I2CADDR_LIS3DH)

eventer = Eventer()

negative_tests = (
            None,
            (),
            [],
            (None),
            (None, None),
            ((EVENT_RISING, EVENT_FALLING)),
            ((EVENT_RISING, EVENT_FALLING),
             (EVENT_RISING, EVENT_FALLING)),
            ((None, None), None, None),
            ((EVENT_RISING,), None, None),
        )

# ensure that a few good calls work first
eo = EventoidLIS3DH(eventer, ((EVENT_RISING, None), None, None), acc)
_ = eventer.register(eo)
eo = EventoidLIS3DH(eventer, [(None,EVENT_FALLING), None, None], acc)
_ = eventer.register(eo)

n = 1
for test in negative_tests:
    print(f"Test #{n}: {test} ", end="")
    crashed = False
    try:
        eo = EventoidLIS3DH(eventer, test, acc)
        _ = eventer.register(eo)
        print("***FAILED***")
    except:
        crashed = True
        print("PASSED")
    n += 1
