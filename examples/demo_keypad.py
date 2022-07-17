# demo_Keypad.py: demo using a stae-machine based program with an M-by-N matrix keypad
#
# Written by Eric B. Wertz (eric@edushields.com)
# Last modified 24-Apr-2022 20:32

from machine  import Pin
from eventer  import Eventer
from eventoid_keypad import EventoidKeypadPolled

TRACE_STATES = False    # True if you want to hear the state machine running

REPORT_PRESSES  = True  # choose whether you want presses and/or releases
REPORT_RELEASES = True

# States of the state machine
STATE_START = const(0)                      # one, boring state just for demo
STATE_STR = { STATE_START: 'STATE_START' }

# Events that we're going to tell our eventoids to send us
EVENT_KEYPAD_PRESS   = const(0)
EVENT_KEYPAD_RELEASE = const(1)
EVENT_STR = { EVENT_KEYPAD_PRESS:   'EVENT_KEYPAD_PRESS',
              EVENT_KEYPAD_RELEASE: 'EVENT_KEYPAD_RELEASE' }

# GPnn pin numbers connected to (in this case 4x4) keypad rows/cols
PINS_ROWS = (7,6,5,4)
PINS_COLS = (3,2,1,0)

KEYS = (("1","2","3","A"),
        ("4","5","6","B"),
        ("7","8","9","C"), 
        ("*","0","#","D"))

EVENTOID_KEYPAD = const(0)

eventer = Eventer(trace=TRACE_STATES, trace_info=(STATE_STR,EVENT_STR))

eo_kp = EventoidKeypadPolled(eventer,
                             (EVENT_KEYPAD_PRESS   if REPORT_PRESSES  else None,
                              EVENT_KEYPAD_RELEASE if REPORT_RELEASES else None),
                             PINS_ROWS,
                             PINS_COLS)
_ = eventer.register(eo_kp)

# Take the current state and the next event, perform the appropriate action(s) and
#   return the next state.  The cross-product of all states and events should
#   be completely covered, and unanticipated combinations should result in a
#   warning/error, as that often indicates a consequential bug in your state machine.
def event_process(state, event, event_ms, event_data):
    if state == STATE_START:
        if event == EVENT_KEYPAD_PRESS:
            row, col = event_data
            print("<press "+KEYS[row][col]+">")
            return STATE_START
        elif event == EVENT_KEYPAD_RELEASE:
            row, col = event_data
            print("<release "+KEYS[row][col]+">")
            return STATE_START
        else:
            eventer.err_bad_event_in_state(state, event, event_data)
    else:
        eventer.err_bad_state(state)

eventer.loop(event_process, STATE_START)
